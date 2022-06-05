import easyocr

csv_path = 'teams-2019.csv'
group_images_directory = 'group_photos'
group_output_directory = 'output_group'
regular_images_directory = 'regular_photos'
regular_output_directory = 'output_regular'

min_participant_matching_score = 50
min_team_matching_score = 80
body_to_face_ratio = 2

reader = easyocr.Reader(['en'])
def readtext(image): return reader.readtext(image, add_margin=0.2,
                                            text_threshold=0.6, paragraph=True, y_ths=0.3)
