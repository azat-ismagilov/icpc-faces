import easyocr

min_participant_matching_score = 50
min_team_matching_score = 50
body_to_face_ratio = 1

reader = easyocr.Reader(['en'])


def readtext(image):
    return reader.readtext(image, add_margin=0.2,
                           text_threshold=0.6, paragraph=True,
                           y_ths=0.3, min_size=20)
