import csv
import argparse
import subprocess, os, platform

from team import parse_teams_from_csv
import re
from PIL import Image, ImageDraw, ImageFont


def main():
    parser = argparse.ArgumentParser(
        description="Generate faces info in picasa format from images with badges",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "teams_csv", type=str, help="a csv file containing the team and name columns"
    )
    parser.add_argument(
        "tags_file", type=str, help="tags file", default="tags.txt", nargs="?"
    )
    parser.add_argument("--filter", type=str, help="regex to filter image paths")
    parser.add_argument(
        "--force", type=bool, help="force to recalculate images info", default=False
    )
    parser.add_argument(
        "--delimiter",
        dest="delimiter",
        metavar="D",
        type=str,
        help="delimiter for teams file",
        default=";",
    )
    args = parser.parse_args()
    teams = parse_teams_from_csv(args.teams_csv, args.delimiter)
    images = []
    with open(args.tags_file, "r", encoding="utf-8") as f:
        reader = csv.reader(
            f, delimiter="\t", quotechar='"', lineterminator="\n", quoting=csv.QUOTE_ALL
        )
        for image in reader:
            images.append(image)

    output_images = []
    for image in images:
        path = image[0]
        if args.filter and not re.match(args.filter, path):
            continue
        tags = image[1:]
        new_tags = []
        team = None
        people = []
        for tag in tags:
            if tag.startswith("team$"):
                teamName = tag[5:]
                for possibleTeam in teams:
                    if possibleTeam.name == teamName:
                        team = possibleTeam
            if re.match(r".*\([0-9a-f]{16}\)", tag):
                name, rest = tag.split("(", 1)
                people.append((name, rest[0:-1]))
            else:
                new_tags.append(tag)
        if team == None:
            output_images.append(image)
            continue
        if args.force:
            people = [("", x[1]) for x in people]
        possible_people = set([x.name for x in team.participants])
        for name, _ in people:
            if name in possible_people:
                possible_people.remove(name)
        for name, picasa_format in people:
            if name == "":
                if len(possible_people) == 0:
                    name = ""
                elif len(possible_people) == 1:
                    name = possible_people.pop()
                else:
                    print("Let's try to figure out, who is this person")
                    print(path)
                    options = {}
                    for i, possible_person in enumerate(possible_people):
                        print(f"[{i}] {possible_person}")
                        options[str(i)] = possible_person
                    print("[?] delete")
                    input("Press enter to see the image")
                    image = Image.open(path)
                    if image is None or image.size == 0:
                        return

                    draw = ImageDraw.Draw(image)
                    normal = ImageFont.truetype("arial.ttf", 100)

                    width, height = image.size

                    left, top, right, bottom = [
                        int(picasa_format[i : i + 4], 16) / 65535
                        for i in range(0, len(picasa_format), 4)
                    ]

                    print(left, top, right, bottom)
                    # right = left + right
                    # bottom = top + bottom
                    left = left * width
                    right = right * width
                    top = top * height
                    bottom = bottom * height

                    draw.rectangle(
                        (left, top, right, bottom),
                        outline="green",
                        width=5,
                    )
                    draw.text(
                        (0, 0),
                        str(options),
                        font=normal,
                        fill="white",
                        stroke_width=5,
                        stroke_fill="black",
                    )
                    imgpath = "temp.jpg"
                    image.save(imgpath)
                    if platform.system() == "Darwin":  # macOS
                        subprocess.call(("open", imgpath))
                    elif platform.system() == "Windows":  # Windows
                        os.startfile(imgpath)
                    else:  # linux variants
                        subprocess.call(("xdg-open", imgpath))
                    choice = input("Enter a number to select the person")
                    if choice == "?":
                        continue
                    name = options[choice]
                    possible_people.remove(name)
            new_tags.append(f"{name}({picasa_format})")

    with open(args.tags_file, "w", encoding="utf-8") as f:
        writer = csv.writer(
            f, delimiter="\t", quotechar='"', lineterminator="\n", quoting=csv.QUOTE_ALL
        )
        for image in images:
            writer.writerow(image)


if __name__ == "__main__":
    main()
