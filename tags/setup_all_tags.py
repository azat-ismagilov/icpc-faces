import argparse
import csv
import traceback

from methods import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Get tags from path',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('dir', type=str,
                        help='Input dir images', default='*', nargs='?')
    parser.add_argument('album_tag', type=str,
                        help='Album tag to add', default='album$2021', nargs='?')
    parser.add_argument('tags_file', type=str,
                        help='Name of the debug file will ', default='tags.txt', nargs='?')
    args = parser.parse_args()

    with open(args.tags_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t', quotechar='"',
                            lineterminator='\n', quoting=csv.QUOTE_ALL)
        for path in find_photos_in_directory(args.dir):
            try:
                tags = [args.album_tag] + \
                    get_tags_from_photo(path) + \
                    get_tags_from_path(args.dir, path) + \
                    convert_digiKam_tags_to_picasa(path)

                tags = list(dict.fromkeys(tags))

                embed_tags_into_photo(path, tags)
                embed_picasa_as_digiKam(path, tags)
                set_description(path, tags)
                writer.writerow([path] + tags)
                print('.', end='', flush=True)
            except Exception:
                print(path)
                traceback.print_exc()
