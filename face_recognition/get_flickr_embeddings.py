import argparse
import json
import os
from dotenv import load_dotenv
from tqdm import tqdm

from src.flickr import FlickrAPI
from src.recognition import get_face_embedding
from src.utils import match_boxes


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(
        description='Get tags from path',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-user_id', type=str,
                        help='Id of the flickr owner of the album')
    parser.add_argument('-tags', nargs='+', help='Photo tags', required=True)
    parser.add_argument('-output_file', type=str,
                        help='Output file with the embeddings', default='embeddings.json')
    parser.add_argument('-raw_embeddings', type=str,
                        help='Output file with the raw embeddings')
    args = parser.parse_args()

    flickr = FlickrAPI(api_key=os.getenv('FLICKR_API_KEY'),
                       api_secret=os.getenv('FLICKR_API_SECRET'))
    photos = flickr.walk(args.user_id, args.tags)

    embeddings = []
    raw_embeddings = []

    for photo in tqdm(photos, desc="Get embeddings"):
        bb_flickr = flickr.get_bounding_boxes(photo)
        bb_recognition = get_face_embedding(photo)
        matches = match_boxes(bb_flickr, bb_recognition)

        embeddings.extend([bb.to_json(photo.id) for bb in matches])
        raw_embeddings.extend([bb.to_json(photo.id) for bb in bb_recognition])
    
    with open(args.output_file, 'w') as file:
        json.dump(embeddings, file, indent=4, separators=(',', ': '))

    if args.raw_embeddings is not None:
        with open(args.raw_embeddings, 'w') as file:
            json.dump(raw_embeddings, file, indent=4, separators=(',', ': '))

if __name__ == '__main__':
    main()

