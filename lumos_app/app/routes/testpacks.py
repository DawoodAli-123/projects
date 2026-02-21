from flask import Blueprint, request, jsonify
from ..db_utils import execute_query
from ..services.activitylog import log_activity

testpacks_bp = Blueprint("testpacks", __name__)


# ---------------------------------------------------
# 1️⃣ Get All Test Packs
# ---------------------------------------------------
@testpacks_bp.route('/list', methods=['GET'])
def get_testpacklist():
    try:
        query = """
            SELECT DISTINCT testpack_name,
                   TO_CHAR(lastupd, 'YYYY-MM-DD HH24:MI:SS GMT') AS lastupd,
                   lastupdby
            FROM lumos.testpack_list
            WHERE inactiveflag = 'N'
            ORDER BY testpack_name
        """

        rows = execute_query(query, fetch="all") or []

        result = [
            {
                "testpack_name": r[0],
                "lastupd": r[1],
                "lastupdby": r[2]
            }
            for r in rows
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------
# 2️⃣ Populate Active Testcases
# ---------------------------------------------------
@testpacks_bp.route('/populate_testcases', methods=['GET'])
def populate_testcases():
    try:
        query = """
            SELECT DISTINCT testcasename
            FROM lumos.testcase_list
            WHERE inactiveflag = 'N'
            ORDER BY testcasename
        """

        rows = execute_query(query, fetch="all") or []

        return jsonify({
            "TestcasesList": [r[0] for r in rows]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------
# 3️⃣ Edit Test Pack
# ---------------------------------------------------
@testpacks_bp.route('/edit', methods=['GET'])
def edit_testpack():

    testpack_name = request.args.get('testpackName')

    if not testpack_name:
        return jsonify({'error': 'Test Pack Name is required'}), 400

    try:
        # Testcases inside pack
        query1 = """
            SELECT DISTINCT testcasename
            FROM lumos.testpack_list
            WHERE testpack_name = %s
              AND inactiveflag = 'N'
              AND testcasename IS NOT NULL
            ORDER BY testcasename
        """

        pack_cases = execute_query(query1, (testpack_name,), fetch="all") or []

        # Active testcases NOT in pack
        query2 = """
            SELECT DISTINCT t.testcasename
            FROM lumos.testcase_list t
            WHERE t.inactiveflag = 'N'
              AND NOT EXISTS (
                  SELECT 1
                  FROM lumos.testpack_list tp
                  WHERE tp.testpack_name = %s
                    AND tp.testcasename = t.testcasename
                    AND tp.inactiveflag = 'N'
              )
            ORDER BY t.testcasename
        """

        other_cases = execute_query(query2, (testpack_name,), fetch="all") or []

        return jsonify({
            "testpack_testcases": [r[0] for r in pack_cases],
            "testcases": [r[0] for r in other_cases]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------
# 4️⃣ Save Test Pack
# ---------------------------------------------------
@testpacks_bp.route('/save', methods=['POST'])
def save_testpack():

    data = request.get_json(silent=True)

    testpackname = data.get('testpackName', '').strip()
    testcaselist = data.get('testcaseList', [])
    username = data.get('userName', '').strip()

    if not testpackname or not username:
        return jsonify({'error': 'Missing required fields'}), 400

    if not testcaselist:
        return jsonify({'error': 'Empty test pack'}), 400

    try:
        count = execute_query(
            """SELECT COUNT(*) FROM lumos.testpack_list
               WHERE testpack_name = %s AND inactiveflag = 'N'""",
            (testpackname,),
            fetch="one"
        )

        if count[0] != 0:
            return jsonify({'error': 'Test Pack already exists'}), 400

        for tc in testcaselist:
            execute_query("""
                INSERT INTO lumos.testpack_list
                (created_by, lastupdby, testpack_name,
                 testcasename, inactiveflag, lastupd)
                VALUES (%s, %s, %s, %s,
                        'N', DATE_TRUNC('second', CURRENT_TIMESTAMP))
            """, (username, username, testpackname, tc),
               commit=True)

        log_activity(username,
                     action='Create',
                     testcasename=f'Pack: {testpackname}',
                     blockname='')

        return jsonify({'message': 'Test Pack created successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------
# 5️⃣ Update Test Pack
# ---------------------------------------------------
@testpacks_bp.route('/update', methods=['PUT'])
def update_testpack():

    data = request.get_json(silent=True)

    testpackname = data.get('testpackName', '').strip()
    new_testcases = data.get('testcaseList', [])
    username = data.get('userName', '').strip()

    if not testpackname or not username:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        execute_query(
            "DELETE FROM lumos.testpack_list WHERE testpack_name = %s",
            (testpackname,),
            commit=True
        )

        for tc in new_testcases:
            execute_query("""
                INSERT INTO lumos.testpack_list
                (created_by, lastupdby, testpack_name,
                 testcasename, inactiveflag, lastupd)
                VALUES (%s, %s, %s, %s,
                        'N', DATE_TRUNC('second', CURRENT_TIMESTAMP))
            """, (username, username, testpackname, tc),
               commit=True)

        log_activity(username,
                     action='Update',
                     testcasename=f'Pack: {testpackname}',
                     blockname='')

        return jsonify({'message': 'Test Pack updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------
# 6️⃣ Soft Delete Test Pack
# ---------------------------------------------------
@testpacks_bp.route('/delete', methods=['PUT'])
def delete_testpack():

    data = request.get_json(silent=True)

    testpackname = data.get('testpackName')
    username = data.get('userName')

    if not testpackname or not username:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        affected = execute_query("""
            UPDATE lumos.testpack_list
            SET inactiveflag='Y',
                lastupdby=%s,
                lastupd=DATE_TRUNC('second', CURRENT_TIMESTAMP)
            WHERE testpack_name=%s
        """, (username, testpackname),
           commit=True,
           return_rowcount=True)

        if affected == 0:
            return jsonify({'error': 'Test Pack not found'}), 404

        log_activity(username,
                     action='Delete',
                     testcasename=f'Pack: {testpackname}',
                     blockname='')

        return jsonify({'message': 'Test Pack deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
