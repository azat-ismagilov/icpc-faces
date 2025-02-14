from dataclasses import dataclass
import re
from typing import Optional

@dataclass
class FlickrPhoto:
    id: str
    secret: str
    server: str
    farm: str
    title: str
    isprimary: str
    ispublic: int
    isfriend: int
    isfamily: int

    def url(self):
        return f"https://farm{self.farm}.staticflickr.com/{self.server}/{self.id}_{self.secret}.jpg"

    @staticmethod
    def from_json(json):
        return FlickrPhoto(
            id=json['id'],
            secret=json['secret'],
            server=json['server'],
            farm=json['farm'],
            title=json['title'],
            isprimary=json['isprimary'],
            ispublic=json['ispublic'],
            isfriend=json['isfriend'],
            isfamily=json['isfamily']
        )
    
    @staticmethod
    def from_etree(etree):
        return FlickrPhoto(
            id=etree.get('id'),
            secret=etree.get('secret'),
            server=etree.get('server'),
            farm=etree.get('farm'),
            title=etree.get('title'),
            isprimary=etree.get('isprimary'),
            ispublic=etree.get('ispublic'),
            isfriend=etree.get('isfriend'),
            isfamily=etree.get('isfamily'),
        )
    
@dataclass
class Person:
    name: Optional[str] = None
    embeddings: Optional[list] = None
    
@dataclass
class BoundingBox:
    """
    All coordinates are normalized to the image size
    to be compatible with flickr.
    """
    left: float
    top: float
    right: float
    bottom: float
    person: Optional[Person] = None

    def __iter__(self):
        return iter((self.left, self.top, self.right, self.bottom))

    def to_pil(self):
        return (self.left, self.top, self.right, self.bottom)
    
    def to_flickr(self):
        top = "%0.4x" % int(self.top * 65535)
        bottom = "%0.4x" % int(self.bottom * 65535)
        left = "%0.4x" % int(self.left * 65535)
        right = "%0.4x" % int(self.right * 65535)
        return left + top + right + bottom
    
    def to_json(self, photo_id=None):
        return {
            'name': self.person.name,
            'embeddings': [self.person.embeddings],
            'bounding_boxes': [
                {
                    'bbox': self.to_flickr(),
                    'photo_id': photo_id,
                }
            ]
        }

    @staticmethod
    def from_flickr(flickr_tag: str):
        name, bbox, _ = re.split('\(|\)', flickr_tag)

        left, top, right, bottom = [int(bbox[i:i+4], 16) / 65535
                                for i in range(0, len(bbox), 4)]
        
        return BoundingBox(left, top, right, bottom, Person(name, None))
    
    @staticmethod
    def from_deepface(bbox: dict, height: int, width: int):
        return BoundingBox(bbox['facial_area']['x'] / width, bbox['facial_area']['y'] / height,
                           (bbox['facial_area']['x'] + bbox['facial_area']['w']) / width,
                           (bbox['facial_area']['y'] + bbox['facial_area']['h']) / height,
                           Person(None, bbox['embedding']))
