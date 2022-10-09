from dataclasses import dataclass
from collections import defaultdict
from typing import List

import csv

import config

@dataclass
class Participant:
    name: str
    face_bbox: List

@dataclass
class Team:
    name: str
    participants: List[Participant]

def parse_teams_from_csv(csv_path) -> List[Team]:
    team_participants = defaultdict(list)
    with open(csv_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=config.delimeter)
        for row in reader:
            team_participants[row['team']].append(Participant(row['name'], None))

    return [Team(team_name, participants)
            for team_name, participants in team_participants.items()
            if team_name != '']