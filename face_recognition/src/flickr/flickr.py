import re
import flickrapi

from src.utils import BoundingBox
from src.flickr.album import FlickrAlbum
from src.utils import FlickrPhoto
from src.flickr.walk_result import FlickrWalk

class FlickrAPI:
    def __init__(self, api_key, api_secret):
        """
        Initialize the Flickr API.

        Input:
            api_key (str): The API key.
            api_secret (str): The API secret.
        """

        self.api_key = api_key
        self.api_secret = api_secret

        try:
            self.flickr = flickrapi.FlickrAPI(
                api_key, api_secret, format='parsed-json'
            )
        except flickrapi.exceptions.FlickrError as e:
            print(f"Error initializing Flickr API: {e}")
    
    def walk(self, user_id: str, tags: list) -> FlickrWalk:
        """
        Walk throw user photos.

        Input:
            user_id (str): The ID of the user who owns the album.
            tags (list): list of photo tags.
        Output:
            FlickrAlbum: The album.
        """

        return FlickrWalk(flickrapi.FlickrAPI(self.api_key, self.api_secret, format='etree'), user_id, tags)
    
    def get_album(self, album_id: str, user_id: str) -> FlickrAlbum:
        """
        Get an album from Flickr.

        Input:
            album_id (str): The ID of the album.
            user_id (str): The ID of the user who owns the album.
        Output:
            FlickrAlbum: The album.
        """

        return FlickrAlbum(self.flickr, album_id, user_id)
    
    def get_tags(self, photo: FlickrPhoto) -> list:
        """
        Get the tags of a photo.

        Input:
            photo (FlickrPhoto): The photo.
        Output:
            list: The tags.
        """

        try:
            tags = self.flickr.photos.getInfo(photo_id=photo.id)['photo']['tags']['tag']
        except flickrapi.exceptions.FlickrError as e:
            print(f"Error fetching photo sizes: {e}")
            return []

        return tags

    def get_bounding_boxes(self, photo: FlickrPhoto) -> list:
        """
        Get the bounding boxes of a photo.

        Input:
            photo (FlickrPhoto): The photo.
        Output:
            tuple: The bounding boxes.
        """

        try:
            tags = self.flickr.photos.getInfo(photo_id=photo.id)['photo']['tags']['tag']
        except flickrapi.exceptions.FlickrError as e:
            print(f"Error fetching photo sizes: {e}")
            return []

        return [BoundingBox.from_flickr(tag['raw']) for tag in tags if self._match_bbox(tag)]
    
    def _match_bbox(self, tag: dict) -> bool:
        """
        Check if a tag is a bounding box.

        Input:
            tag (dict): The tag.
        Output:
            bool: True if the tag is a bounding box, False otherwise.
        """

        string = tag['raw']

        return len(re.split('\(|\)', string)) == 3 and \
            len(re.split('\(|\)', string)[2]) == 0 and \
            len(re.split('\(|\)', string)[1]) == 16 and\
            (re.fullmatch('([a-f0-9])+', re.split('\(|\)', string)[1]) is not None)
