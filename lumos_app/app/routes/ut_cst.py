from flask import Blueprint, request, jsonify
from datetime import datetime
from ..db_utils import execute_query
from ..services.activitylog import log_activity

ut_bp = Blueprint("ut", __name__)


# ==========================================================
# GET UT LIST
# ==========================================================
@ut_bp.route('/api/utlist', methods=['GET'])
def get_utlist():
    try:
        rows = execute_query("""
            SELECT rowid,
                   releaseid,
                   storyref,
                   name,
                   description,
                   acceptancecriteria,
                   type,
                   review,
                   reviewcomments,
                   status,
                   regressiontest,
                   passivesite,
                   lastupdby,
                   TO_CHAR(lastupd_at, 'YYYY-MM-DD HH24:MI:SS GMT')
            FROM lumos.ut_list
            WHERE inactiveflag = 'N'
            ORDER BY rowid DESC
        """, fetch="all") or []

        return jsonify({"ut_list": rows}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==========================================================
# EDIT UT
# ==========================================================
@ut_bp.route('/api/editutlist', methods=['GET'])
def edit_utlist():

    rowid = request.args.get('rowId')

    if not rowid:
        return jsonify({'error': 'RowId is required'}), 400

    try:
        row = execute_query("""
            SELECT rowid,
                   releaseid,
                   storyref,
                   name,
                   description,
                   acceptancecriteria,
                   type,
                   review,
                   reviewcomments,
                   status,
                   regressiontest,
                   passivesite
            FROM lumos.ut_list
            WHERE rowid = %s
        """, (rowid,), fetch="one")

        if not row:
            return jsonify({'error': 'UT record not found'}), 404

        result = {
            "rowId": row[0],
            "releaseId": row[1],
            "storyRef": row[2],
            "name": row[3],
            "description": row[4],
            "acceptancecriteria": row[5],
            "type": row[6],
            "review": row[7],
            "reviewcomments": row[8],
            "status": row[9],
            "regressiontest": row[10],
            "passivesite": row[11]
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==========================================================
# SAVE UT
# ==========================================================
@ut_bp.route('/api/saveutlist', methods=['POST'])
def save_utlist():

    data = request.get_json(silent=True)

    required = ['ReleaseNumber', 'SaborRefNum', 'Name', 'userName']
    missing = [f for f in required if not data or not data.get(f)]

    if missing:
        return jsonify({'error': f"Missing fields: {', '.join(missing)}"}), 400

    try:
        rowid = datetime.now().strftime('%Y%m%d%H%M%S')

        execute_query("""
            INSERT INTO lumos.ut_list
            (rowid, releaseid, storyref, name, description,
             acceptancecriteria, type, review, reviewcomments,
             status, regressiontest, passivesite,
             inactiveflag, lastupdby, lastupd_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    'N', %s,
                    DATE_TRUNC('second', CURRENT_TIMESTAMP))
        """, (
            rowid,
            data['ReleaseNumber'],
            data['SaborRefNum'],
            data['Name'],
            data.get('Description'),
            data.get('AcceptanceCriteria'),
            data.get('Type'),
            data.get('DesignReview'),
            data.get('ReviewComments'),
            data.get('Status'),
            data.get('RegressionTest'),
            data.get('PassiveSite'),
            data['userName']
        ), commit=True)

        log_activity(
            data['userName'],
            action='Create',
            testcasename=f"UT StoryRef: {data['SaborRefNum']}",
            blockname=''
        )

        return jsonify({'message': 'UT record created successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==========================================================
# UPDATE UT
# ==========================================================
@ut_bp.route('/api/updateutlist', methods=['PUT'])
def update_utlist():

    data = request.get_json(silent=True)

    required = ['rowId', 'ReleaseNumber', 'SaborRefNum', 'Name', 'userName']
    missing = [f for f in required if not data or not data.get(f)]

    if missing:
        return jsonify({'error': f"Missing fields: {', '.join(missing)}"}), 400

    try:
        affected = execute_query("""
            UPDATE lumos.ut_list
            SET releaseid=%s,
                storyref=%s,
                name=%s,
                description=%s,
                acceptancecriteria=%s,
                type=%s,
                review=%s,
                reviewcomments=%s,
                status=%s,
                regressiontest=%s,
                passivesite=%s,
                lastupdby=%s,
                lastupd_at=DATE_TRUNC('second', CURRENT_TIMESTAMP)
            WHERE rowid=%s
        """, (
            data['ReleaseNumber'],
            data['SaborRefNum'],
            data['Name'],
            data.get('Description'),
            data.get('AcceptanceCriteria'),
            data.get('Type'),
            data.get('DesignReview'),
            data.get('ReviewComments'),
            data.get('Status'),
            data.get('RegressionTest'),
            data.get('PassiveSite'),
            data['userName'],
            data['rowId']
        ), commit=True, return_rowcount=True)

        if affected == 0:
            return jsonify({'error': 'UT record not found'}), 404

        log_activity(
            data['userName'],
            action='Update',
            testcasename=f"UT StoryRef: {data['SaborRefNum']}",
            blockname=''
        )

        return jsonify({'message': 'UT record updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==========================================================
# DELETE UT (Soft Delete)
# ==========================================================
@ut_bp.route('/api/deleteutlist', methods=['PUT'])
def delete_utlist():

    data = request.get_json(silent=True)

    rowid = data.get('rowId')
    username = data.get('userName')
    storyref = data.get('storyRef')

    if not rowid or not username:
        return jsonify({'error': 'RowId and userName required'}), 400

    try:
        execute_query("""
            UPDATE lumos.ut_list
            SET inactiveflag='Y',
                lastupdby=%s,
                lastupd_at=DATE_TRUNC('second', CURRENT_TIMESTAMP)
            WHERE rowid=%s
        """, (username, rowid), commit=True)

        execute_query("""
            UPDATE lumos.ut_cst_int
            SET inactiveflag='Y',
                lastupdby=%s,
                lastupd_at=DATE_TRUNC('second', CURRENT_TIMESTAMP)
            WHERE ut_rowid=%s
        """, (username, rowid), commit=True)

        log_activity(
            username,
            action='Delete',
            testcasename=f"UT StoryRef: {storyref}",
            blockname=''
        )

        return jsonify({'message': 'UT record deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
