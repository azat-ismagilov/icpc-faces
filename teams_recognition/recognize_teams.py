import pickle
import time
import argparse
from tqdm import tqdm

from image_process import GroupImageProcess, find_photos_by_tag
from teams_processor import process_teams


def main():
    parser = argparse.ArgumentParser(
        description='Generate faces info in picasa format from images with badges',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('teams_csv', type=str,
                        help='a csv file containing the team and name columns')
    parser.add_argument('input_dir', type=str,
                        help='input images directory')
    parser.add_argument('output_dir', type=str,
                        help='output images directory', default='output/', nargs='?')
    parser.add_argument('tags_file', type=str,
                        help='tags file', default='tags.txt', nargs='?')
    parser.add_argument('--delimiter', dest='delimiter', metavar='D',
                        type=str, help='delimiter for teams file', default=';')
    args = parser.parse_args()

    start = time.time()
    try:
        with open('save.pkl', 'rb') as f:
            images = pickle.load(f)
        print('You are using precalculated images info. If you want to update your images, please delete save.pkl.')
    except:
        image_paths = find_photos_by_tag(args.input_dir)
        images = [GroupImageProcess(image_path) for image_path in
                  tqdm(image_paths, desc="Face detection and ocr")]
        print("Processed all images: {}".format(time.time() - start))
        with open('save.pkl', 'wb') as f:
            pickle.dump(images, f)

    process_teams(args.teams_csv, args.delimiter,
                  args.output_dir, args.tags_file, images)
    print("Time elapsed: {}".format(time.time() - start))


if __name__ == '__main__':
    main()
