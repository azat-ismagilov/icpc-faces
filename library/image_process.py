from typing import List

import os
import json
import cv2
import face_recognition
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from iptcinfo3 import IPTCInfo

import library.params as params
from library.team import Team, Participant


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
    width: int
    height: int

    def __init__(self, image_path):
        self.path = image_path

        image = face_recognition.load_image_file(self.path)
        self.face_locations = face_recognition.face_locations(image)

        self.width, self.height = Image.open(self.path).size

        self.ocr = self.__advanced_ocr()

        self.team = None

    def __get_white_rectangles(self, im):
        width, height = im.size

        image_array = np.array(im)
        img = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        ret, thresh = cv2.threshold(img_grey, 180, 255, cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(
            thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

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
                            params.body_to_face_ratio * face_width)
            body_right = min(width, face_right +
                             params.body_to_face_ratio * face_width)
            body_top = face_bottom
            body_bottom = height

            for top, right, bottom, left in white_rectangles:
                if body_top <= top and bottom <= body_bottom and body_left <= left and right <= body_right:
                    cropped = im.crop((left, top, right, bottom))

                    crop_ocr = params.readtext(np.array(cropped))

                    ocr += [((left + min_gx, left + max_gx, top + min_gy, top + max_gy), text)
                            for (([min_gx, min_gy], _, [max_gx, max_gy], _), text) in crop_ocr]

        return ocr

    def __convert_bbox(self, bbox):
        top, right, bottom, left = bbox
        top = "%0.4x" % int(top / self.height * 65535)
        bottom = "%0.4x" % int(bottom / self.height * 65535)
        left = "%0.4x" % int(left / self.width * 65535)
        right = "%0.4x" % int(right / self.width * 65535)
        return left + top + right + bottom

    def save(self, output_directory, tags_file):
        os.makedirs(output_directory, exist_ok=True)
        if self.team is None:
            return
        team = self.team
        image = Image.open(self.path)
        if image is None or image.size == 0:
            return
        draw = ImageDraw.Draw(image)
        giant = ImageFont.truetype('arial.ttf', 200)
        normal = ImageFont.truetype('arial.ttf', 50)
        small = ImageFont.truetype('arial.ttf', 16)

        tags = []

        draw.text((100, 150), team.name, fill='green', font=giant)
        tags.append("team${}".format(team.name))

        for participant in team.participants:
            if participant.face_bbox is None:
                continue
            (top, right, bottom, left) = participant.face_bbox
            draw.rectangle((left, top, right, bottom),
                           outline="green", width=5)
            draw.text((left, top - 100), participant.name,
                      fill='green', font=normal)

            tags.append("{}({})".format(participant.name,
                                        self.__convert_bbox(participant.face_bbox)))

        rest_bbox = [face_bbox for face_bbox in self.face_locations if face_bbox not in [
            x.face_bbox for x in team.participants]]
        for face_bbox in rest_bbox:
            top, right, bottom, left = face_bbox
            draw.rectangle((left, top, right, bottom), outline="red")
            tags.append("({})".format(self.__convert_bbox(face_bbox)))

        for (quadrangle, text) in self.ocr:
            left, right, top, bottom = quadrangle
            draw.rectangle((left, top, right, bottom), outline="red")
            draw.text((left, top - 5), text, fill='red', font=small)

        image.save(os.path.join(output_directory, os.path.basename(self.path)))
        with open(tags_file, 'a', encoding='utf-8') as f:
            line = '"{}"\t'.format(self.path) + ','.join(['"{}"'.format(tag) for tag in tags])
            f.write(line)