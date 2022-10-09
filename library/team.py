from dataclasses import dataclass
from collections import defaultdict
from typing import List

import csv

import config
from library.rectangle import Box

@dataclass
class Participant:
    name: str
    face_bbox: Box

    def __iter__(self):
        return iter((self.name, self.face_bbox))

@dataclass
class Team:
    name: str
    participants: List[Participant]

    def __iter__(self):
        return iter((self.name, self.participants))

def parse_teams_from_csv(csv_path) -> List[Team]:
    team_participants = defaultdict(list)
    with open(csv_path, 'r', encoding='utf-8-sig') as csv_file:
        reader = csv.DictReader(csv_file, delimiter=config.delimeter)
        for row in reader:
            team_participants[row['team']].append(Participant(row['name'], None))
            

    return [Team(team_name, participants)
            for team_name, participants in team_participants.items()
            if team_name != '']
