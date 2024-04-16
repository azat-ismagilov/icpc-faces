import easyocr

min_participant_matching_score = 20
min_team_matching_score = 50
body_to_face_ratio = 1


class Reader:
    __reader = None

    def readtext(image):
        if Reader.__reader == None:
            Reader.__reader = easyocr.Reader(['en'])
        return Reader.__reader.readtext(image,
                                 add_margin=0.2,
                                 text_threshold=0.6, paragraph=True,
                                 canvas_size=1280,
                                 y_ths=0.3, min_size=20)
