from flask import Blueprint, request, jsonify
from ..db_utils import execute_query
from ..services.config_tab import get_page_info 
from ..services.file_utils import list_files    
import os

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
