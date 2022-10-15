import glob
import os
import re
from typing import List
from exiftool import ExifToolHelper


def find_photos_in_directory(dir) -> List:
    result = []
    for path in glob.glob(os.path.join(dir, '**/*'), recursive=True):
        if not path.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        result.append(path)
    return result


def get_tags_from_path(dir, path) -> List[str]:
    return path[len(dir):].split('/')[:-1]


def get_tags_from_photo(path) -> List[str]:
    et = ExifToolHelper()
    tags = []
    for cur_tags in et.get_tags(path, tags=['IPTC:Keywords']):
        tags = cur_tags.get('IPTC:Keywords', []) + tags
    return tags


def set_description(path, tags):
    photographer = None
    for tag in tags:
        if tag.startswith('photographer$'):
            photographer = tag[len('photographer$'):]

    if photographer == None:
        return

    et = ExifToolHelper()
    description = ""
    for cur_description in et.get_tags(path, tags=['EXIF:ImageDescription']):
        description += cur_description.get('EXIF:ImageDescription', "")

    if photographer in description:
        return

    description = f'Photographer: {photographer}\n' + description
    # TODO - check where to store description for flickr
    et.set_tags(path, tags={
        'EXIF:ImageDescription': description,
        'XMP:ImageDescription': description,
        'XMP:Description': description
    })


def embed_tags_into_photo(path, tags):
    et = ExifToolHelper()

    tags = get_tags_from_photo(path) + tags
    tags = list(dict.fromkeys(tags))

    et.set_tags(path, tags={
        'IPTC:Keywords': tags,
    })


def rectangle_format(picasa_format):
    left, top, right, bottom = [int(picasa_format[i:i+4], 16) / 65535
                                for i in range(0, len(picasa_format), 4)]
    return left, top, right, bottom


def digiKam_format(picasa_format):
    left, top, right, bottom = rectangle_format(picasa_format)
    return ', '.join(str(x) for x in [left, top, right - left, bottom - top])


def embed_picasa_as_digiKam(path, tags):
    et = ExifToolHelper()
    names = []
    types = []
    rectangles = []
    for tag in tags:
        match = re.match(r'(.*)\(([a-f0-9]{16})\)', tag)
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


def picasa_format(rectangle_digiKam):
    rectangle = [float(x) for x in rectangle_digiKam.split(',')]
    left = rectangle[0]
    top = rectangle[1]
    right = rectangle[0] + rectangle[2]
    bottom = rectangle[1] + rectangle[3]
    return ("".join(["%0.4x" % int(x * 65535)
                     for x in [left, top, right, bottom]]))


def convert_digiKam_tags_to_picasa(path) -> List[str]:
    et = ExifToolHelper()
    picasa_faces = []
    for tags in et.get_tags(path, ['XMP:RegionName', 'XMP:RegionType', 'XMP:RegionRectangle']):
        for name, type, rectangle_digiKam in zip(tags.get('XMP:RegionName', []),
                                                 tags.get(
                                                     'XMP:RegionType', []),
                                                 tags.get('XMP:RegionRectangle', [])):
            if type != 'Face':
                continue

            picasa = picasa_format(rectangle_digiKam)
            picasa_faces.append(f'{name}({picasa})')
    return picasa_faces
