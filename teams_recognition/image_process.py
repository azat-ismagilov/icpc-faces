from typing import List, Tuple

import os
import face_recognition
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from iptcinfo3 import IPTCInfo

import params as params
from rectangle import *
from team import Team


def find_photos_by_tag(images_directory, group_photo_tag=None):
    result = []
    for file in os.listdir(images_directory):
        if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        path = os.path.join(images_directory, file)
        if group_photo_tag == None or group_photo_tag in IPTCInfo(path)['keywords']:
            result.append(path)
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

            crop_ocr = params.Reader.readtext(np.array(cropped))

            ocr += [(Box(body_left + min_gx, body_top + min_gy, body_left + max_gx, body_top + max_gy), text)
                    for (([min_gx, min_gy], _, [max_gx, max_gy], _), text) in crop_ocr]

        return ocr

    def __convert_bbox(self, bbox: Box):
        top = "%0.4x" % int(bbox.top / self.height * 65535)
        bottom = "%0.4x" % int(bbox.bottom / self.height * 65535)
        left = "%0.4x" % int(bbox.left / self.width * 65535)
        right = "%0.4x" % int(bbox.right / self.width * 65535)
        return left + top + right + bottom

    def save(self, output_directory, writer):
        os.makedirs(output_directory, exist_ok=True)
        image = Image.open(self.path)
        if image is None or image.size == 0:
            return

        draw = ImageDraw.Draw(image)
        giant = ImageFont.truetype('arial.ttf', 150)
        normal = ImageFont.truetype('arial.ttf', 100)
        small = ImageFont.truetype('arial.ttf', 50)

        tags = []
        processed_faces = []

        if self.team:
            team = self.team
            draw.text((100, 100), team.name, font=giant,
                      fill='white', stroke_width=2, stroke_fill='black')
            draw.text((200, 250), ', '.join([participant.name for participant in team.participants]), font=small,
                      fill='white', stroke_width=2, stroke_fill='black')
            tags.append(f'team${team.name}')

            for (name, face_bbox) in team.participants:
                if face_bbox is None:
                    continue
                draw.rectangle(face_bbox.toPIL(), outline="green", width=5)
                draw.text((face_bbox.left, face_bbox.top - 100), name, font=normal,
                          fill='white', stroke_width=2, stroke_fill='black')

                tags.append(f'{name}({self.__convert_bbox(face_bbox)})')

            processed_faces += [x.face_bbox for x in team.participants]

        # TODO: Rewrite
        rest_bbox = [
            face_bbox for face_bbox in self.face_locations if face_bbox not in processed_faces]

        for face_bbox in rest_bbox:
            draw.rectangle(face_bbox.toPIL(), outline="red")
            tags.append(f'({self.__convert_bbox(face_bbox)})')

        for (bbox, text) in self.ocr:
            draw.rectangle(bbox.toPIL(), outline="red")
            draw.text((bbox.left, bbox.top + 200), text, font=small,
                      fill='white', stroke_width=2, stroke_fill='black')

        image.save(os.path.join(output_directory, os.path.basename(self.path)))

        writer.writerow([self.path] + tags)
