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
    
@dataclass
class Person:
    name: Optional[str] = None
    embeddings: Optional[list] = None
    
@dataclass
class BoundingBox:
    left: int
    top: int
    right: int
    bottom: int
    person: Optional[Person] = None

    def __iter__(self):
        return iter((self.left, self.top, self.right, self.bottom))

    def toPIL(self):
        return (self.left, self.top, self.right, self.bottom)

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
