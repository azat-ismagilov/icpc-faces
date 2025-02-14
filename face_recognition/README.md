## Contents
1. [Requirements](#requirements)
2. [Installation](#installation)
3. [How to use](#how-to-use)
4. [Known issues](#known-issues)

## Requirements
- python (3.4+)
- pip
- cmake
- CUDA (if you want to use GPU)

## Colab

We recommend using Google Colab to get embeddings from photos.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1VNzQ7px_ATv_37x8_f8QJf2P1t_INTsa?usp=sharing)

## Installation
```bash
pip install -r requirements.txt
```

## How to use:

1. Set your api keys in `.env` file.

```
FLICKR_API_KEY=...
FLICKR_API_SECRET=...
```

2. Run following command. Specify user_id(from flickr) and tags(to specify photos to get embeddings from).

```bash
python get_flickr_embeddings.py [-h] -user_id -tags [-output_file] [-raw_embeddings]
```

Using -raw_embeddings option, you can get all bounding boxes from photos, even without names.
