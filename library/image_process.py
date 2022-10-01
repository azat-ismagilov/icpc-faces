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

    def __get_white_rectangles(self, im):
        width, height = im.size

        image_array = np.array(im)
        img = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


        ret, thresh = cv2.threshold(img_grey,180,255,cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        white_rectangles = []
        for cnt in contours:
            if cv2.contourArea(cnt) < width * height / 5 and cv2.contourArea(cnt) > width * height / 10000:
                x, y, w, h = cv2.boundingRect(cnt)
                left, right, top, bottom = x, x + w, y, y + h
                white_rectangles.append((top, right, bottom, left))

        return white_rectangles

    def __advanced_ocr(self):
        im = Image.open(self.path)
        width, height = im.size

        white_rectangles = self.__get_white_rectangles(im)

        ocr = []

        for face_location in self.face_locations:
            (face_top, face_right, face_bottom, face_left) = face_location
            face_width = face_right - face_left

            body_left = max(0, face_left -
                             config.body_to_face_ratio * face_width)
            body_right = min(width, face_right +
                             config.body_to_face_ratio * face_width)
            body_top = face_bottom
            body_bottom = height

            for top, right, bottom, left in white_rectangles:
                if body_top <= top and bottom <= body_bottom and body_left <= left and right <= body_right:
                    cropped = im.crop((left, top, right, bottom))

                    crop_ocr = config.readtext(np.array(cropped))

                    ocr += [((left + min_gx, left + max_gx, top + min_gy, top + max_gy), text)
                            for (([min_gx, min_gy], _, [max_gx, max_gy], _), text) in crop_ocr]

        return ocr

    def save(self, output_directory):
        os.makedirs(output_directory, exist_ok=True)
        if self.team is None:
            return
        team = self.team
        image = cv2.imread(self.path)
        if image is None or image.size == 0:
            return
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
        rest_bbox = [face_bbox for face_bbox in self.face_locations if face_bbox not in [x.face_bbox for x in team.participants]]
        for face_bbox in rest_bbox:
            top, right, bottom, left = face_bbox
            cv2.rectangle(image, (left, top), 
                          (right, bottom), (255, 0, 255), 5)
        for (quadrangle, text) in self.ocr:
            left, right, top, bottom = quadrangle
            cv2.rectangle(image, (left, top),
                          (right, bottom), (0, 255, 255), 1)
            cv2.putText(image, text, (left, top - 5),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (0, 0, 255))
        cv2.imwrite(os.path.join(output_directory, os.path.basename(self.path)), image)
        with open(os.path.join(output_directory, os.path.basename(self.path) + ".json"), 'w') as f:
            data = {
                'team': team.name,
                'people': [x.name for x in team.participants],
                'bbox': [x.face_bbox for x in team.participants],
                'remaining_bbox': rest_bbox
            }
            json.dump(data, f)
