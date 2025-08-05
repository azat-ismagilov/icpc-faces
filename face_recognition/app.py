from pathlib import Path
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from src.database import DataBase, UpdateQueue
from src.utils import render_image

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['IMAGE_FOLDER'] = 'static'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['IMAGE_FOLDER'], exist_ok=True)

# Mock backend state
backend_state = {
    'step': 0,
    'finished': False,
    'main_img': None,
    'refs': [],
    'ref_captions': [],
    'state': {},
    'indices': [],
}

MAIN_QUEUE = None

def update_state():
    global backend_state, MAIN_QUEUE

    for img in Path(app.config['IMAGE_FOLDER']).iterdir():
        if img.is_file() and img.suffix in ['.jpg', '.jpeg', '.png']:
            os.remove(img)

    state, similar_faces, similar_faces_indices = MAIN_QUEUE.get()
    backend_state['step'] += 1
    backend_state['state'] = state
    backend_state['refs'] = [render_image(ref, True, app.config['IMAGE_FOLDER']) for ref in similar_faces]
    backend_state['ref_captions'] = [ref['name'] for ref in similar_faces]
    backend_state['main_img'] = render_image(state, False, app.config['IMAGE_FOLDER'])
    backend_state['indices'] = similar_faces_indices
    backend_state['finished'] = True if state == {} else False


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
            MAIN_QUEUE = UpdateQueue(database, path2)
            # Reset backend state
            backend_state['step'] = 0
            update_state()

            return redirect(url_for('process'))
    return render_template('index.html')

@app.route('/process', methods=['GET'])
def process():
    if backend_state['finished']:
        return render_template('done.html')
    return render_template('process.html', 
                         main_img=backend_state['main_img'], 
                         refs=backend_state['refs'],
                         ref_captions=backend_state['ref_captions'])

@app.route('/choose', methods=['POST'])
def choose():
    data = request.form
    choice_raw = data.get('choice')
    custom_name = data.get('custom_name')
    skip = data.get('skip')
    
    if skip == 'true':
        MAIN_QUEUE.undo(backend_state['state'])
    elif custom_name and custom_name.strip():
        custom_name_final = custom_name.strip()
        MAIN_QUEUE.update(backend_state['state'], name=custom_name_final)
    elif choice_raw and choice_raw.isdigit():
        choice = int(choice_raw) - 1
        MAIN_QUEUE.update(backend_state['state'], idx=backend_state['indices'][choice])
    
    
    update_state()
    return jsonify({'done': False, 'main_img': backend_state['main_img'], 'refs': backend_state['refs'], 'ref_captions': backend_state['ref_captions']})

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'finished': backend_state['finished']})

if __name__ == '__main__':
    load_dotenv()  # Load environment variables from .env file if needed
    app.run(host='0.0.0.0', port=8081, debug=True)
