import os
import csv
import argparse
import traceback

from exiftool import ExifToolHelper


def picasa_format(rectangle_digiKam):
    rectangle = [float(x) for x in rectangle_digiKam.split(',')]
    left = rectangle[0]
    top = rectangle[1]
    right = rectangle[0] + rectangle[2]
    bottom = rectangle[1] + rectangle[3]
    return ("".join(["%0.4x" % int(x * 65535)
                     for x in [left, top, right, bottom]]))


def main():
    parser = argparse.ArgumentParser(
        description='Convert digiKam tags to Picasa format',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('dir', type=str, help='Input dir images', default='./', nargs='?')
    parser.add_argument('tags_file', type=str,
                        help='Name of the output file', default='tags.txt', nargs='?')
    args = parser.parse_args()

    with open(args.tags_file, 'w', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter='\t', quotechar='"', lineterminator='\n', quoting=csv.QUOTE_ALL)
        et = ExifToolHelper()

        for file in os.listdir(args.dir):
            if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
            try:
                path = os.path.join(args.dir, file)
                picasa_faces = []
                for tags in et.get_tags(path, ['XMP:RegionName', 'XMP:RegionType', 'XMP:RegionRectangle']):
                    for name, type, rectangle_digiKam in zip(tags['XMP:RegionName'], tags['XMP:RegionType'], tags['XMP:RegionRectangle']):
                        if type != 'Face':
                            continue

                        picasa = picasa_format(rectangle_digiKam)
                        picasa_faces.append(f'{name}({picasa})')

                writer.writerow([path] + picasa_faces)
            except Exception:
                traceback.print_exc()



if __name__ == '__main__':
    main()
