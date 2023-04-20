import glob
import os
import re
from typing import List
import random
from iptcinfo3 import IPTCInfo
import logging
from lxml import etree

def get_iptc_instance(path):
    iptcinfo_logger = logging.getLogger('iptcinfo')
    iptcinfo_logger.setLevel(logging.ERROR)
    return IPTCInfo(path)

def try_decode(s):
    try:
        return s.decode()
    except:
        return ''


def get_list_str(inp, field):
    tags = inp.get(field, [])
    if type(tags) != list:
        tags = [tags]
    return tags


def find_photos_in_directory(dir) -> List:
    result = []
    for path in glob.glob(os.path.join(dir, '**/*'), recursive=True):
        if not path.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        result.append(path)
    return result


def get_tags_from_path(dir, path) -> List[str]:
    parts = path.split(os.sep)[:-1]
    tags = ['event$' + parts[0].replace('_', ' ')]
    if len(parts) > 1:
        tags += ['photographer$' + parts[1].replace('_', ' ').split('-')[0]] + parts[2:]

    return tags


def get_tags_from_photo(path) -> List[str]:
    info = get_iptc_instance(path)
    return [try_decode(s) for s in info['keywords']]


def embed_tags_into_photo(path, tags):
    tags = get_tags_from_photo(path) + tags
    tags = list(dict.fromkeys(tags))

    # tags = [s for s in tags if str(s).startswith("team$")]

    # caterories = '<Categories>' + \
    #     ''.join(['<Category Assigned="1">' + str(tag) +
    #             '</Category>' for tag in tags]) + '</Categories>'

    info = get_iptc_instance(path)
    info['keywords'] = [bytes(s, encoding="raw_unicode_escape") for s in tags]
    info.save(options=["overwrite"])


def get_description_from_photo(path) -> str:
    info = get_iptc_instance(path)
    if info['caption/abstract'] is None:
        return ''
    return info['caption/abstract'].decode()


def set_description(path, tags):
    photographer = None
    for tag in tags:
        if tag.startswith('photographer$'):
            photographer = tag[len('photographer$'):]

    if photographer == None:
        return

    description = get_description_from_photo(path)

    if photographer in description:
        return

    description = f'Photographer: {photographer} ' + description
    info = get_iptc_instance(path)
    info['caption/abstract'] = description
    info.save(options=["overwrite"])


def rectangle_format(picasa_format):
    left, top, right, bottom = [int(picasa_format[i:i+4], 16) / 65535
                                for i in range(0, len(picasa_format), 4)]
    return left, top, right, bottom


def digiKam_format(picasa_format):
    left, top, right, bottom = rectangle_format(picasa_format)
    return ', '.join(str(x) for x in [left, top, right - left, bottom - top])


def get_xmp(path):
    with open(path, 'rb') as f:
        jpeg_data = f.read()

    xmp_start = jpeg_data.find(b'<x:xmpmeta')
    xmp_end = jpeg_data.find(b'</x:xmpmeta')
    if xmp_start == -1 or xmp_end == -1:
        return None

    xmp_str = jpeg_data[xmp_start:xmp_end + len('</x:xmpmeta>')]
    xmp = etree.XML(xmp_str, etree.XMLParser(remove_blank_text=True))

    return xmp


def set_xmp(path, xmp):
    if xmp is None:
        return

    with open(path, 'rb') as f:
        jpeg_data = f.read()

    xmp_start = jpeg_data.find(b'<x:xmpmeta')
    xmp_end = jpeg_data.find(b'</x:xmpmeta')
    if xmp_start == -1 or xmp_end == -1:
        return

    xmp_str = etree.tostring(xmp, pretty_print=True)
    jpeg_data = jpeg_data[:xmp_start] + xmp_str + \
        jpeg_data[xmp_end + len('</x:xmpmeta>'):]

    with open(path, 'wb') as f:
        f.write(jpeg_data)


def xmp_namespaces():
    return {"mwgrs": "http://www.metadataworkinggroup.com/schemas/regions/",
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "xmp": "http://ns.adobe.com/xap/1.0/",
            "stDim": "http://ns.adobe.com/xap/1.0/sType/Dimensions#",
            "stArea": "http://ns.adobe.com/xmp/sType/Area#",
            "mp": "http://ns.microsoft.com/photo/1.2/",
            "mpr": "http://ns.microsoft.com/photo/1.2/t/Region#",
            "mpri": "http://ns.microsoft.com/photo/1.2/t/RegionInfo#"
            }


def remove_regions_info(xmp):
    if xmp is None:
        return

    region_tags = xmp.xpath("//mpri:Regions", namespaces=xmp_namespaces()) + \
        xmp.xpath("//mwgrs:RegionList", namespaces=xmp_namespaces())
    for region in region_tags:
        region.getparent().remove(region)


def embed_picasa_as_digiKam(path, tags):
    # Does not work right now
    xmp = get_xmp(path)
    # names = []
    # types = []
    # rectangles = []
    # for tag in tags:
    #     match = re.match(r'(.*)\(([a-f0-9]{16})\)', tag)
    #     if match:
    #         name, picasa_format = match.groups()

    #         if name == "":
    #             name = str(random.randint(1, 10000))
    #         names.append(name)
    #         types.append('Face')
    #         rectangles.append(digiKam_format(picasa_format))

    set_xmp(path, xmp)


def picasa_format(rectangle_digiKam):
    rectangle = [float(x) for x in rectangle_digiKam.split(',')]
    left = rectangle[0]
    top = rectangle[1]
    right = rectangle[0] + rectangle[2]
    bottom = rectangle[1] + rectangle[3]
    return ("".join(["%0.4x" % int(x * 65535)
                     for x in [left, top, right, bottom]]))


def convert_digiKam_tags_to_picasa(path) -> List[str]:
    xmp = get_xmp(path)
    if xmp is None:
        return []

    region_infos = xmp.xpath("//mpri:Regions", namespaces=xmp_namespaces())

    picasa_faces = []
    for region_info in region_infos:
        for region in region_info.xpath(".//rdf:li", namespaces=xmp_namespaces()):
            name = region.get("{%s}PersonDisplayName" %
                              xmp_namespaces()["mpr"])
            rectangle_digiKam = region.get(
                "{%s}Rectangle" % xmp_namespaces()["mpr"])

            picasa = picasa_format(rectangle_digiKam)
            picasa_faces.append(f'{name}({picasa})')

    return picasa_faces
