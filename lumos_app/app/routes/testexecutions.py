from flask import Blueprint, request, jsonify
from datetime import datetime
from ..db_utils import execute_query
from ..services.activitylog import log_activity
from ..services.processsubmit import processsubmittedrecords
from ..services.stop_containers import stop_containers_by_execution_id

testexecutions_bp = Blueprint("executions", __name__)


# ---------------------------------------------------
# 1️⃣ Get Executions List
# ---------------------------------------------------
@testexecutions_bp.route('/api/executionslist', methods=['GET'])
def get_executionslist():
    try:
        query = """
            SELECT lumos_user,
                   rowid,
                   exec_id,
                   releaseid,
                   TO_CHAR(exec_date, 'YYYY-MM-DD HH24:MI:SS GMT') AS exec_date,
                   TO_CHAR(scheduled_dt, 'YYYY-MM-DD HH24:MI:SS GMT') AS scheduled_dt,
                   env_name,
                   exec_status,
                   exec_test_list
            FROM lumos.executions
            WHERE exec_status != ''
              AND exec_date >= NOW() - INTERVAL '6 months'
            ORDER BY exec_date DESC
        """

        rows = execute_query(query, fetch="all") or []

        result = [
            {
                "lumos_user": r[0],
                "rowid": r[1],
                "exec_id": r[2],
                "releaseid": r[3],
                "exec_date": r[4],
                "scheduled_dt": r[5],
                "env_name": r[6],
                "exec_status": r[7],
                "exec_test_list": r[8],
            }
            for r in rows
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------
# 2️⃣ Populate Testcases & Testpacks
# ---------------------------------------------------
@testexecutions_bp.route('/api/new_execution', methods=['GET'])
def new_execution():
    try:
        query = """
            SELECT testcasename AS name, 'Testcase' AS type
            FROM lumos.testcase_list
            WHERE inactiveflag = 'N'

            UNION

            SELECT testpack_name AS name, 'Testpack' AS type
            FROM lumos.testpack_list
            WHERE inactiveflag = 'N'
        """

        rows = execute_query(query, fetch="all") or []

        result = [
            {"name": r[0], "type": r[1]}
            for r in rows
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------
# 3️⃣ Save Execution
# ---------------------------------------------------
@testexecutions_bp.route('/api/save_execution', methods=['POST'])
def save_execution():

    data = request.get_json(silent=True)

    releaseid = data.get('releaseId')
    executionname = data.get('executionName')
    screencapture = data.get('screenCapture')
    env_name = data.get('env_name')
    browser = data.get('browser')
    scheduled_dt = data.get('scheduled_dt')
    frequency = data.get('frequency')
    testlist = data.get('testlist', [])
    username = data.get('userName', '').strip()

    if not executionname or not releaseid or not username:
        return jsonify({'error': 'Missing required fields'}), 400

    if not testlist:
        return jsonify({'error': 'Select at least one Testcase/Testpack'}), 400

    rowid = datetime.now().strftime('%Y%m%d%H%M%S')
    total_testlist = ",".join(testlist)

    try:
        count = execute_query(
            "SELECT COUNT(*) FROM lumos.executions WHERE exec_id = %s",
            (executionname,),
            fetch="one"
        )

        if count[0] != 0:
            return jsonify({'error': 'Execution name already exists'}), 400

        execute_query("""
            INSERT INTO lumos.executions
            (
                releaseid,
                lumos_user,
                exec_status,
                exec_id,
                rowid,
                env_name,
                browser,
                screen_capture,
                scheduled_dt,
                frequency,
                exec_test_list,
                exec_date
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
             DATE_TRUNC('second', CURRENT_TIMESTAMP))
        """, (
            releaseid,
            username,
            "Submitted",
            executionname,
            rowid,
            env_name,
            browser,
            screencapture,
            scheduled_dt,
            frequency,
            total_testlist
        ), commit=True)

        # Optional
        # processsubmittedrecords()

        log_activity(username,
                     action='Execution Submitted',
                     testcasename=f'Execution: {executionname}',
                     blockname='')

        return jsonify({
            "message": "Execution submitted successfully",
            "rowid": rowid
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------
# 4️⃣ Stop Execution
# ---------------------------------------------------
@testexecutions_bp.route('/api/deletepod', methods=['PUT'])
def delete_pod():

    data = request.get_json(silent=True)

    executionid = data.get('executionId')
    username = data.get('userName', '').strip()

    if not executionid:
        return jsonify({'error': 'Execution ID is required'}), 400

    try:
        row = execute_query(
            "SELECT exec_status FROM lumos.executions WHERE rowid = %s",
            (executionid,),
            fetch="one"
        )

        if not row:
            return jsonify({'error': 'Execution not found'}), 404

        status = row[0]

        if status == "Completed":
            return jsonify({'message': 'Execution already completed'}), 200

        # Optional
        # stop_containers_by_execution_id(executionid, username)

        log_activity(username,
                     action='Execution Stopped',
                     testcasename=f'Execution: {executionid}',
                     blockname='')

        return jsonify({'message': 'Execution stopped successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------
# 5️⃣ Retrigger Execution
# ---------------------------------------------------
@testexecutions_bp.route('/api/retriggerpod', methods=['POST'])
def retrigger_pod():

    data = request.get_json(silent=True)

    executionid = data.get('executionId')
    executionname = data.get('executionName')
    username = data.get('userName', '').strip()

    if not executionid or not executionname or not username:
        return jsonify({'error': 'Missing required fields'}), 400

    new_rowid = datetime.now().strftime('%Y%m%d%H%M%S')

    try:
        row = execute_query(
            """SELECT releaseid, env_name, browser,
                      screen_capture, scheduled_dt,
                      frequency, exec_test_list
               FROM lumos.executions
               WHERE rowid = %s""",
            (executionid,),
            fetch="one"
        )

        if not row:
            return jsonify({'error': 'Execution not found'}), 404

        releaseid, env_name, browser, screencapture, scheduled_dt, frequency, total_testlist = row

        execute_query("""
            INSERT INTO lumos.executions
            (
                releaseid,
                lumos_user,
                exec_status,
                exec_id,
                rowid,
                env_name,
                browser,
                screen_capture,
                scheduled_dt,
                frequency,
                exec_test_list,
                exec_date
            )
            VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
             DATE_TRUNC('second', CURRENT_TIMESTAMP))
        """, (
            releaseid,
            username,
            "Submitted",
            executionname,
            new_rowid,
            env_name,
            browser,
            screencapture,
            scheduled_dt,
            frequency,
            total_testlist
        ), commit=True)

        log_activity(username,
                     action='Execution Retriggered',
                     testcasename=f'Execution: {executionname}',
                     blockname='')

        return jsonify({'message': 'Execution retriggered successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
