import csv
import argparse
import traceback
import methods


def convert_digiKam_to_picasa():
    parser = argparse.ArgumentParser(
        description='Convert digiKam tags to Picasa format',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'dir', type=str, help='Input dir images', default='./', nargs='?')
    parser.add_argument('tags_file', type=str,
                        help='Name of the output file', default='tags.txt', nargs='?')
    args = parser.parse_args()

    with open(args.tags_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t', quotechar='"',
                            lineterminator='\n', quoting=csv.QUOTE_ALL)
        for path in methods.find_photos_in_directory(args.dir):
            try:
                writer.writerow(
                    [path] + methods.convert_digiKam_tags_to_picasa(path))
            except Exception:
                print(path)
                traceback.print_exc()


if __name__ == '__main__':
    convert_digiKam_to_picasa()
