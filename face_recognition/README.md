## Contents
1. [Requirements](#requirements)
2. [Preparation](#preparation)
3. [Processing new embeddings](#processing-new-embeddings)
4. [Merging new embeddings into an existing database](#merging-new-embeddings-into-an-existing-database)

## Requirements
- python (3.4+)
- pip
- cmake
- CUDA (if you want to use GPU)

## Preparation

1. Install all dependencies

```bash
pip install -r requirements.txt
```

2. Set your API keys in the `.env` file.

```
FLICKR_API_KEY=...
FLICKR_API_SECRET=...
```

## Processing new embeddings

1. We recommend using Google Colab to get embeddings from photos.

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1VNzQ7px_ATv_37x8_f8QJf2P1t_INTsa?usp=sharing)

2. Run the following command. Specify `user_id` (from Flickr) and `tags` (to select photos to process).

```bash
python get_flickr_embeddings.py [-h] -user_id -tags [-output_file] [-raw_embeddings]
```

Using the `-raw_embeddings` option, you can extract all bounding boxes from photos, even without names.

## Merging new embeddings into an existing database

Use the `raw_embeddings` file from the previous step to merge it into an existing database. Start the web app to review and confirm face similarities:

```bash
python app.py [-h]
```

Available flags for `app.py`:

- `--host` — Host interface to bind (env: `APP_HOST`, default: `0.0.0.0`).
- `--port` — Port to listen on (env: `APP_PORT`, default: `8081`).
- `--session-timeout-seconds` — Seconds of inactivity before a session is auto-cancelled (env: `SESSION_TIMEOUT_SECONDS`, default: `300`).
- `--candidates-to-show` — Number of candidate faces displayed on the right panel (1–9). Values above 9 are capped by the UI (env: `CANDIDATES_TO_SHOW`, default: `5`).
- `--upload-folder` — Directory for uploaded files (env: `UPLOAD_FOLDER`, default: `static/uploads`).
- `--image-folder` — Base directory for static files; session folders are created under `<image-folder>/sessions` (env: `IMAGE_FOLDER`, default: `static`).

You can also configure the app via environment variables or a `.env` file (loaded automatically). Command-line flags override environment variables.

Example:

```bash
python app.py \
  --host 0.0.0.0 \
  --port 8081 \
  --session-timeout-seconds 300 \
  --candidates-to-show 5
```

Multi-user access:

- Open `http://<host>:<port>/` to upload the database and embeddings.
- Share `http://<host>:<port>/new` with annotators to start independent sessions. Sessions are automatically cancelled after the configured inactivity timeout.
