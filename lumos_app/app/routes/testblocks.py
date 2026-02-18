from flask import Blueprint, request, jsonify
from ..activitylog import log_activity
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
  
