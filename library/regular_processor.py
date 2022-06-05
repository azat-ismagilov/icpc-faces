from typing import List, Any
from dataclasses import dataclass

import os
import cv2
import json
import face_recognition
import numpy as np

import config
from library.team import Participant


@dataclass
class KnownFace:
    name: str
    face_encoding: Any


def __process_regular_image(path, output_directory, known_faces: List[KnownFace], tolerance):
    image = face_recognition.load_image_file(path)
    face_locations = face_recognition.face_locations(image)
    face_encodings = face_recognition.face_encodings(image, face_locations)

    known_face_encodings = [face.face_encoding for face in known_faces]
    known_face_names = [face.name for face in known_faces]

    participants = []

    for face_encoding, face_bbox in zip(face_encodings, face_locations):
        face_distances = face_recognition.face_distance(
            known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        name = 'Unknown'
        if face_distances[best_match_index] <= tolerance:
            name = known_face_names[best_match_index]

        participants.append(Participant(name, face_bbox))

    __save_regular_image(path, output_directory, participants)


def __save_regular_image(path, output_directory, participants: List[Participant]):
    os.makedirs(output_directory, exist_ok=True)
    image = cv2.imread(path)
    for participant in participants:
        if participant.face_bbox is None:
            continue
        (top, right, bottom, left) = participant.face_bbox
        cv2.rectangle(image, (left, top),
                      (right, bottom), (255, 255, 255), 5)
        cv2.putText(image, participant.name, (left, top - 20),
                    cv2.FONT_HERSHEY_DUPLEX, 3, (0, 0, 255), 4)
    cv2.imwrite(os.path.join(output_directory,
                os.path.basename(path)), image)
    with open(os.path.join(output_directory, os.path.basename(path) + ".json"), 'w') as f:
        data = {
            'people': [x.name for x in participants],
            'bbox': [x.face_bbox for x in participants]
        }
        json.dump(data, f)


def get_known_face_encodings(image_paths: List) -> List[KnownFace]:
    result = []
    for path in image_paths:
        with open(path + ".json", 'r') as f:
            data = json.load(f)

            participants = [Participant(name, bbox)
                            for name, bbox in zip(data['people'], data['bbox'])
                            if bbox is not None]

            image = face_recognition.load_image_file(path)
            known_face_encodings = face_recognition.face_encodings(
                image, [participant.face_bbox for participant in participants])

            for participant, encoding in zip(participants, known_face_encodings):
                result.append(KnownFace(participant.name, encoding))
    return result


def process_regular(output_directory, known_face_encodings: List[KnownFace], image_paths: List, tolerance=0.6):
    for image_path in image_paths:
        __process_regular_image(
            image_path, output_directory, known_face_encodings, tolerance)
