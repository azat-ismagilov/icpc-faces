import flickrapi
from tqdm import tqdm

from src.utils import FlickrPhoto

class FlickrWalk:
    def __init__(
        self,
        flickr: flickrapi.FlickrAPI,
        user_id: str,
        tags: list,
    ):
        """
        Initialize the Flickr album.

        Input:
            flickr (flickrapi.FlickrAPI): The Flickr API.
            user_id (str): The ID of the user who owns the album.
            tags (list): list of photo tags.
        """

        self.flickr = flickr
        self.user_id = user_id
        self.tags = tags

        self.photos = self._get_photos()

    def _get_photos(self) -> list:
        """
        Get the photo IDs in the album.

        Output:
            list: The photo IDs.
        """

        try:
            photos = self.flickr.walk(
                user_id=self.user_id,
                tags=",".join(self.tags),
                tag_mode='all',
            )
        except flickrapi.exceptions.FlickrError as e:
            print(f"Error fetching album photos: {e}")
            return []

        return [FlickrPhoto.from_etree(photo) for photo in tqdm(photos, desc="Load photos")]

    def __getitem__(self, key: int) -> FlickrPhoto:
        """
        Get a photo from the album.

        Input:
            key (int): The index of the photo.
        Output:
            FlickrPhoto: The photo.
        """

        return self.photos[key]

    def __iter__(self):
        """
        Iterate over the photos in the album.
        """

        return iter(self.photos)
