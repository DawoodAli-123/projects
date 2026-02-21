from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from functools import wraps
from ..db_utils import execute_query
from ..services.activitylog import log_activity
from ..services.login import authenticate_user

user_bp = Blueprint("user", __name__)


# ---------------------------------------------------
# Login Required Decorator
# ---------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("user.login"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------
# Login
# ---------------------------------------------------
@user_bp.route('/')
@user_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        data = request.get_json(silent=True)

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'status': 'Missing credentials'}), 400

        user = authenticate_user(username, password)

        if user:
            session['username'] = user[0]
            session['type'] = user[1]
            session['logged_in'] = True

            log_activity(user[0],
                         action="Login",
                         testcasename="",
                         blockname="")

            return jsonify({'status': 'success'}), 200

        return jsonify({'status': 'Invalid credentials'}), 401

    return render_template('login.html')


# ---------------------------------------------------
# User Type Details
# ---------------------------------------------------
@user_bp.route('/api/usertypedetails', methods=['GET'])
@login_required
def user_details():

    username = session.get('username')
    user_type = session.get('type')

    try:
        release_rows = execute_query(
            """SELECT name
               FROM lumos.lst_of_val
               WHERE type='Lumos_release'
               AND inactiveflag='N'
               ORDER BY dt_column DESC
               LIMIT 4""",
            fetch="all"
        ) or []

        release_ids = [r[0] for r in release_rows]

        return jsonify({
            'status': 'User details fetched',
            'username': username,
            'type': user_type,
            'releaseId': release_ids
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------
# Home
# ---------------------------------------------------
@user_bp.route('/home', methods=['GET'])
@login_required
def home():

    username = session.get('username')

    if username and username.strip() != "":
        return render_template('home.html', username=username)

    session.clear()
    return redirect(url_for('user.login'))


# ---------------------------------------------------
# Logout
# ---------------------------------------------------
@user_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('user.login'))


# ---------------------------------------------------
# Get User List
# ---------------------------------------------------
@user_bp.route('/api/userlist', methods=['GET'])
@login_required
def get_userlist():

    try:
        rows = execute_query(
            """SELECT username, type, mailid, orgid
               FROM lumos.userlist
               WHERE inactiveflag='N'
               ORDER BY mailid""",
            fetch="all"
        ) or []

        result = [
            {
                "username": r[0],
                "type": r[1],
                "mailid": r[2],
                "orgid": r[3]
            }
            for r in rows
        ]

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------
# Create User
# ---------------------------------------------------
@user_bp.route('/api/createuser', methods=['POST'])
@login_required
def createuser():

    data = request.get_json(silent=True)

    username = data.get('newUserName', '').strip()
    password = data.get('newPassword')
    mailid = data.get('newMailid')
    user_type = data.get('type')
    created_by = data.get('userName', '').strip()

    if not username or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        count = execute_query(
            """SELECT COUNT(*)
               FROM lumos.userlist
               WHERE username=%s
               AND inactiveflag='N'""",
            (username,),
            fetch="one"
        )

        if count[0] != 0:
            return jsonify({'error': 'User already exists'}), 400

        execute_query("""
            INSERT INTO lumos.userlist
            (lastupdby, username, password, type,
             mailid, inactiveflag, lastupd)
            VALUES (%s, %s, %s, %s,
                    %s, 'N',
                    DATE_TRUNC('second', CURRENT_TIMESTAMP))
        """, (
            created_by,
            username,
            password,
            user_type,
            mailid
        ), commit=True)

        return jsonify({'message': 'User created successfully'}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------
# Audit - Last 2 Months
# ---------------------------------------------------
@user_bp.route('/api/audit', methods=['GET'])
@login_required
def get_audit():

    try:
        rows = execute_query("""
            SELECT lumos_user,
                   TO_CHAR(act_date, 'YYYY-MM-DD HH24:MI:SS GMT') AS act_date,
                   action_type,
                   testcasename,
                   blockname
            FROM lumos.activity_log
            WHERE act_date >= NOW() - INTERVAL '2 months'
            ORDER BY act_date DESC
        """, fetch="all") or []

        return jsonify(rows), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------------------------------------------------
#  All Audit
# ---------------------------------------------------
@user_bp.route('/api/allaudit', methods=['GET'])
@login_required
def get_allaudit():

    try:
        rows = execute_query("""
            SELECT lumos_user,
                   TO_CHAR(act_date, 'YYYY-MM-DD HH24:MI:SS GMT') AS act_date,
                   action_type,
                   testcasename,
                   blockname
            FROM lumos.activity_log
            ORDER BY act_date DESC
        """, fetch="all") or []

        return jsonify(rows), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
