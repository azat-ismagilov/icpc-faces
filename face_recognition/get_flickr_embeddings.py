import argparse
import json
import os
from dotenv import load_dotenv
from tqdm import tqdm

from src.flickr import FlickrAPI
from src.recognition import get_face_embedding
from src.utils import is_team_photo, match_boxes


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description='Get tags from path',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('album_id', type=str,
                        help='Id of the flickr album')
    parser.add_argument('user_id', type=str,
                        help='Id of the flickr owner of the album')
    parser.add_argument('output_file', type=str,
                        help='Output file with the embeddings', default='embeddings.json')
    args = parser.parse_args()

    flickr = FlickrAPI(api_key=os.getenv('FLICKR_API_KEY'),
                       api_secret=os.getenv('FLICKR_API_SECRET'))
    album = flickr.get_album(args.album_id, args.user_id)

    embeddings = []

    for photo in tqdm(album.photos):
        if not is_team_photo(flickr.get_tags(photo)):
            continue
        
        bb_flickr = flickr.get_bounding_boxes(photo)
        bb_recognition = get_face_embedding(photo)
        matches = match_boxes(bb_flickr, bb_recognition)

        embeddings.extend([{
            'name': bb.person.name,
            'embeddings': [bb.person.embeddings],
            'bounding_boxes': [
                {
                    'left': bb.left,
                    'top': bb.top,
                    'right': bb.right,
                    'bottom': bb.bottom,
                    'photo_id': photo.id,
                }
            ]
        }
                           for bb in matches])
    
    with open(args.output_file, 'w') as file:
        json.dump(embeddings, file, indent=4, separators=(',', ': '))

if __name__ == '__main__':
    main()

