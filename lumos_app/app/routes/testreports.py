from flask import Blueprint, request, jsonify, send_file
from ..db_utils import execute_query
from ..services.config_tab import get_page_info 
from ..services.file_utils import list_files    
import os
import io
import zipfile

testreports_bp = Blueprint("reports", __name__)


# ---------------------------------------------------
# Reports List API
# ---------------------------------------------------
@testreports_bp.route('/api/reportslist', methods=['GET'])
def get_reportslist():

    rowid = request.args.get('rowid', '*')

    try:
        if rowid == '*':
            query = """
                SELECT lumos_user,
                       rowid,
                       exec_id,
                       releaseid,
                       env_name,
                       exec_status,
                       TO_CHAR(exec_date, 'YYYY-MM-DD HH24:MI:SS GMT') AS exec_date,
                       exec_time,
                       pass_count,
                       fail_count,
                       total_count
                FROM lumos.executions
                WHERE exec_status IN ('In-Progress', 'Completed')
                  AND exec_date >= NOW() - INTERVAL '6 months'
                ORDER BY exec_date DESC
            """
            rows = execute_query(query, fetch="all") or []

        else:
            query = """
                SELECT lumos_user,
                       rowid,
                       exec_id,
                       releaseid,
                       env_name,
                       exec_status,
                       TO_CHAR(exec_date, 'YYYY-MM-DD HH24:MI:SS GMT') AS exec_date,
                       exec_time,
                       pass_count,
                       fail_count,
                       total_count
                FROM lumos.executions
                WHERE exec_status IN ('In-Progress', 'Completed')
                  AND rowid = %s
            """
            rows = execute_query(query, (rowid,), fetch="all") or []

        result = [
            {
                "lumos_user": r[0],
                "rowid": r[1],
                "exec_id": r[2],
                "releaseid": r[3],
                "env_name": r[4],
                "exec_status": r[5],
                "exec_date": r[6],
                "exec_time": r[7],
                "pass_count": r[8],
                "fail_count": r[9],
                "total_count": r[10]
            }
            for r in rows
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------
# Execution Details / Logs / Reports
# ---------------------------------------------------
@testreports_bp.route('/api/execdetails', methods=['GET'])
def get_execdetails():

    rowid = request.args.get('rowid')
    pagename = request.args.get('pageName')

    if not rowid or not pagename:
        return jsonify({'error': 'Missing required parameters'}), 400

    try:
        if pagename == "ExecutionDetails":

            query = """
                SELECT exec_id,
                       TO_CHAR(exec_date, 'YYYY-MM-DD HH24:MI:SS GMT') AS exec_date,
                       testcasename,
                       status,
                       exec_time
                FROM lumos.exec_details
                WHERE exec_id = %s
                ORDER BY exec_date DESC
            """

            rows = execute_query(query, (rowid,), fetch="all") or []

            result = [
                {
                    "exec_id": r[0],
                    "exec_date": r[1],
                    "testcasename": r[2],
                    "status": r[3],
                    "exec_time": r[4]
                }
                for r in rows
            ]

            return jsonify(result), 200

        elif pagename in ["ExecutionLog", "ExecutionReports"]:

            page_info = get_page_info(pagename)

            if not page_info:
                return jsonify({'error': 'Invalid pageName'}), 400

            requested_path = os.path.join(page_info['path'], rowid)

            if not os.path.exists(requested_path):
                return jsonify({'error': 'Path not found'}), 404

            tree = list_files(requested_path)

            return jsonify(tree), 200

        else:
            return jsonify({'error': 'Invalid pageName'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------
# Download Execution Folder (ZIP)
# ---------------------------------------------------
@testreports_bp.route('/api/download_exec_folder', methods=['POST'])
def download_exec_folder():

    data = request.get_json(silent=True)

    rowid = data.get('rowid')
    pagename = data.get('pageName')  # ExecutionReports or ExecutionLog

    if not rowid or not pagename:
        return jsonify({"error": "Missing rowid or pageName"}), 400

    page_info = get_page_info(pagename)

    if not page_info:
        return jsonify({"error": "Invalid pageName"}), 400

    # Build safe absolute path
    folder_path = os.path.join(page_info['path'], rowid)
    abs_folder_path = os.path.abspath(folder_path)
    base_path = os.path.abspath(page_info['path'])

    # Security check (prevent path traversal)
    if not abs_folder_path.startswith(base_path):
        return jsonify({"error": "Access denied"}), 403

    if not os.path.isdir(abs_folder_path):
        return jsonify({"error": "Folder not found"}), 404

    # Set ZIP file name
    if pagename == "ExecutionReports":
        zip_filename = f"{rowid}.zip"
    elif pagename == "ExecutionLog":
        zip_filename = f"{rowid}_log.zip"
    else:
        return jsonify({"error": "Invalid pageName"}), 400

    try:
        # Create ZIP in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(abs_folder_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, abs_folder_path)
                    zipf.write(full_path, arcname=rel_path)

        zip_buffer.seek(0)

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=zip_filename
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
