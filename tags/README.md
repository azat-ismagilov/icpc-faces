## Contents
1. [File structure](#file-structure)
2. [Requirements](#requirements)
3. [Installation](#installation)
4. [How to use](#how-to-use)
5. [Known issues](#known-issues)


## File structure: 
Your file structure should be organized in following way:
```
├── base_folder
│   ├── Photo_Tour
│   │   ├── John_Smith-1
│   │   │   ├── tag
│   │   │   │   ├── othertag
│   │   │   │   │   └── image1.jpg
│   │   │   │   └── differenttag
│   │   │   └── image2.jpg
│   │   ├── John_Smith-2
│   │   └── Azat_Ismagilov-1
│   └── Team_Photos
```

If you do so, `image1.jpg` with have tags: `album$2021, event$Photo Tour, photographer$John Smith, tag, othertag` and `image2.jpg` with have tags `album$2021, event$Photo Tour, photographer$John Smith`.

You can change `album$2021` tag as a parameter.

## Requirements
- python (3.4+)
- pip

## Installation
```bash
pip install -r requirements.txt
```

## How to use

1. Go to your base_folder
2. Copy methods.py and setup_all_tags.py to this folder.
3. Run `
python setup_all_tags.py Photo_Tour
`

### Granular control

You might want to have a lot more control with your tagging process. In that case I would recommend following approach.

1. Go to `base_folder`, and copy all python files from tags directory.

2. Run 
``` bash
python get_tags_from_paths.py Photo_Tour album$2021 tags.txt
```

This process will generate `tags.txt` file with all tags that will be imported into current files. You can manually change some entities inside.

4. After that you can run 
``` bash
python embed_tags_info_photos.py tags.txt
```
 to import those tags into your photos.

5. Import photos into digiKam, mark faces and export them with metadata.

6. Run 
``` bash
python convert_digiKam_to_picasa.py Photo_Tour face_tags.txt
```

This process will convert digiKam face tags to picasa format for you to upload. You can preview those in `face_tags.txt` file before you proceed.


7. After that you can run 
``` bash
python embed_tags_info_photos.py face_tags.txt
```
 to import face tags into your photos.

8. Upload photos to flikr.
