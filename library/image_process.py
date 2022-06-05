from typing import List

import os
import json
import cv2
import face_recognition
from PIL import Image
import numpy as np
from iptcinfo3 import IPTCInfo

from library.team import Team, Participant
import config


def find_photos_by_tag(images_directory, group_photo_tag=None):
    result = []
    for path in os.listdir(images_directory):
        if path.endswith(".png") or path.endswith(".jpg") or path.endswith(".jpeg"):
            file = os.path.join(images_directory, path)
            if group_photo_tag == None or group_photo_tag in IPTCInfo(file)['keywords']:
                result.append(file)
    return result

class GroupImageProcess:
    path: str
    face_locations: List
    ocr: List
    team: Team

    def __init__(self, image_path):
        self.path = image_path

        image = face_recognition.load_image_file(self.path)
        self.face_locations = face_recognition.face_locations(image)

        self.ocr = self.__advanced_ocr()

        self.team = None

    def __advanced_ocr(self):
        im = Image.open(self.path)
        width, height = im.size

        ocr = []

        for face_location in self.face_locations:
            (face_top, face_right, face_bottom, face_left) = face_location
            face_width = face_right - face_left

            body_left = max(0, face_left -
                            config.body_to_face_ratio / 2 * face_width)
            body_right = min(width, face_right +
                             config.body_to_face_ratio / 2 * face_width)
            body_top = face_bottom
            body_bottom = height

            cropped = im.crop((body_left, body_top, body_right, body_bottom))
            crop_ocr = config.readtext(np.array(cropped))

            ocr += [(body_left + (quadrangle[0][0] + quadrangle[1][0]) / 2, text)
                    for (quadrangle, text) in crop_ocr]

        return ocr

    def save(self, output_directory):
        os.makedirs(output_directory, exist_ok=True)
        if self.team is None:
            return
        team = self.team
        image = cv2.imread(self.path)
        cv2.putText(image, team.name, (100, 150),
                    cv2.FONT_HERSHEY_SIMPLEX, 5, (0, 0, 255), 5)
        for participant in team.participants:
            if participant.face_bbox is None:
                continue
            (top, right, bottom, left) = participant.face_bbox
            cv2.rectangle(image, (left, top),
                          (right, bottom), (255, 255, 255), 5)
            cv2.putText(image, participant.name, (left, top - 20),
                        cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 255), 4)
        cv2.imwrite(os.path.join(output_directory,
                    os.path.basename(self.path)), image)
        with open(os.path.join(output_directory, os.path.basename(self.path) + ".json"), 'w') as f:
            data = {
                'team': team.name,
                'people': [x.name for x in team.participants],
                'bbox': [x.face_bbox for x in team.participants]
            }
            json.dump(data, f)
