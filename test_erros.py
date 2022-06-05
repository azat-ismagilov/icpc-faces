import json
import logging
import os

from Levenshtein import distance
from iptcinfo3 import IPTCInfo

import config

iptcinfo_logger = logging.getLogger('iptcinfo')
iptcinfo_logger.setLevel(logging.ERROR)

wrong_teams = []
wrong_faces = []
total_teams = 0
total_faces = 0

for path in os.listdir(config.group_images_directory):
    if path.endswith(".png") or path.endswith(".jpg") or path.endswith(".jpeg"):
        file = os.path.join(config.group_images_directory, path)
        keywords = [keyword.decode("ISO-8859-1") for keyword in IPTCInfo(file)['keywords']]
        if 'event$Team Photos' not in keywords:
            continue

        teamPrefixes = ['team$', 'tema$', 'TEAM$ ']
        realTeamName = None
        realParticipants = []
        for keyword in keywords:
            for prefix in teamPrefixes:
                if keyword.startswith(prefix):
                    realTeamName = keyword[len(prefix):]
            if '(' in keyword:
                realParticipants.append(keyword.split('(')[0])
        total_teams += 1

        myjson = os.path.join(config.group_output_directory, path + '.json')
        try:
            with open(myjson, 'r') as f:
                data = json.load(f)
        except:
            print("Unable to find team {} from file: {}".format(realTeamName, path))
            wrong_teams.append(realTeamName)
            #wrong_faces.extend(realParticipants)
            continue

        if distance(realTeamName, data['team']) > 8:
            print("Wrong team name {}, correct should be {}. File: {}".format(data['team'], realTeamName, path))
            wrong_teams.append(realTeamName)

        total_faces += len(realParticipants)
        actual = [data['people'][i] for i in range(len(data['people'])) if data['bbox'][i] is not None]
        if len(actual) == 0:
            continue
        for participant in realParticipants:
            inside = False
            if min([distance(participant, chel) for chel in actual]) <= 4:
                continue
            #print(participant, "----", actual)
            wrong_faces.append(participant)

print("WRONG_TEAMS: {}/{}".format(len(wrong_teams), total_teams))
print("WRONG_CHELS: {}/{}".format(len(wrong_faces), total_faces))
