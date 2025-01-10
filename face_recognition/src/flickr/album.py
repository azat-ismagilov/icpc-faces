import flickrapi

from src.utils import FlickrPhoto

class FlickrAlbum:
    def __init__(
        self,
        flickr: flickrapi.FlickrAPI,
        album_id: str,
        user_id: str
    ):
        """
        Initialize the Flickr album.

        Input:
            flickr (flickrapi.FlickrAPI): The Flickr API.
            album_id (str): The ID of the album.
            user_id (str): The ID of the user who owns the album.
        """

        self.flickr = flickr
        self.album_id = album_id
        self.user_id = user_id

        self.photos = self._get_photo_ids()

    def _get_photo_ids(self) -> list:
        """
        Get the photo IDs in the album.

        Output:
            list: The photo IDs.
        """

        try:
            pages = self.flickr.photosets.getPhotos(
                photoset_id=self.album_id,
                user_id=self.user_id
            )['photoset']['pages']
        except flickrapi.exceptions.FlickrError as e:
            print(f"Error fetching album photos: {e}")
            return []

        photos = []

        for i in range(1, pages + 1):
            try:
                photos += self.flickr.photosets.getPhotos(
                    photoset_id=self.album_id,
                    user_id=self.user_id,
                    page=i
                )['photoset']['photo']
            except flickrapi.exceptions.FlickrError as e:
                print(f"Error fetching album photos: {e}")
                return photos

        return [FlickrPhoto(**photo) for photo in photos]

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
