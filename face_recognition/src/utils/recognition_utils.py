def intersect(rect1, rect2):
    # Координаты первого прямоугольника
    x1_1, y1_1, x2_1, y2_1 = rect1
    # Координаты второго прямоугольника
    x1_2, y1_2, x2_2, y2_2 = rect2

    # Координаты пересечения
    x1 = max(x1_1, x1_2)
    y1 = max(y1_1, y1_2)
    x2 = min(x2_1, x2_2)
    y2 = min(y2_1, y2_2)

    # Проверка, существует ли пересечение
    if x1 < x2 and y1 < y2:
        return (x1, y1, x2, y2)
    else:
        return None
    

def area(rect):
    x1, y1, x2, y2 = rect
    return abs(x2 - x1) * abs(y2 - y1)


def match_boxes(bb_flickr: list, bb_recognition: list) -> list:
    """
    Match bounding boxes from flickr and recognition

    Parameters
    ----------
    bb_flickr : list
        List of bounding boxes from flickr
    bb_recognition : list
        List of bounding boxes from recognition

    Returns
    -------
    dict
        Dictionary with the matching bounding boxes
    """

    matches = []

    for box_recognition in bb_recognition:
        for box_flickr in bb_flickr:
            intersection = intersect(box_flickr, box_recognition)
            if not intersection:
                continue
            if area(intersection) / min(area(box_flickr), area(box_recognition)) > 0.7:
                box_recognition.person.name = box_flickr.person.name
                matches.append(box_recognition)
                break

    return matches
