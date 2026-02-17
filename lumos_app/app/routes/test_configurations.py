from flask import current_app, Blueprint, render_template, request, jsonify
from .config_tab import get_page_info
from werkzeug.utils import secure_filename
import os

configurations_bp = Blueprint("configurations", __name__)

ALLOWED_EXTENSIONS = {"txt", "json", "yaml", "yml", "conf"}


# --------------------
# Utility: Safe Path Validation
# --------------------

def validate_safe_path(path):
    BASE_DIR = current_app.config["BASE_DIR"]
    abs_path = os.path.abspath(path)

    if os.path.commonpath([abs_path, BASE_DIR]) != BASE_DIR:
        raise PermissionError("Access denied")

    return abs_path


# --------------------
# Template Routes
# --------------------

@configurations_bp.route('/')
def index():
    return render_template('index.html')


@configurations_bp.route('/edit')
def edit():
    return render_template('edit.html')


@configurations_bp.route('/view')
def view():
    return render_template('view.html')


# --------------------
# API: Get File List
# --------------------

@configurations_bp.route('/api/filelist', methods=['GET'])
def get_files():
    pagename = request.args.get('pageName')

    if not pagename:
        return jsonify({'error': 'pageName is required'}), 400

    page_info = get_page_info(pagename)

    if not page_info:
        return jsonify({'error': 'Invalid pageName'}), 404

    try:
        safe_path = validate_safe_path(page_info['path'])

        # Make sure list_files is properly imported
        tree = list_files(safe_path)

        return jsonify(tree), 200

    except PermissionError:
        return jsonify({'error': 'Access denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --------------------
# API: Get File Content
# --------------------

@configurations_bp.route('/api/getfilecontent', methods=['GET'])
def get_file_content():

    file_path = request.args.get('file_path')

    if not file_path:
        return jsonify({'error': 'file_path is required'}), 400

    try:
        abs_path = validate_safe_path(file_path)

        if not os.path.exists(abs_path):
            return jsonify({'error': 'File not found'}), 404

        with open(abs_path, 'r') as file:
            content = file.read()

        return jsonify({
            'file_path': abs_path,
            'content': content
        }), 200

    except PermissionError:
        return jsonify({'error': 'Access denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --------------------
# API: Save File Content
# --------------------

@configurations_bp.route('/api/savefilecontent', methods=['PUT'])
def save_file_content():

    file_path = request.args.get('file_path')

    if not file_path:
        return jsonify({'error': 'file_path is required'}), 400

    try:
        abs_path = validate_safe_path(file_path)

        if not os.path.exists(abs_path):
            return jsonify({'error': 'File not found'}), 404

        data = request.get_json(silent=True)

        if not data or 'content' not in data:
            return jsonify({'error': 'content is required'}), 400

        content = data['content']

        with open(abs_path, 'w') as file:
            file.write(content)

        return jsonify({'message': 'File saved successfully!'}), 200

    except PermissionError:
        return jsonify({'error': 'Access denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --------------------
# API: Upload File
# --------------------

@configurations_bp.route('/api/uploadfile', methods=['POST'])
def upload_file():

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in request'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)

    if '.' not in filename:
        return jsonify({'error': 'Invalid file format'}), 400

    ext = filename.rsplit('.', 1)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({'error': 'File type not allowed'}), 400

    pagename = request.form.get('pageName')

    if not pagename:
        return jsonify({'error': 'pageName is required'}), 400

    page_info = get_page_info(pagename)

    if not page_info:
        return jsonify({'error': 'Invalid pageName'}), 404

    try:
        safe_folder = validate_safe_path(page_info['path'])

        os.makedirs(safe_folder, exist_ok=True)

        file_path = os.path.join(safe_folder, filename)

        file.save(file_path)

        return jsonify({
            'message': 'File uploaded successfully!',
            'file_path': file_path
        }), 201

    except PermissionError:
        return jsonify({'error': 'Access denied'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
