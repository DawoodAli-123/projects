from flask import Blueprint, request, jsonify
from ..db_utils import execute_query
from ..services.activitylog import log_activity

userstory_bp = Blueprint("userstory", __name__)


# -------------------------------------------------------
# Get All Active User Stories
# -------------------------------------------------------
@userstory_bp.route('/api/userstorylist', methods=['GET'])
def get_userstory():
    try:
        rows = execute_query("""
            SELECT rowid,
                   releaseid,
                   productfamily,
                   epicid,
                   featureid,
                   storydesc,
                   developers,
                   designers,
                   status,
                   manual_tcount,
                   lumos_tcount,
                   lastupdby,
                   TO_CHAR(lastupd_at, 'YYYY-MM-DD HH24:MI:SS GMT')
            FROM lumos.user_story
            WHERE inactiveflag = 'N'
            ORDER BY lastupd_at DESC
        """, fetch="all") or []

        return jsonify({"UserStories": rows}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------
# Get Single User Story for Edit
# -------------------------------------------------------
@userstory_bp.route('/api/edituserstory', methods=['GET'])
def edit_userstory():

    rowid = request.args.get('rowId')

    if not rowid:
        return jsonify({'error': 'RowId is required'}), 400

    try:
        row = execute_query("""
            SELECT releaseid,
                   productfamily,
                   epicid,
                   featureid,
                   storydesc,
                   developers,
                   designers,
                   status,
                   manual_tcount,
                   lumos_tcount
            FROM lumos.user_story
            WHERE rowid = %s
        """, (rowid,), fetch="one")

        if not row:
            return jsonify({'error': 'User story not found'}), 404

        result = {
            "releaseId": row[0],
            "productFamily": row[1],
            "epicId": row[2],
            "featureId": row[3],
            "storyDesc": row[4],
            "developers": row[5],
            "designers": row[6],
            "status": row[7],
            "manual_tcount": row[8],
            "lumos_tcount": row[9]
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------
# Create New User Story
# -------------------------------------------------------
@userstory_bp.route('/api/saveuserstory', methods=['POST'])
def save_userstory():

    data = request.get_json(silent=True)

    required_fields = [
        'rowId', 'releaseId', 'productFamily', 'epicId',
        'featureId', 'storyDesc', 'developers',
        'designers', 'status',
        'manual_tcount', 'lumos_tcount', 'userName'
    ]

    missing = [field for field in required_fields if not data or not data.get(field)]

    if missing:
        return jsonify({'error': f"Missing fields: {', '.join(missing)}"}), 400

    try:
        execute_query("""
            INSERT INTO lumos.user_story
            (rowid, releaseid, productfamily, epicid,
             featureid, storydesc, developers, designers,
             status, manual_tcount, lumos_tcount,
             inactiveflag, lastupdby, lastupd_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    'N', %s,
                    DATE_TRUNC('second', CURRENT_TIMESTAMP))
        """, (
            data['rowId'],
            data['releaseId'],
            data['productFamily'],
            data['epicId'],
            data['featureId'],
            data['storyDesc'],
            data['developers'],
            data['designers'],
            data['status'],
            data['manual_tcount'],
            data['lumos_tcount'],
            data['userName']
        ), commit=True)

        log_activity(
            data['userName'],
            action='Create',
            testcasename=f"Story FeatureId: {data['featureId']}",
            blockname=''
        )

        return jsonify({'message': 'User story created successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------
# Update User Story
# -------------------------------------------------------
@userstory_bp.route('/api/updateuserstory', methods=['PUT'])
def update_userstory():

    data = request.get_json(silent=True)

    required_fields = ['rowId', 'releaseId', 'productFamily', 'epicId', 'featureId', 'userName']

    missing = [field for field in required_fields if not data or not data.get(field)]

    if missing:
        return jsonify({'error': f"Missing fields: {', '.join(missing)}"}), 400

    try:
        affected = execute_query("""
            UPDATE lumos.user_story
            SET releaseid=%s,
                productfamily=%s,
                epicid=%s,
                featureid=%s,
                storydesc=%s,
                developers=%s,
                designers=%s,
                status=%s,
                manual_tcount=%s,
                lumos_tcount=%s,
                lastupdby=%s,
                lastupd_at=DATE_TRUNC('second', CURRENT_TIMESTAMP)
            WHERE rowid=%s
        """, (
            data['releaseId'],
            data['productFamily'],
            data['epicId'],
            data['featureId'],
            data.get('storyDesc'),
            data.get('developers'),
            data.get('designers'),
            data.get('status'),
            data.get('manual_tcount'),
            data.get('lumos_tcount'),
            data['userName'],
            data['rowId']
        ), commit=True, return_rowcount=True)

        if affected == 0:
            return jsonify({'error': 'User story not found'}), 404

        log_activity(
            data['userName'],
            action='Update',
            testcasename=f"Story FeatureId: {data['featureId']}",
            blockname=''
        )

        return jsonify({'message': 'User story updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------
# Soft Delete User Story
# -------------------------------------------------------
@userstory_bp.route('/api/deleteuserstory', methods=['PUT'])
def delete_userstory():

    data = request.get_json(silent=True)

    rowid = data.get('rowId')
    username = data.get('userName')

    if not rowid or not username:
        return jsonify({'error': 'RowId and userName required'}), 400

    try:
        affected = execute_query("""
            UPDATE lumos.user_story
            SET inactiveflag='Y',
                lastupdby=%s,
                lastupd_at=DATE_TRUNC('second', CURRENT_TIMESTAMP)
            WHERE rowid=%s
        """, (username, rowid),
           commit=True,
           return_rowcount=True)

        if affected == 0:
            return jsonify({'error': 'User story not found'}), 404

        log_activity(
            username,
            action='Delete',
            testcasename=f"Story RowId: {rowid}",
            blockname=''
        )

        return jsonify({'message': 'User story deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
