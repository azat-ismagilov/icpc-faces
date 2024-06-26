from dataclasses import dataclass
from collections import defaultdict
from typing import List

import csv

from rectangle import Box


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
    id: str

    def __iter__(self):
        return iter((self.name, self.participants))


def parse_teams_from_csv(csv_path, delimiter) -> List[Team]:
    team_participants = defaultdict(list)
    team_name = defaultdict(str)
    with open(csv_path, "r", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file, delimiter=delimiter)
        for row in reader:
            if row["role"] == "Contestant" or row["role"] == "Coach":
                team_name[row["id"]] = row["name"]
                team_participants[row["id"]].append(Participant(row["name"], None))

    return [
        Team(team_name[id], participants, id)
        for id, participants in team_participants.items()
        if id != ""
    ]
