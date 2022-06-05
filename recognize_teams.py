import time
from tqdm import tqdm

import config
from library.image_process import GroupImageProcess, find_photos_by_tag
from library.teams_processor import process_teams


def main():
    start = time.time()

    image_paths = find_photos_by_tag(config.group_images_directory)
    images = [GroupImageProcess(image_path) for image_path in tqdm(image_paths, desc="Face detection and ocr")]
    print("Processed all images: {}".format(time.time() - start))

    process_teams(config.csv_path, config.group_output_directory, images)
    print("Time elapsed: {}".format(time.time() - start))


if __name__ == '__main__':
    main()
