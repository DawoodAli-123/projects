from flask import Blueprint, request, jsonify
from ..db_utils import execute_query

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/developer-report", methods=["GET"])
def developer_report():

    releaseid = request.args.get("releaseId")

    if not releaseid:
        return jsonify({"error": "releaseId is required"}), 400

    try:
        # Step 1: Get start date
        query1 = """
            SELECT dt_column
            FROM lumos.lst_of_val
            WHERE type = %s AND name = %s
        """

        date_result = execute_query(
            query1,
            ("Lumos_release", releaseid),
            fetch="all"
        )

        if not date_result:
            return jsonify({"error": "Release not found"}), 404

        start_date = date_result[0][0]

        # Step 2: Get developer report data
        query2 = """
            SELECT user_id, testcase_count, execution_count
            FROM your_report_table
            WHERE start_date >= %s AND release_id = %s
        """

        data = execute_query(
            query2,
            (start_date, releaseid),
            fetch="all"
        )

        # Step 3: Build structured response
        report = []

        for row in data:
            report.append({
                "user_id": row[0],
                "testcase_count": row[1],
                "execution_count": row[2]
            })

        return jsonify(report), 200

    except Exception as e:
        return jsonify({
            "error": f"Failed to fetch developer report: {str(e)}"
        }), 500
