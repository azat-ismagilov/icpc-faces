import pickle
import time
from tqdm import tqdm

import config
from library.image_process import GroupImageProcess, find_photos_by_tag
from library.teams_processor import process_teams


def main():
    start = time.time()

    try:
        with open('save.pkl', 'rb') as f:
            images = pickle.load(f)
        print('You are using precalculated images info. If you want to update your images, please delete save.pkl')
    except:
        image_paths = find_photos_by_tag(config.group_images_directory)
        images = [GroupImageProcess(image_path) for image_path in tqdm(image_paths, desc="Face detection and ocr")]
        print("Processed all images: {}".format(time.time() - start))
        with open('save.pkl', 'wb') as f:
            pickle.dump(images, f)

    process_teams(config.csv_path, config.group_output_directory, config.tags_file, images)
    print("Time elapsed: {}".format(time.time() - start))


if __name__ == '__main__':
    main()
