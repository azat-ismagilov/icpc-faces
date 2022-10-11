import argparse
import traceback
import re
import csv

from exiftool import ExifToolHelper


def digiKam_format(picasa_format):
    left, top, right, bottom = [int(picasa_format[i:i+4], 16) / 65535
                                for i in range(0, len(picasa_format), 4)]
    rectangle = [left, top, right - left, bottom - top]
    return ', '.join(str(x) for x in rectangle)


def main():
    parser = argparse.ArgumentParser(
        description='Embed digiKam tags from picasa file')
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
                names = []
                types = []
                rectangles = []
                for tag in tags:
                    match = re.match(r'"(.*)\(([a-f0-9]{16})\)"', tag)
                    if match:
                        name, picasa_format = match.groups()

                        names.append(name)
                        types.append('Face')
                        rectangles.append(digiKam_format(picasa_format))

                et.set_tags(path, tags={
                    'XMP:RegionName': names,
                    'XMP:RegionType': types,
                    'XMP:RegionRectangle': rectangles,
                    'XMP:RegionPersonDisplayName': names,
                })

            except Exception:
                traceback.print_exc()


if __name__ == '__main__':
    main()
