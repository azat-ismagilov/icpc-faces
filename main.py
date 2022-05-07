import logging
import os
import pickle
import time

from iptcinfo3 import IPTCInfo

import TeamProcess
import config
from ImageProcess import ImageProcess


def find_photos_by_tag(images_directory, group_photo_tag):
    result = []
    for path in os.listdir(images_directory):
        if path.endswith(".png") or path.endswith(".jpg") or path.endswith(".jpeg"):
            file = os.path.join(images_directory, path)
            if group_photo_tag in IPTCInfo(file)['keywords']:
                result.append(file)
    return result


def main():
    iptcinfo_logger = logging.getLogger('iptcinfo')
    iptcinfo_logger.setLevel(logging.ERROR)
    start = time.time()

    image_paths = find_photos_by_tag(config.images_directory, config.group_photo_tag)
    images = [ImageProcess(image_path) for image_path in image_paths]
    print("Processed all images: {}".format(time.time() - start))

    with open('save.pkl', 'wb') as f:
        pickle.dump(images, f)

    with open('save.pkl', 'rb') as f:
        images = pickle.load(f)

    teams_processor = TeamProcess.TeamsProcessor(config.csv_path)
    teams_processor.match_team_images(images)
    print("All teams matched: {}".format(time.time() - start))

    teams_processor.save_new_photos(config.output_directory)
    print("Time elapsed: {}".format(time.time() - start))


if __name__ == '__main__':
    main()
