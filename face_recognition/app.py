from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from src.database import DataBase, UpdateQueue
from src.utils import render_image
import uuid
import threading
import shutil
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['IMAGE_FOLDER'] = 'static'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['IMAGE_FOLDER'], exist_ok=True)
SESSION_BASE = os.path.join(app.config['IMAGE_FOLDER'], 'sessions')
os.makedirs(SESSION_BASE, exist_ok=True)

# Mock backend state
backend_state = {
    'step': 0,
    'finished': False,
    'main_img': None,
    'main_img_caption': '',
    'refs': [],
    'ref_captions': [],
    'state': {},
    'indices': [],
}

MAIN_QUEUE = None
QUEUE_LOCK = threading.Lock()
SESSIONS = {}  # sid -> {folder, timer, state, refs, ref_captions, indices, main_img, main_img_caption, finished}

# --- Session helpers ---

def _session_folder(sid: str) -> str:
    return os.path.join(SESSION_BASE, sid)


def _cleanup_folder(folder: str):
    if folder and os.path.isdir(folder):
        try:
            shutil.rmtree(folder)
        except Exception:
            pass


def _reset_session_timer(sid: str, seconds: int = 300):
    sess = SESSIONS.get(sid)
    if not sess:
        return
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
    try:
        # If user abandoned during grouping, return the entire batch
        if sess.get('mode') == 'group' and sess.get('group_batch'):
            with QUEUE_LOCK:
                for st in sess['group_batch']:
                    MAIN_QUEUE.undo(st)
        else:
            # Return the task to the queue if any
            state = sess.get('state')
            if state:
                with QUEUE_LOCK:
                    MAIN_QUEUE.undo(state)
    except Exception:
        pass
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
    main_face = render_image(batch[0], True, folder)
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
        sess.update({'finished': True})
        _reset_session_timer(sid)
        return sess

    if len(batch) > 1:
        # Stage 1: grouping UI
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
    data = _render_session_state(sid, batch[0], similar_faces, similar_faces_indices, similarities)
    data.update({'mode': 'choose'})
    sess.update(data)
    _reset_session_timer(sid)
    return data


def _clear_all_sessions():
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
    SESSIONS[sid] = {
        'folder': _session_folder(sid),
        'timer': None,
    }
    _get_next_for_session(sid)
    return sid

@app.route('/', methods=['GET', 'POST'])
def index():
    global MAIN_QUEUE, backend_state

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
            # Initialize backend state with uploaded images
            database = DataBase(path1)
            with QUEUE_LOCK:
                MAIN_QUEUE = UpdateQueue(database, path2)
            # Reset any active sessions and their timers/files
            _clear_all_sessions()
            # Do not prefetch a state here; users should go to /new
            return redirect(url_for('new_session'))
    return render_template('index.html')


@app.route('/new', methods=['GET'])
def new_session():
    if MAIN_QUEUE is None:
        return redirect(url_for('index'))
    sid = _create_session()
    return redirect(url_for('process_session', sid=sid))


@app.route('/process/<sid>', methods=['GET'])
def process_session(sid):
    sess = SESSIONS.get(sid)
    if not sess:
        return redirect(url_for('new_session'))

    # If session finished, try to pick up new work that might have been returned by other users' cancellations
    if sess.get('finished'):
        data = _get_next_for_session(sid)
        sess = SESSIONS.get(sid)
        if sess.get('finished'):
            return render_template('done.html')

    if sess.get('mode') == 'group':
        return render_template(
            'group.html',
            main_img=sess['group_main'],
            items=sess['group_items'],
            session_id=sid,
        )
    return render_template(
        'process.html',
        main_img=sess['main_img'],
        main_img_caption=sess['main_img_caption'],
        refs=sess['refs'],
        ref_captions=sess['ref_captions'],
        ref_names=sess['ref_names'],
        session_id=sid,
    )


@app.route('/choose/<sid>', methods=['POST'])
def choose(sid):
    sess = SESSIONS.get(sid)
    if not sess:
        return jsonify({'error': 'session_not_found'}), 404
    data = request.form
    choice_raw = data.get('choice')
    custom_name = data.get('custom_name')
    skip = data.get('skip')

    try:
        if skip == 'true':
            with QUEUE_LOCK:
                MAIN_QUEUE.undo(sess['state'])
        elif custom_name and custom_name.strip():
            custom_name_final = custom_name.strip()
            with QUEUE_LOCK:
                MAIN_QUEUE.update(sess['state'], name=custom_name_final)
        elif choice_raw and choice_raw.isdigit():
            choice = int(choice_raw) - 1
            with QUEUE_LOCK:
                MAIN_QUEUE.update(sess['state'], idx=sess['indices'][choice])
    finally:
        # After any action, fetch next state for this session (or mark finished)
        data_next = _get_next_for_session(sid)

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
        return jsonify({'error': 'session_not_found_or_not_grouping'}), 404

    # selected indices refer to positions in batch (1..len-1). First (0) is always included
    selected_raw = request.form.get('selected', '')  # e.g., "1,3,4"
    selected_set = set()
    for part in selected_raw.split(','):
        part = part.strip()
        if part.isdigit():
            i = int(part)
            if i >= 1 and i < len(sess['group_batch']):
                selected_set.add(i)

    batch = sess['group_batch']

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
        return jsonify({'error': 'session_not_found'}), 404
    return jsonify({'finished': sess.get('finished', False)})


if __name__ == '__main__':
    load_dotenv()  # Load environment variables from .env file if needed
    app.run(host='0.0.0.0', port=8081, debug=True)
