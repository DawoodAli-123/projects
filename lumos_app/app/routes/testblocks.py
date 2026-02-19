from flask import Blueprint, request, jsonify
from ..services.activitylog import log_activity
from ..db_utils import execute_query

testblocks_bp = Blueprint("testblocks", __name__)

@testblocks_bp.route("/list", methods=["GET"])
def testblocks_list():
    try:

        query = """
            SELECT blockname, act_date, lumos_user, action_type
            FROM (
                SELECT 
                    b.blockname,
                    al.lumos_user,
                    TO_CHAR(al.act_date, 'YYYY-MM-DD HH24:MI:SS GMT') AS act_date,
                    al.action_type,
                    ROW_NUMBER() OVER (
                        PARTITION BY b.blockname 
                        ORDER BY al.act_date DESC
                    ) AS rn
                FROM (
                    SELECT DISTINCT blockname
                    FROM lumos.reuseable_pack
                    WHERE inactiveflag = 'N'
                ) b
                LEFT JOIN lumos.activity_log al
                    ON b.blockname = al.blockname
            ) t1
            WHERE rn = 1
        """

        result = execute_query(query, fetch="all")

        response = [
            {
                "blockname": row[0],
                "act_date": row[1],
                "lumos_user": row[2],
                "action_type": row[3]
            }
            for row in result
        ]

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Failed at testblocks list: {str(e)}"}), 500
  

from flask import Blueprint, request, jsonify
from ..db_utils import execute_query

testblocks_bp = Blueprint("testblocks", __name__)


@testblocks_bp.route("/edit", methods=["GET"])
def edit_testblock():

    testblock_name = request.args.get("testblock_name")

    if not testblock_name:
        return jsonify({
            "error": "Missing input: Test Block Name must be specified."
        }), 400

    try:
        query = """
            SELECT 
                CASE 
                    WHEN action = 'Reuseable' 
                    THEN element 
                    ELSE 'Non Reuseable' 
                END AS step_type,
                CASE 
                    WHEN action = 'Reuseable' 
                    THEN 'Plain action' 
                    ELSE element 
                END AS element,
                CASE 
                    WHEN action = 'Reuseable' 
                    THEN 'Action' 
                    ELSE action 
                END AS action,
                errorcode, defaultvalue, variable, update_flag
            FROM lumos.reuseable_pack WHERE blockname = %s ORDER BY step
        """

        rows = execute_query(query, (testblock_name,), fetch="all")

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
        return jsonify({"error": f"Failed at edit_testblock: {str(e)}"}), 500


@testblocks_bp.route("/save", methods=['POST'])
def save_testblock():

    data = request.get_json(silent=True)

    if not data:
        return jsonify({'error': 'Invalid JSON input'}), 400

    testblockname = data.get('testblockName', '').strip()
    steplist = data.get('stepList')
    username = data.get('userName', '').strip()

    if not testblockname:
        return jsonify({'error': 'Test Block name is mandatory.'}), 400

    if not username:
        return jsonify({'error': 'User name is missing.'}), 400

    if not steplist:
        return jsonify({'error': 'At least one step is required.'}), 400

    try:
        # Check if block already exists
        count = execute_query(
            """
            SELECT COUNT(*) 
            FROM lumos.reuseable_pack 
            WHERE blockname = %s 
            AND inactiveflag = %s
            """,
            (testblockname, 'N'),
            fetch="one"
        )

        if count[0] != 0:
            return jsonify({
                'error': f"Testblock {testblockname} already exists."
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
                INSERT INTO lumos.reuseable_pack
                (
                    lastupdby,
                    blockname,
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
                username,
                testblockname,
                step_number,
                element if step_type == 'Non Reuseable' else step_type,
                action,
                errorcode,
                regvalue,
                var_value
            )

            execute_query(query, values, commit=True)

        # Log activity
        log_activity(
            username,
            action='Create',
            testcasename='',
            blockname=testblockname
        )

        return jsonify({'message': f"Testblock {testblockname} created successfully."}), 201

    except Exception as e:
        return jsonify({'error': f"Failed at save_testblock: {str(e)}"}), 500

