import time
from tqdm import tqdm

import config
from library.regular_processor import get_known_face_encodings, process_regular
from library.image_process import find_photos_by_tag


def main():
    start = time.time()

    known_faces = get_known_face_encodings(
        find_photos_by_tag(config.group_output_directory))
    print("Processed all known faces: {}".format(time.time() - start))

    images = find_photos_by_tag(config.regular_images_directory)
    process_regular(config.regular_output_directory, known_faces, images)
    print("Time elapsed: {}".format(time.time() - start))


if __name__ == '__main__':
    main()
