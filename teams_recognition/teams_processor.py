from dataclasses import dataclass
from typing import Any, List

import networkx as nx
from thefuzz import fuzz, process
from tqdm import tqdm

import csv
import params as params
from rectangle import Box
from image_process import GroupImageProcess
from team import Team, parse_teams_from_csv


@dataclass
class WeightedBipartiteEdge:
    left: int
    right: int
    weight: int
    result: Any

    def __iter__(self):
        return iter((self.left, self.right, self.weight, self.result))


def __square_distance_between_centers(a: Box, b: Box) -> float:
    return pow((a.left + a.right) - (b.left + b.right), 2)


def __max_weight_matching_multi_graph(edges_list: List[WeightedBipartiteEdge]) -> List[WeightedBipartiteEdge]:
    G = nx.Graph()
    min_right_index = max([edge.left for edge in edges_list]) + 1
    for left, right, _, _ in edges_list:
        if not G.has_edge(left, right + min_right_index):
            other_edges = [
                edge for edge in edges_list if edge.left == left and edge.right == right]
            heavy_edge = max(other_edges, key=lambda edge: edge.weight)
            G.add_edge(heavy_edge.left, heavy_edge.right + min_right_index,
                       weight=heavy_edge.weight, result=heavy_edge.result)

    matching = nx.max_weight_matching(G)
    edges_in_matching = []
    for u, v in matching:
        if u >= min_right_index:
            u, v = v, u
        edges_in_matching.append(
            WeightedBipartiteEdge(u, v - min_right_index, G[u][v]['weight'], G[u][v]['result']))
    return edges_in_matching


def __custom_substring_scorer(query, check):
    match = fuzz.token_sort_ratio
    if len(check) > len(query) * 1.5:
        return max([match(query, check[pos:pos + len(query)])
                    for pos in range(len(check) - len(query))])
    else:
        return match(query, check)


def __match_team_images(images: List[GroupImageProcess], teams: List[Team]):
    ocr_candidates = [(text, i)
                      for i in range(len(images))
                      for (_, text) in images[i].ocr]

    edges_list = []
    for (index_team, team) in enumerate(teams):
        for text in [team.name] + [participant.name for participant in team.participants]:
            result = process.extract(
                (text,), ocr_candidates, lambda x: x[0], scorer=__custom_substring_scorer)
            for ((_, index_image), score) in result:
                if score < params.min_team_matching_score:
                    continue
                edges_list.append(WeightedBipartiteEdge(index_team, index_image, score, result))

    matching = __max_weight_matching_multi_graph(edges_list)
    for (index_team, index_image, weight, result) in matching:
        images[index_image].team = teams[index_team]


def __match_participants(image: GroupImageProcess):
    if image.team is None:
        return
    participants = image.team.participants

    edges_list = []
    for (index_participant, participant) in enumerate(participants):
        result = process.extract(
            (None, participant.name), image.ocr, lambda x: x[1], scorer=__custom_substring_scorer)
        for ((text_bbox, _), score) in result:
            if score < params.min_participant_matching_score:
                continue

            index_face = -1
            min_distance = None
            for index, face in enumerate(image.face_locations):
                if text_bbox.bottom < face.top:
                    continue
                distance = __square_distance_between_centers(face, text_bbox)
                if index_face == -1 or min_distance > distance:
                    min_distance = distance
                    index_face = index

            edges_list.append(WeightedBipartiteEdge(index_participant, index_face, score, result))

    if len(edges_list) == 0:
        return

    matching = __max_weight_matching_multi_graph(edges_list)
    for (index_participant, index_face, weight, result) in matching:
        participants[index_participant].face_bbox = image.face_locations[index_face]


def process_teams(csv_path, delimiter, output_directory, tags_file, images: List[GroupImageProcess]):
    teams = parse_teams_from_csv(csv_path, delimiter)
    with tqdm(desc="Matching teams", total=1) as pbar:
        __match_team_images(images, teams)
        pbar.update(1)

    for image in tqdm(images, desc="Matching participants"):
        __match_participants(image)

    with open(tags_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_ALL)
        for image in tqdm(images, desc="Saving files"):
            image.save(output_directory, writer)
