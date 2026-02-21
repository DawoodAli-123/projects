from flask import Blueprint, request, jsonify
from ..db_utils import execute_query
from ..services.activitylog import log_activity

testelements_bp = Blueprint("testelements", __name__)


# ---------------------------------------------------
# 1️⃣ Get All Elements
# ---------------------------------------------------
@testelements_bp.route('/list', methods=['GET'])
def get_testelement_list():
    try:
        query = """
            SELECT element, xpath, productname,
                   TO_CHAR(lastupd, 'YYYY-MM-DD HH24:MI:SS GMT') AS lastupd,
                   lastupdby
            FROM lumos.repository
            WHERE inactiveflag = 'N'
            ORDER BY lastupd DESC
        """

        rows = execute_query(query, fetch="all") or []

        result = [
            {
                "element": r[0],
                "xpath": r[1],
                "productname": r[2],
                "lastupd": r[3],
                "lastupdby": r[4]
            }
            for r in rows
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------
# 2️⃣ Edit Element
# ---------------------------------------------------
@testelements_bp.route('/edit', methods=['GET'])
def edit_testelement():

    elementname = request.args.get('elementName')

    if not elementname:
        return jsonify({'error': 'Element Name is required'}), 400

    try:
        query = """
            SELECT element, xpath, pagetitle,
                   popuptitle, dropdownvalues,
                   defaultvalue, productname
            FROM lumos.repository
            WHERE element = %s AND inactiveflag = 'N'
        """

        row = execute_query(query, (elementname,), fetch="one")

        if not row:
            return jsonify({'error': 'Element not found'}), 404

        result = {
            "element": row[0],
            "xpath": row[1],
            "pagetitle": row[2],
            "popuptitle": row[3],
            "dropdownvalues": row[4],
            "defaultvalue": row[5],
            "productname": row[6]
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------
# 3️⃣ Save Element
# ---------------------------------------------------
@testelements_bp.route('/save', methods=['POST'])
def save_testelement():

    data = request.get_json(silent=True)

    elementname = data.get('elementName', '').strip()
    xpath = data.get('xpath')
    pagetitle = data.get('pageTitle')
    popuptitle = data.get('popupTitle')
    dropdownvalues = data.get('dropdownValues')
    defaultvalue = data.get('defaultValue')
    productname = data.get('productName')
    username = data.get('userName', '').strip()

    if not elementname or not xpath or not username:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # Check duplicate element
        element_count = execute_query(
            """SELECT COUNT(*) FROM lumos.repository
               WHERE element = %s AND inactiveflag = 'N'""",
            (elementname,),
            fetch="one"
        )

        if element_count[0] != 0:
            return jsonify({'error': 'Element already exists'}), 400

        # Check duplicate xpath
        xpath_count = execute_query(
            """SELECT COUNT(*) FROM lumos.repository
               WHERE xpath = %s AND inactiveflag = 'N'""",
            (xpath,),
            fetch="one"
        )

        if xpath_count[0] != 0:
            return jsonify({'error': 'XPath already exists'}), 400

        # Insert new element
        execute_query("""
            INSERT INTO lumos.repository
            (lastupdby, element, xpath, pagetitle,
             popuptitle, dropdownvalues, defaultvalue,
             productname, inactiveflag, lastupd)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s,
                    'N', DATE_TRUNC('second', CURRENT_TIMESTAMP))
        """, (
            username, elementname, xpath,
            pagetitle, popuptitle,
            dropdownvalues, defaultvalue,
            productname
        ), commit=True)

        log_activity(username, action='Create',
                     testcasename=f'Element: {elementname}',
                     blockname='')

        return jsonify({'message': 'Element created successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------
# 4️⃣ Update Element
# ---------------------------------------------------
@testelements_bp.route('/update', methods=['PUT'])
def update_testelement():

    data = request.get_json(silent=True)

    elementname = data.get('elementName', '').strip()
    xpath = data.get('xpath')
    pagetitle = data.get('pageTitle')
    popuptitle = data.get('popupTitle')
    dropdownvalues = data.get('dropdownValues')
    defaultvalue = data.get('defaultValue')
    productname = data.get('productName')
    username = data.get('userName', '').strip()

    if not elementname or not xpath or not username:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        affected_rows = execute_query("""
            UPDATE lumos.repository
            SET lastupdby=%s,
                xpath=%s,
                pagetitle=%s,
                popuptitle=%s,
                dropdownvalues=%s,
                defaultvalue=%s,
                productname=%s,
                lastupd=DATE_TRUNC('second', CURRENT_TIMESTAMP)
            WHERE element=%s AND inactiveflag='N'
        """, (
            username, xpath, pagetitle,
            popuptitle, dropdownvalues,
            defaultvalue, productname,
            elementname
        ), commit=True, return_rowcount=True)

        if affected_rows == 0:
            return jsonify({'error': 'Element not found'}), 404

        log_activity(username, action='Update',
                     testcasename=f'Element: {elementname}',
                     blockname='')

        return jsonify({'message': 'Element updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------
# 5️⃣ Soft Delete Element
# ---------------------------------------------------
@testelements_bp.route('/delete', methods=['PUT'])
def delete_testelement():

    data = request.get_json(silent=True)

    elementname = data.get('elementName')
    username = data.get('userName')

    if not elementname or not username:
        return jsonify({'error': 'Element Name and User Name are required'}), 400

    try:
        affected_rows = execute_query("""
            UPDATE lumos.repository
            SET inactiveflag='Y',
                lastupdby=%s,
                lastupd=DATE_TRUNC('second', CURRENT_TIMESTAMP)
            WHERE element=%s
        """, (username, elementname),
           commit=True,
           return_rowcount=True)

        if affected_rows == 0:
            return jsonify({'error': 'Element not found'}), 404

        log_activity(username, action='Delete',
                     testcasename=f'Element: {elementname}',
                     blockname='')

        return jsonify({'message': 'Element deleted successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
