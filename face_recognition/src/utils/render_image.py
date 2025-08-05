import os
from src.utils import BoundingBox
import flickrapi
import requests
from PIL import Image, ImageDraw
from io import BytesIO

def download_image_from_flickr(username: str, photo_id: str) -> Image.Image:
    """
    Download an image from Flickr using username and photo ID.
    
    Args:
        username: Flickr username
        photo_id: ID of the photo to download
        api_key: Flickr API key
        api_secret: Flickr API secret
    
    Returns:
        PIL Image object
    """
    # Initialize Flickr API
    flickr = flickrapi.FlickrAPI(os.getenv('FLICKR_API_KEY'), os.getenv('FLICKR_API_SECRET'), format='parsed-json')
    
    # Get available sizes for the photo
    sizes = flickr.photos.getSizes(photo_id=photo_id)
    
    # Find the largest available size
    largest_size = max(sizes['sizes']['size'], key=lambda x: int(x['width']) * int(x['height']))
    image_url = largest_size['source']
    
    # Download the image
    response = requests.get(image_url)
    response.raise_for_status()
    
    # Convert to PIL Image
    image = Image.open(BytesIO(response.content))
    return image

def render_image(state: dict, cut: bool = False, path: str = 'static') -> str:
    flickr_bb = state['bounding_boxes'][0]['bbox']
    bounding_box = BoundingBox.from_flickr_bbox(flickr_bb)
    photo_id = state['bounding_boxes'][0]['photo_id']
    photo = download_image_from_flickr("icpcnews", photo_id)
    if cut:
        # Crop the image to the bounding box
        left = int(bounding_box.left * photo.width)
        upper = int(bounding_box.top * photo.height)
        right = int(bounding_box.right * photo.width)
        lower = int(bounding_box.bottom * photo.height)
        photo = photo.crop((left, upper, right, lower))
        photo.save(f'{path}/{photo_id}.jpg')
        return f'{path}/{photo_id}.jpg'
    else:
        # Draw the bounding box on the full image
        draw = ImageDraw.Draw(photo)
        draw.rectangle(
            [bounding_box.left * photo.width, bounding_box.top * photo.height,
             bounding_box.right * photo.width, bounding_box.bottom * photo.height],
            outline="red", width=5
        )
        # Save the full image
        photo.save(f'{path}/{photo_id}_full.jpg')
        return f'{path}/{photo_id}_full.jpg'
