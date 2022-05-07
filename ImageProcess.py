import face_recognition

import config


class ImageProcess:
    def __init__(self, image_path):
        self.path = image_path
        self.ocr = config.readtext(self.path)

        image = face_recognition.load_image_file(self.path)
        self.face_locations = face_recognition.face_locations(image)