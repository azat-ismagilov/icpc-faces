import argparse
import traceback
import csv

from exiftool import ExifToolHelper

def main():
    parser = argparse.ArgumentParser(
        description='Embed tags from file to images',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('tags_file', type=str,
                        help='Tags file', default='tags.txt', nargs='?')
    args = parser.parse_args()

    et = ExifToolHelper()
    with open(args.tags_file, 'r', encoding='utf-8') as f:
        rd = csv.reader(f, delimiter='\t', quotechar='"', lineterminator='\n')
        for row in rd:
            try:
                path = row[0]
                tags = row[1:]

                for d in et.get_tags(path, tags=['IPTC:Keywords']):
                    tags = d['IPTC:Keywords'] + tags

                tags = list(dict.fromkeys(tags))

                et.set_tags(path, tags={
                    'Keywords': tags,
                })
            except Exception:
                traceback.print_exc()


if __name__ == '__main__':
    main()
