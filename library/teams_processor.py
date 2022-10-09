import os
from typing import List

import networkx as nx
from thefuzz import fuzz, process
from tqdm import tqdm

import library.params as params
from library.rectangle import Box
from library.image_process import GroupImageProcess
from library.team import Team, parse_teams_from_csv


def __square_distance_between_centers(a: Box, b: Box):
    return pow((a.left + a.right) - (b.left + b.right), 2)


def __max_weight_matching_multi_graph(edges_list):
    G = nx.Graph()
    min_right_index = max([edge[0] for edge in edges_list]) + 1
    for u, v, _, _ in edges_list:
        if not G.has_edge(u, v + min_right_index):
            other_edges = [
                edge for edge in edges_list if edge[0] == u and edge[1] == v]
            max_edge = max(other_edges, key=lambda edge: edge[2])
            G.add_edge(max_edge[0], max_edge[1] + min_right_index,
                       weight=max_edge[2], result=max_edge[3])

    matching = nx.max_weight_matching(G)
    edges_in_matching = []
    for u, v in matching:
        if u >= min_right_index:
            u, v = v, u
        edges_in_matching.append(
            (u, v - min_right_index, G[u][v]['weight'], G[u][v]['result']))
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
                edges_list.append((index_team, index_image, score, result))

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
                if index_face == -1 or min_distance < distance:
                    min_distance = distance
                    index_face = index
                    
            edges_list.append((index_participant, index_face, score, result))

    if len(edges_list) == 0:
        return

    matching = __max_weight_matching_multi_graph(edges_list)
    for (index_participant, index_face, weight, result) in matching:
        participants[index_participant].face_bbox = image.face_locations[index_face]


def process_teams(csv_path, output_directory, tags_file, images: List[GroupImageProcess]):
    teams = parse_teams_from_csv(csv_path)
    __match_team_images(images, teams)
    for image in tqdm(images, desc="Matching participants"):
        __match_participants(image)

    open(tags_file, 'w').close()
    for image in tqdm(images, desc="Save files"):
        image.save(output_directory, tags_file)
