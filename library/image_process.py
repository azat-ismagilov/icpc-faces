from typing import List, Tuple

import os
import face_recognition
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from iptcinfo3 import IPTCInfo

import library.params as params
from library.rectangle import *
from library.team import Team


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
    face_locations: List[Box]
    ocr: List[Tuple[Box, str]]
    team: Team
    width: int
    height: int

    def __init__(self, image_path):
        self.path = image_path

        image = face_recognition.load_image_file(self.path)
        self.face_locations = [boxFromFaceLocation(location)
                               for location in face_recognition.face_locations(image)]

        self.width, self.height = Image.open(self.path).size

        self.ocr = self.__advanced_ocr()

        self.team = None

    def __advanced_ocr(self):
        im = Image.open(self.path)

        ocr = []

        for bbox in self.face_locations:
            face_width = bbox.right - bbox.left

            body_left = max(0, bbox.left -
                            params.body_to_face_ratio * face_width)
            body_right = min(self.width, bbox.right +
                             params.body_to_face_ratio * face_width)
            body_top = bbox.bottom
            body_bottom = self.height

            cropped = im.crop((body_left, body_top, body_right, body_bottom))

            crop_ocr = params.readtext(np.array(cropped))

            ocr += [(Box(body_left + min_gx, body_top + min_gy, body_left + max_gx, body_top + max_gy), text)
                    for (([min_gx, min_gy], _, [max_gx, max_gy], _), text) in crop_ocr]

        return ocr

    def __convert_bbox(self, bbox: Box):
        top = "%0.4x" % int(bbox.top / self.height * 65535)
        bottom = "%0.4x" % int(bbox.bottom / self.height * 65535)
        left = "%0.4x" % int(bbox.left / self.width * 65535)
        right = "%0.4x" % int(bbox.right / self.width * 65535)
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

        # TODO: Rewrite
        for (name, face_bbox) in team.participants:
            if face_bbox is None:
                continue
            draw.rectangle(face_bbox.toPIL(), outline="green", width=5)
            draw.text((face_bbox.left, face_bbox.top - 100),
                      name, fill='green', font=normal)

            tags.append("{}({})".format(name, self.__convert_bbox(face_bbox)))

        rest_bbox = [face_bbox for face_bbox in self.face_locations if face_bbox not in [
            x.face_bbox for x in team.participants]]

        for face_bbox in rest_bbox:
            draw.rectangle(face_bbox.toPIL(), outline="red")
            tags.append("({})".format(self.__convert_bbox(face_bbox)))

        for (bbox, text) in self.ocr:
            draw.rectangle(bbox.toPIL(), outline="red")
            draw.text((bbox.left, bbox.top - 5), text, fill='red', font=small)

        image.save(os.path.join(output_directory, os.path.basename(self.path)))
        with open(tags_file, 'a', encoding='utf-8') as f:
            line = '"{}"\t'.format(
                self.path) + ','.join(['"{}"'.format(tag) for tag in tags])
            f.write(line)
