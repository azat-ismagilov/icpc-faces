import csv
import argparse
import traceback
import methods


def get_tags_from_path():
    parser = argparse.ArgumentParser(
        description='Get tags from path',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('dir', type=str,
                        help='Input dir images', default='./', nargs='?')
    parser.add_argument('album_tag', type=str,
                        help='Album tag to add', default='album$2021', nargs='?')
    parser.add_argument('tags_file', type=str,
                        help='Name of the output file', default='tags.txt', nargs='?')
    args = parser.parse_args()

    with open(args.tags_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t', quotechar='"',
                            lineterminator='\n', quoting=csv.QUOTE_ALL)
        for path in methods.find_photos_in_directory(args.dir):
            try:
                tags = [args.album_tag] + \
                    methods.get_tags_from_path(args.dir, path)
                writer.writerow([path] + tags)
            except Exception:
                print(path)
                traceback.print_exc()


if __name__ == '__main__':
    get_tags_from_path()
