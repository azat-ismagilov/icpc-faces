import csv
import argparse
import traceback
import methods


def embed_tags_into_photo():
    parser = argparse.ArgumentParser(
        description='Embed tags from file to images',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('tags_file', type=str,
                        help='Tags file', default='tags.txt', nargs='?')
    args = parser.parse_args()

    with open(args.tags_file, 'r', encoding='utf-8') as f:
        rd = csv.reader(f, delimiter='\t', quotechar='"', lineterminator='\n')
        for row in rd:
            try:
                path = row[0]
                tags = row[1:]
                methods.embed_tags_into_photo(path, tags)
                methods.set_description(path, tags)
            except Exception:
                print(path)
                traceback.print_exc()


if __name__ == '__main__':
    embed_tags_into_photo()
