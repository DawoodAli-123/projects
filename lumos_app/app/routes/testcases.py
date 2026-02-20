from flask import Blueprint, request, jsonify
from ..services.activitylog import log_activity
from ..db_utils import execute_query
from ..extensions import connection_pool
from datetime import datetime

testcases_bp = Blueprint("testcases", __name__)


@testcases_bp.route("/list", methods=["GET"])
def testcases_list():
    try:
        query = """
            SELECT testcasename, act_date, lumos_user, action_type
            FROM (
                SELECT 
                    t.testcasename,
                    al.lumos_user,
                    TO_CHAR(al.act_date, 'YYYY-MM-DD HH24:MI:SS GMT') AS act_date,
                    al.action_type,
                    ROW_NUMBER() OVER(
                        PARTITION BY t.testcasename 
                        ORDER BY al.act_date DESC
                    ) AS rn
                FROM lumos.testcase_list t
                LEFT JOIN lumos.activity_log al
                    ON t.testcasename = al.testcasename
                WHERE t.inactiveflag = 'N'
            ) t1
            WHERE rn = 1
        """

        rows = execute_query(query, fetch="all") or []

        response = [
            {
                "testcasename": r[0],
                "act_date": r[1],
                "lumos_user": r[2],
                "action_type": r[3]
            }
            for r in rows
        ]

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#API endpoint to retrieve the Test Case ID for a given Test Case Name (if active)
@testcases_bp.route('/testcase_id', methods=['GET'])
def testcase_id():
  
  testcase_name = request.args.get('testcase_name')
  
  try:
  
    id = execute_query('''SELECT testid FROM lumos.testcase_list WHERE testcasename = %s AND Inactiveflag = 'N';''', 
                  (testcase_name,), fetch="one")

    return jsonify({"id": id}), 200
  
  except Exception as e:
  
    return jsonify({'error': f"Failed at testcase_id: {str(e))"}), 400


@testcases_bp.route("/edit", methods=["GET"])
def edit_testcase():

    testcase_name = request.args.get("testcase_name")

    if not testcase_name:
        return jsonify({
            "error": "Missing input: Test case Name must be specified."
        }), 400

    try:
        query = '''SELECT CASE WHEN action = 'Reuseable' THEN (element) ELSE 'Non Reuseable' END AS step_type, 
        CASE WHEN action 'Reuseable' THEN ('Plain action') ELSE element END AS element, 
        CASE WHEN action = 'Reuseable' THEN ('Action') ELSE action END AS action, 
        errorcode, defaultvalue, variable, update_flag
        FROM lumos.regression_pack
        WHERE testcasename = %s ORDER BY step;'''

        rows = execute_query(query, (testcase_name,), fetch="all")

        formatted_rows = [
            {
                "StepType": row[0],
                "Element": row[1],
                "Action": row[2],
                "ErrorCode": row[3],
                "Value": row[4],
                "Variable": row[5],
                "UpdateFlag": row[6]
            }
            for row in rows
        ]

        return jsonify(formatted_rows), 200

    except Exception as e:
        return jsonify({"error": f"Failed at edit_testcase: {str(e)}"}), 500


# API endpoint to generate a unique ID based on the current timestamp in 'YYYYMMDDHHMMSS' format
@testcases_bp.route('/generate_id', methods=['GET'])
def generate_id():
    current_datetime = datetime.now().strftime('%Y%m%d%H%M%S')
    return jsonify({"id": current_datetime}), 200


@testcases_bp.route("/save", methods=['POST'])
def save_testcase():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'Invalid JSON input'}), 400

    testcasename = data.get('testcasekName', '').strip()
    testid = data.get('testID')
    steplist = data.get('stepList')
    username = data.get('userName', '').strip()

    if not testcasename:
        return jsonify({'error': 'Test Case name is mandatory.'}), 400

    if not username:
        return jsonify({'error': 'User name is missing.'}), 400

    if not steplist:
        return jsonify({'error': 'At least one step is required.'}), 400

    try:
        # Check if testcase already exists
        count = execute_query(
            """
            SELECT COUNT(*) 
            FROM lumos.regression_pack 
            WHERE testcasename = %s 
            AND inactiveflag = %s
            """,
            (testcasename, 'N'),
            fetch="one"
        )

        if count[0] != 0:
            return jsonify({
                'error': f"Testblock {testcasename} already exists."
            }), 400

        # Insert steps
        for step_number, item in enumerate(steplist, start=1):

            step_type = item.get('StepType')
            element = item.get('Element')
            action = item.get('Action')
            errorcode = item.get('ErrorCode')
            regvalue = item.get('Value')
            var_value = item.get('Variable')

            query = """
                INSERT INTO lumos.regression_pack
                (
                    testid
                    lastupdby,
                    testcasename,
                    step,
                    element,
                    action,
                    errorcode,
                    defaultvalue,
                    variable,
                    update_flag,
                    lastupd
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s,
                    'YES',
                    DATE_TRUNC('second', CURRENT_TIMESTAMP)
                )
            """

            values = (
                testid,
                username,
                testcasename,
                step_number,
                element if step_type == 'Non Reuseable' else step_type,
                action if step_type == 'Non Reuseable' else 'Reuseable',
                errorcode,
                regvalue,
                var_value
            )

            execute_query(query, values, commit=True)

        # The insertion into TESTCASE_LIST table
        execute_query('''INSERT INTO lumos. TESTCASE_LIST
        (testcasename, testID, priority_level, product_name, scenario_type, channel_type, journey_type)
        VALUES (%s, %s, 'P2', '', '', '', '')''', (testcasename, testid), commit=True )

        # Log activity
        log_activity(
            username,
            action='Create',
            testcasename=testcasename,
            blockname=''
        )

        return jsonify({'message': f"Testcase {testcasename} created successfully."}), 201

    except Exception as e:
        return jsonify({'error': f"Failed at save_testcase: {str(e)}"}), 500


# API to update an existing Test Block by replacing its steps in the Reuseable_pack table
@testblocks_bp.route('/update', methods=['PUT'])
def update_testcase():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    testcasename = data.get('testcasekName', '').strip()
    testid = data.get('testID')
    steplist = data.get('stepList')
    username = data.get('userName', '').strip()

    if not testcasename:
        return jsonify({'error': 'Invalid Test Case selected.'}), 400

    if not username:
        return jsonify({'error': 'User name is missing.'}), 400

    try:
        # Check existence
        count = execute_query(
            """
            SELECT COUNT(*)
            FROM lumos.reuseable_pack
            WHERE testcasename = %s AND inactiveflag = %s
            """,
            (testcasename, 'N'),
            fetch="one"
        )

        if count[0] == 0:
            return jsonify({
                'error': f"Testblock {testcasename} does not exist."
            }), 400

        # Start manual transaction
        conn = connection_pool.getconn()

        try:
            cursor = conn.cursor()

            # Delete old steps
            cursor.execute("DELETE FROM lumos.regression_pack WHERE testcasename = %s", (testcasename,))

            # Insert new steps
            for step_number, item in enumerate(steplist, start=1):

                cursor.execute("""
                    INSERT INTO lumos.regression_pack
                    (
                        lastupdby,
                        testid,
                        testcasename,
                        step,
                        element,
                        action,
                        errorcode,
                        defaultvalue,
                        variable,
                        update_flag,
                        lastupd
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        'YES',
                        DATE_TRUNC('second', CURRENT_TIMESTAMP)
                    )
                """, (
                    username,
                    testid,
                    testcasename,
                    step_number,
                    item.get('Element'),
                    item.get('Action'),
                    item.get('ErrorCode'),
                    item.get('Value'),
                    item.get('Variable')
                ))

            conn.commit()  # Commit once

            log_activity(
                username,
                action='Update',
                testcasename=testcasename,
                blockname=''
            )

            return jsonify({
                'message': f"Test Block {testcasename} updated successfully."
            }), 200

        except Exception as error:
            conn.rollback()  # Rollback everything
            return jsonify({
                'error': f"Update failed: {str(error)}"
            }), 500

        finally:
            connection_pool.putconn(conn)

    except Exception as e:
        return jsonify({'error': f"Failed at update_testcase: {str(e)}"}), 500


#API endpoint to populate dropdown options for test step creation/editing 
@testcases_bp.route('/populate_rows', methods=['GET'])
def populate_rows():
  
  conn connection_pool.getconn()
  
  try:
    
    cursor conn.cursor()
    
    cursor.execute('SELECT DISTINCT blockname FROM lumos.reuseable pack ORDER BY blockname')
    reuseablelist = ["Non Reuseable"]+ [item[0] for item in cursor.fetchall()]
    
    cursor.execute('SELECT DISTINCT element FROM lumos.repository ORDER BY element')
    elementlist = ["Plain action"]+ [item[0] for item in cursor.fetchall()]
    
    cursor.execute('SELECT functions FROM lumos.functions ORDER BY functions')
    functionlist = ["Action"]+ [item[0] for item in cursor.fetchall()] cursor.execute('SELECT textid FROM lumos.generictexttable')
  
    cursor.execute('SELECT tectid FROM lumos.generictexttable')
    textidlist= [item[0] for item in cursor.fetchall()]
    
    return jsonify({
      "StepType": reuseablelist,
      "Element": elementlist,
      "Action": functionlist,
      "ErrorCode": textidlist
    }), 200
  
  except Exception as e:
    return jsonify({'error': f"Failed at populate_rows: (str(e))"}), 400

  finally:
    cursor.close()
    connection_pool.putconn(conn)


# API to Soft-delete a Test Block by marking it inactive in Reuseable_pack tables
@testcases_bp.route('/delete', methods=['PUT'])
def delete_testcase():

    data = request.get_json(silent=True)
    testcase_name = data.get('testcase_name')
    username = data.get('userName')

    conn = connection_pool.getconn()

    try:
        cursor = conn.cursor()

        tables = [
            "lumos.regression_pack",
            "lumos.testcase_list",
            "lumos.testpack_list"
        ]

        for table in tables:
            cursor.execute(f"""
                UPDATE {table}
                SET inactiveflag = %s,
                    lastupdby = %s,
                    lastupd = DATE_TRUNC('second', CURRENT_TIMESTAMP)
                WHERE testcasename = %s
            """, ('Y', username, testcase_name))

        conn.commit()

        log_activity(username, action='Delete',
                     testcasename=testcase_name, blockname='')

        return jsonify({'message': 'Deleted successfully'}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500

    finally:
        connection_pool.putconn(conn)
