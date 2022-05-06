import easyocr

csv_path = 'teams2019.csv'
images_directory = 'photos'
output_directory = 'output'
group_photo_tag = b'event$Team Photos'

reader = easyocr.Reader(['en'], gpu=False)
readtext = lambda x: reader.readtext(x, add_margin=0.2, text_threshold=0.6, canvas_size=4000, paragraph=True, y_ths=0.3)
