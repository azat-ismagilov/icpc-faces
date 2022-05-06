import face_recognition

import config


class ImageProcess:
    def __init__(self, imagepath):
        """Constructor"""
        self.path = imagepath
        self.ocr = config.readtext(imagepath)
        image = face_recognition.load_image_file(self.path)
        self.face_locations = face_recognition.face_locations(image)