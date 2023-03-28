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

You can change `album$2021` tag in code, file `methods.py`.

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
