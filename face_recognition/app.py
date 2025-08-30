from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
import os
import argparse
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging

from src.database import DataBase, UpdateQueue
from src.utils import render_image
import uuid
import threading
import shutil
from datetime import datetime, timedelta

app = Flask(__name__)
# Configuration will be initialized in __main__ after parsing env/CLI
# Remove global config constants and directory creation from here.

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

MAIN_QUEUE = None
QUEUE_LOCK = threading.Lock()
SESSIONS = {}  # sid -> {folder, timer, state, refs, ref_captions, indices, main_img, main_img_caption, finished}

# --- Session helpers ---

def _session_folder(sid: str) -> str:
    return os.path.join(app.config['SESSION_BASE'], sid)


def _cleanup_folder(folder: str):
    if folder and os.path.isdir(folder):
        try:
            shutil.rmtree(folder)
        except Exception:
            pass


def _reset_session_timer(sid: str, seconds: int = None):
    sess = SESSIONS.get(sid)
    if not sess:
        return
    if seconds is None:
        seconds = app.config['SESSION_TIMEOUT_SECONDS']
    # cancel old
    t = sess.get('timer')
    if t:
        try:
            t.cancel()
        except Exception:
            pass
    # create new
    timer = threading.Timer(seconds, _cancel_session, args=(sid,))
    timer.daemon = True
    sess['timer'] = timer
    timer.start()


def _cancel_session(sid: str):
    sess = SESSIONS.pop(sid, None)
    if not sess:
        return
    
    logger.info(f"[SESSION_TIMEOUT] sid={sid} mode={sess.get('mode', 'unknown')} auto-cancelled due to inactivity")
    
    try:
        # If user abandoned during grouping, return the entire batch
        if sess.get('mode') == 'group' and sess.get('group_batch'):
            batch_count = len(sess.get('group_batch', []))
            logger.info(f"[SESSION_TIMEOUT] sid={sid} returning {batch_count} items from abandoned group to queue")
            with QUEUE_LOCK:
                for st in sess['group_batch']:
                    MAIN_QUEUE.undo(st)
        else:
            # Return the task to the queue if any
            state = sess.get('state')
            if state:
                logger.info(f"[SESSION_TIMEOUT] sid={sid} returning 1 item from abandoned choice to queue")
                with QUEUE_LOCK:
                    MAIN_QUEUE.undo(state)
    except Exception as e:
        logger.error(f"[SESSION_TIMEOUT] sid={sid} error returning items to queue: {e}")
    _cleanup_folder(sess.get('folder'))


def _render_session_state(sid: str, state, similar_faces, similar_indices, similarities):
    folder = _session_folder(sid)
    os.makedirs(folder, exist_ok=True)
    # Clear only this session's files
    try:
        for img in Path(folder).iterdir():
            if img.is_file():
                img.unlink()
    except Exception:
        pass
    refs = [render_image(ref, True, folder) for ref in similar_faces]
    ref_names = [ref['name'] for ref in similar_faces]
    ref_captions = [ref['name'] + f' (Similarity: {(2 - similarities[i]) / 2:.2f})' for i, ref in enumerate(similar_faces)]
    main_img = render_image(state, False, folder)
    main_img_caption = state.get('name', '')
    finished = True if state == {} else False
    return {
        'state': state,
        'refs': refs,
        'ref_names': ref_names,
        'ref_captions': ref_captions,
        'main_img': main_img,
        'main_img_caption': main_img_caption,
        'indices': similar_indices,
        'finished': finished,
        'folder': folder,
    }


def _render_group_state(sid: str, batch):
    folder = _session_folder(sid)
    os.makedirs(folder, exist_ok=True)
    # Clear only this session's files
    try:
        for img in Path(folder).iterdir():
            if img.is_file():
                img.unlink()
    except Exception:
        pass
    # First item is the reference
    main_face = render_image(batch[0], False, folder)
    items = []
    for i in range(1, len(batch)):
        items.append({
            'idx': i,
            'img': render_image(batch[i], True, folder),
        })
    return main_face, items


def _get_next_for_session(sid: str):
    with QUEUE_LOCK:
        batch, similar_faces, similar_faces_indices, similarities = MAIN_QUEUE.get()
    sess = SESSIONS[sid]
    if not batch:
        # finished
        logger.info(f"[QUEUE_EMPTY] sid={sid} no more items in queue, session finished")
        sess.update({'finished': True})
        _reset_session_timer(sid)
        return sess

    if len(batch) > 1:
        # Stage 1: grouping UI
        logger.info(f"[STAGE_GROUP] sid={sid} showing group of {len(batch)} similar faces for review")
        main_face, items = _render_group_state(sid, batch)
        sess.update({
            'mode': 'group',
            'group_batch': batch,
            'group_main': main_face,
            'group_items': items,
            'finished': False,
        })
        _reset_session_timer(sid)
        return sess

    # Stage 2: normal choice UI for a single item
    logger.info(f"[STAGE_CHOICE] sid={sid} showing single face with {len(similar_faces)} candidates")
    data = _render_session_state(sid, batch[0], similar_faces, similar_faces_indices, similarities)
    data.update({'mode': 'choose'})
    sess.update(data)
    _reset_session_timer(sid)
    return data


def _clear_all_sessions():
    session_count = len(SESSIONS)
    logger.info(f"[CLEAR_SESSIONS] clearing {session_count} active sessions due to new upload")
    
    for sid, sess in list(SESSIONS.items()):
        try:
            if sess.get('timer'):
                sess['timer'].cancel()
        except Exception:
            pass
        try:
            if sess.get('state'):
                with QUEUE_LOCK:
                    MAIN_QUEUE.undo(sess['state'])
        except Exception:
            pass
        _cleanup_folder(sess.get('folder'))
        SESSIONS.pop(sid, None)


def _create_session() -> str:
    sid = uuid.uuid4().hex
    logger.info(f"[SESSION_CREATE] new session created: {sid}")
    SESSIONS[sid] = {
        'folder': _session_folder(sid),
        'timer': None,
    }
    _get_next_for_session(sid)
    return sid

@app.route('/', methods=['GET', 'POST'])
def index():
    global MAIN_QUEUE

    if request.method == 'POST':
        file1 = request.files.get('file1')
        file2 = request.files.get('file2')

        if file1 and file2:
            filename1 = secure_filename(file1.filename)
            filename2 = secure_filename(file2.filename)
            path1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
            path2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
            file1.save(path1)
            file2.save(path2)
            
            logger.info(f"[UPLOAD] database={filename1} embeddings={filename2}")
            
            # Initialize backend state with uploaded images
            database = DataBase(path1)
            with QUEUE_LOCK:
                MAIN_QUEUE = UpdateQueue(database, path2, num_faces_show=app.config['CANDIDATES_TO_SHOW'], num_candidates_merge=app.config['CANDIDATES_TO_MERGE'])
            
            logger.info(f"[QUEUE_INIT] database_size={len(database)} queue_size={len(MAIN_QUEUE.queue)} candidates_to_show={app.config['CANDIDATES_TO_SHOW']}")
            
            # Reset any active sessions and their timers/files
            _clear_all_sessions()
            # Do not prefetch a state here; users should go to /new
            return redirect(url_for('new_session'))
    return render_template('index.html')


@app.route('/new', methods=['GET'])
def new_session():
    if MAIN_QUEUE is None:
        logger.warning("[SESSION_NEW] attempt to create session without queue, redirecting to upload")
        return redirect(url_for('index'))
    sid = _create_session()
    logger.info(f"[SESSION_NEW] created session {sid}, redirecting to process")
    return redirect(url_for('process_session', sid=sid))


@app.route('/process/<sid>', methods=['GET'])
def process_session(sid):
    sess = SESSIONS.get(sid)
    if not sess:
        logger.warning(f"[SESSION_MISSING] sid={sid} not found, redirecting to new session")
        return redirect(url_for('new_session'))

    # If session finished, try to pick up new work that might have been returned by other users' cancellations
    if sess.get('finished'):
        logger.info(f"[SESSION_REFRESH] sid={sid} checking for new work after completion")
        data = _get_next_for_session(sid)
        sess = SESSIONS.get(sid)
        if sess.get('finished'):
            logger.info(f"[SESSION_DONE] sid={sid} no more work available, showing done page")
            return render_template('done.html')

    if sess.get('mode') == 'group':
        logger.info(f"[PAGE_GROUP] sid={sid} showing group page with {len(sess.get('group_items', []))} candidates")
        return render_template(
            'group.html',
            main_img=sess['group_main'],
            items=sess['group_items'],
            session_id=sid,
        )
    
    logger.info(f"[PAGE_CHOICE] sid={sid} showing choice page with {len(sess.get('refs', []))} candidates")
    return render_template(
        'process.html',
        main_img=sess['main_img'],
        main_img_caption=sess['main_img_caption'],
        refs=sess['refs'],
        ref_captions=sess['ref_captions'],
        ref_names=sess['ref_names'],
        session_id=sid,
        max_candidates=app.config['CANDIDATES_TO_SHOW'],
        keyboard_max=min(9, app.config['CANDIDATES_TO_SHOW']),
    )


@app.route('/choose/<sid>', methods=['POST'])
def choose(sid):
    sess = SESSIONS.get(sid)
    if not sess:
        logger.warning(f"[CHOICE_ERROR] sid={sid} session not found")
        return jsonify({'error': 'session_not_found'}), 404
    
    data = request.form
    choice_raw = data.get('choice')
    custom_name = data.get('custom_name')
    skip = data.get('skip')

    logger.info(f"[CHOICE_REQUEST] sid={sid} choice={choice_raw} custom_name='{custom_name}' skip={skip}")

    action_applied = False
    try:
        if skip == 'true':
            logger.info(f"[CHOICE_SKIP] sid={sid} skipping current face")
            with QUEUE_LOCK:
                MAIN_QUEUE.undo(sess['state'])
            action_applied = True
        elif custom_name and custom_name.strip():
            custom_name_final = custom_name.strip()
            logger.info(f"[CHOICE_CUSTOM] sid={sid} assigning custom name: '{custom_name_final}'")
            with QUEUE_LOCK:
                MAIN_QUEUE.update(sess['state'], name=custom_name_final)
            action_applied = True
        elif choice_raw and choice_raw.isdigit():
            choice = int(choice_raw) - 1
            if 0 <= choice < len(sess.get('indices', [])):
                selected_name = sess.get('ref_names', [])[choice] if choice < len(sess.get('ref_names', [])) else 'unknown'
                logger.info(f"[CHOICE_SELECT] sid={sid} selected candidate #{choice+1} (name: '{selected_name}')")
                with QUEUE_LOCK:
                    MAIN_QUEUE.update(sess['state'], idx=sess['indices'][choice])
                action_applied = True
            else:
                logger.warning(f"[CHOICE_INVALID] sid={sid} choice {choice+1} out of range (max: {len(sess.get('indices', []))})")
    finally:
        # After any action, fetch next state for this session (or keep current if no-op)
        if action_applied:
            data_next = _get_next_for_session(sid)
        else:
            data_next = sess

    return jsonify({
        'done': data_next.get('finished', False),
        'main_img': data_next.get('main_img'),
        'main_img_caption': data_next.get('main_img_caption'),
        'refs': data_next.get('refs'),
        'ref_captions': data_next.get('ref_captions'),
    })


@app.route('/group/<sid>', methods=['POST'])
def apply_group(sid):
    sess = SESSIONS.get(sid)
    if not sess or 'group_batch' not in sess:
        logger.warning(f"[GROUP_ERROR] sid={sid} session not found or not in group mode")
        return jsonify({'error': 'session_not_found_or_not_grouping'}), 404

    action = request.form.get('action', '')
    selected_raw = request.form.get('selected', '')
    
    logger.info(f"[GROUP_REQUEST] sid={sid} action='{action}' selected='{selected_raw}' batch_size={len(sess.get('group_batch', []))}")
    
    # Handle skip action
    if action == 'skip':
        batch = sess['group_batch']
        logger.info(f"[GROUP_SKIP] sid={sid} skipping entire group of {len(batch)} faces")
        with QUEUE_LOCK:
            for st in batch:
                MAIN_QUEUE.undo(st)
        # Get next work
        data_next = _get_next_for_session(sid)
        return jsonify({
            'ok': True,
            'redirect': url_for('process_session', sid=sid)
        })
    
    # Handle delete action (delete first face, return rest to queue)
    if action == 'delete':
        batch = sess['group_batch']
        logger.info(f"[GROUP_DELETE] sid={sid} deleting reference face, returning {len(batch)-1} faces to queue")
        # Return all except the first (reference) face to queue
        if len(batch) > 1:
            with QUEUE_LOCK:
                for st in batch[1:]:
                    MAIN_QUEUE.undo(st)
        # First face is deleted (not returned to queue)
        # Get next work
        data_next = _get_next_for_session(sid)
        return jsonify({
            'ok': True,
            'redirect': url_for('process_session', sid=sid)
        })

    # Original merge logic
    selected_set = set()
    for part in selected_raw.split(','):
        part = part.strip()
        if part.isdigit():
            i = int(part)
            if i >= 1 and i < len(sess['group_batch']):
                selected_set.add(i)

    batch = sess['group_batch']
    
    logger.info(f"[GROUP_MERGE] sid={sid} merging {1 + len(selected_set)} faces (reference + {len(selected_set)} selected), returning {len(batch) - 1 - len(selected_set)} to queue")

    # Undo all unselected (excluding first item at index 0)
    to_undo = [batch[i] for i in range(1, len(batch)) if i not in selected_set]
    if to_undo:
        with QUEUE_LOCK:
            for st in to_undo:
                MAIN_QUEUE.undo(st)

    # Selected states include the first item + all chosen
    selected_states = [batch[0]] + [batch[i] for i in sorted(selected_set)]
    # Merge selected states into one (user to implement actual logic)
    merged_state = MAIN_QUEUE.combine_group(selected_states)

    # Compute similar faces for merged state
    with QUEUE_LOCK:
        similar_faces, similar_indices, similarities = MAIN_QUEUE.compute_similar(merged_state)

    logger.info(f"[GROUP_MERGED] sid={sid} created merged face, proceeding to choice stage with {len(similar_faces)} candidates")

    # Render normal choice UI
    data = _render_session_state(sid, merged_state, similar_faces, similar_indices, similarities)
    data.update({'mode': 'choose'})
    sess.update(data)
    _reset_session_timer(sid)

    return jsonify({
        'ok': True,
        'redirect': url_for('process_session', sid=sid)
    })


@app.route('/status/<sid>', methods=['GET'])
def status(sid):
    sess = SESSIONS.get(sid)
    if not sess:
        logger.warning(f"[STATUS_ERROR] sid={sid} session not found")
        return jsonify({'error': 'session_not_found'}), 404
    
    status_info = {
        'finished': sess.get('finished', False),
        'mode': sess.get('mode', 'unknown'),
        'session_id': sid
    }
    logger.debug(f"[STATUS_CHECK] sid={sid} status={status_info}")
    return jsonify(status_info)


if __name__ == '__main__':
    load_dotenv()  # Load environment variables from .env file if needed

    parser = argparse.ArgumentParser(
        description='Run face recognition web app',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    # Defaults from env
    env_host = os.getenv('APP_HOST', '0.0.0.0')
    env_port = int(os.getenv('APP_PORT', '8081'))
    env_timeout = int(os.getenv('SESSION_TIMEOUT_SECONDS', '300'))
    env_candidates = int(os.getenv('CANDIDATES_TO_SHOW', '5'))
    env_candidates_merge = int(os.getenv('CANDIDATES_TO_MERGE', '10'))

    parser.add_argument('--host', type=str, default=env_host, help='Server host')
    parser.add_argument('--port', type=int, default=env_port, help='Server port')
    parser.add_argument('--session-timeout-seconds', type=int, default=env_timeout, help='Seconds of inactivity before session is canceled')
    parser.add_argument('--candidates-to-show', type=int, default=env_candidates, help='Number of candidates shown on the right panel')
    parser.add_argument('--candidates-to-merge', type=int, default=env_candidates_merge, help='Number of candidates shown to merge')
    parser.add_argument('--upload-folder', type=str, default=os.getenv('UPLOAD_FOLDER', 'static/uploads'), help='Path to uploads folder')
    parser.add_argument('--image-folder', type=str, default=os.getenv('IMAGE_FOLDER', 'static'), help='Path to images folder')
    args = parser.parse_args()

    # Apply config
    app.config.update({
        'APP_HOST': args.host,
        'APP_PORT': args.port,
        'SESSION_TIMEOUT_SECONDS': args.session_timeout_seconds,
        'CANDIDATES_TO_SHOW': args.candidates_to_show,
        'CANDIDATES_TO_MERGE': args.candidates_to_merge,
        'UPLOAD_FOLDER': args.upload_folder,
        'IMAGE_FOLDER': args.image_folder,
    })
    # Derived paths and ensure directories exist
    app.config['SESSION_BASE'] = os.path.join(app.config['IMAGE_FOLDER'], 'sessions')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['IMAGE_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SESSION_BASE'], exist_ok=True)

    logger.info(f"[APP_START] Starting app on {args.host}:{args.port}")
    logger.info(f"[CONFIG] timeout={args.session_timeout_seconds}s candidates_show={args.candidates_to_show} candidates_merge={args.candidates_to_merge}")

    app.run(host=app.config['APP_HOST'], port=app.config['APP_PORT'], debug=True)
