import os
from typing import List

import networkx as nx
from thefuzz import fuzz, process

import config
from library.image_process import GroupImageProcess
from library.team import Team, parse_teams_from_csv


def __square_distance_between_centers(l_1, r_1, l_2, r_2):
    return pow((l_1 + r_1) - (l_2 + r_2), 2)


def __max_weight_matching_multi_graph(M):
    G = nx.Graph()
    for u, v, _ in M.edges(data=True):
        if not G.has_edge(u, v):
            weight = max(d.get('weight', 1)
                         for d in M.get_edge_data(u, v).values())
            G.add_edge(u, v, weight=weight)
    return nx.max_weight_matching(G)


def __match_team_images(images: List[GroupImageProcess], teams: List[Team]):
    ocr_candidates = [(text, i)
                      for i in range(len(images))
                      for (_, text) in images[i].ocr]

    M = nx.MultiGraph()
    M.add_nodes_from(range(len(teams) + len(images)))
    for (index_team, team) in enumerate(teams):
        for text in [team.name] + [participant.name for participant in team.participants]:
            result = process.extract(
                (text,), ocr_candidates, lambda x: x[0], scorer=fuzz.token_sort_ratio)
            for ((_, index_image), score) in result:
                if score < config.min_team_matching_score:
                    continue
                M.add_edge(index_team, len(teams) + index_image, weight=score)

    matching = __max_weight_matching_multi_graph(M)
    for (index_image, index_team) in matching:
        if index_team >= len(teams):
            index_image, index_team = index_team, index_image
        index_image -= len(teams)

        images[index_image].team = teams[index_team]
        __match_participants(images[index_image])


def __match_participants(image: GroupImageProcess):
    if image.team is None:
        return
    participants = image.team.participants

    print("--------")
    print("Team: ", image.team.name, image.team.participants)
    print(image.ocr)
    print(image.face_locations)
    print("--------")

    M = nx.MultiGraph()
    M.add_nodes_from(range(len(participants) + len(image.face_locations)))
    for (index_participant, participant) in enumerate(participants):
        result = process.extract(
            (None, participant.name), image.ocr, lambda x: x[1], scorer=fuzz.token_sort_ratio)
        for ((center, _), score) in result:
            if score < config.min_participant_matching_score:
                continue
            (index_face, bbox) = min(enumerate(image.face_locations),
                                     key=lambda x: __square_distance_between_centers(x[1][1], x[1][3],
                                                                                     center, center))
            M.add_edge(index_face, index_participant +
                       len(image.face_locations), weight=score)

    matching = __max_weight_matching_multi_graph(M)
    for (index_participant, index_face) in matching:
        if index_face >= len(image.face_locations):
            index_participant, index_face = index_face, index_participant
        index_participant -= len(image.face_locations)

        bbox = image.face_locations[index_face]
        participants[index_participant].face_bbox = bbox


def process_teams(csv_path, output_directory, images: List[GroupImageProcess]):
    teams = parse_teams_from_csv(csv_path)
    __match_team_images(images, teams)
    os.makedirs(output_directory, exist_ok=True)
    for image in images:
        image.save(output_directory)
