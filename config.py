import easyocr

csv_path = 'teams-2019.csv'
images_directory = 'photos'
output_directory = 'output'
group_photo_tag = b'event$Team Photos'
min_participant_matching_score = 70
min_team_matching_score = 60

reader = easyocr.Reader(['en'], gpu=False)
readtext = lambda x: reader.readtext(x, add_margin=0.2, text_threshold=0.6, canvas_size=4000, paragraph=True, y_ths=0.3)
