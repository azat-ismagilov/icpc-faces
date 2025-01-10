import requests
import numpy as np
from PIL import Image
from io import BytesIO
from deepface import DeepFace

from src.utils import FlickrPhoto, BoundingBox

def get_face_embedding(image: FlickrPhoto) -> list:
    response = requests.get(image.url())
    response.raise_for_status()

    image = Image.open(BytesIO(response.content))

    image_array = np.array(image)

    try:
        bboxes = DeepFace.represent(image_array, model_name='Facenet', detector_backend='retinaface')
    except:
        return []

    return [BoundingBox.from_deepface(bbox, *image_array.shape[:-1]) for bbox in bboxes]
