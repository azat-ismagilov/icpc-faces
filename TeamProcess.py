import csv
import json
import os
from collections import defaultdict
from dataclasses import dataclass

import cv2
import networkx as nx
from thefuzz import fuzz
from thefuzz import process

import config
from ImageProcess import ImageProcess


@dataclass
class ParticipantInfo:
    name: str
    face_bbox: ((int, int), (int, int)) = None


@dataclass
class TeamInfo:
    name: str
    participants: [ParticipantInfo]
    image_process: ImageProcess = None


def square_distance_between_centers(l_1, r_1, l_2, r_2):
    return pow((l_1 + r_1) - (l_2 + r_2), 2)


def max_weight_matching_multi_graph(M):
    G = nx.Graph()
    for u, v, data in M.edges(data=True):
        if not G.has_edge(u, v):
            weight = max(d.get('weight', 1) for d in M.get_edge_data(u, v).values())
            G.add_edge(u, v, weight=weight)
    return nx.max_weight_matching(G)


def recognize_participants(image: ImageProcess, participants: [ParticipantInfo]):
    M = nx.MultiGraph()
    M.add_nodes_from(range(len(participants) + len(image.face_locations)))
    for (index_participant, participant) in enumerate(participants):
        result = process.extract((None, participant.name), image.ocr, lambda x: x[1], scorer=fuzz.token_sort_ratio)
        for ((quadrangle, text), score) in result:
            if score < config.min_participant_matching_score:
                continue
            (index_face, bbox) = min(enumerate(image.face_locations),
                                     key=lambda x: square_distance_between_centers(x[1][1], x[1][3],
                                                                                   quadrangle[0][0], quadrangle[1][0]))
            M.add_edge(index_face, index_participant + len(image.face_locations), weight=score)

    matching = max_weight_matching_multi_graph(M)
    for (index_participant, index_face) in matching:
        if index_face >= len(image.face_locations):
            index_participant, index_face = index_face, index_participant
        index_participant -= len(image.face_locations)

        bbox = image.face_locations[index_face]
        participants[index_participant].face_bbox = bbox


class TeamsProcessor:
    teams: [TeamInfo] = []

    def __init__(self, csv_path):
        team_participants: [TeamInfo] = defaultdict(list)
        with open(csv_path, 'r') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                team_participants[row['instName']].append(ParticipantInfo(row['Name']))
        self.teams = [TeamInfo(team_name, participants)
                      for team_name, participants in team_participants.items()
                      if team_name != '']

    def match_team_images(self, images: [ImageProcess]):
        ocr_candidates = [(text, i) for i in range(len(images)) for (bbox, text) in images[i].ocr]

        M = nx.MultiGraph()
        M.add_nodes_from(range(len(self.teams) + len(images)))
        for (index_team, team) in enumerate(self.teams):
            for text in [team.name] + [participant.name for participant in team.participants]:
                result = process.extract((text,), ocr_candidates, lambda x: x[0], scorer=fuzz.token_sort_ratio)
                for ((best, index_image), score) in result:
                    if score < config.min_team_matching_score:
                        continue
                    M.add_edge(index_team, len(self.teams) + index_image, weight=score)

        matching = max_weight_matching_multi_graph(M)
        for (index_image, index_team) in matching:
            if index_team >= len(self.teams):
                index_image, index_team = index_team, index_image
            index_image -= len(self.teams)

            self.teams[index_team].image_process = images[index_image]
            recognize_participants(self.teams[index_team].image_process, self.teams[index_team].participants)

    def save_new_photos(self, output_directory):
        os.makedirs(config.output_directory, exist_ok=True)
        for team in self.teams:
            if team.image_process is None:
                continue
            image = cv2.imread(team.image_process.path)
            cv2.putText(image, team.name, (100, 150), cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 5)
            for participant in team.participants:
                if participant.face_bbox is None:
                    continue
                (top, right, bottom, left) = participant.face_bbox
                cv2.rectangle(image, (left, top), (right, bottom), (255, 255, 255), 5)
                cv2.putText(image, participant.name, (left, top - 20), cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 255), 4)
            cv2.imwrite(os.path.join(output_directory, os.path.basename(team.image_process.path)), image)
            with open(os.path.join(output_directory, os.path.basename(team.image_process.path) + ".json"), 'w') as f:
                data = {
                    'team': team.name,
                    'people': [x.name for x in team.participants],
                    'bbox': [x.face_bbox for x in team.participants]
                }
                json.dump(data, f)
