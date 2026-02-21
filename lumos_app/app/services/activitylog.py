import configparser
import socket
from datetime import datetime
from ..db_utils import execute_query


# ---------------------------------------------------------
# Load DB Details from config.ini
# ---------------------------------------------------------
def get_db_details():

    config = configparser.ConfigParser()
    config.read('config.ini')

    active_db = config['LUMOS_DB']['active_db']
    db_details = config[active_db]

    return db_details, active_db


# ---------------------------------------------------------
# Log Activity using execute_query()
# ---------------------------------------------------------
def log_activity(username, action, testcasename="", blockname=""):

    try:
        db_details, active_db = get_db_details()

        db_user = db_details.get('user')
        db_schema = db_details.get('schema_name', 'lumos')

        act_date = datetime.now()
        current_time = datetime.now().strftime('%d%m%Y%H%M%S')
        act_id = f"{username}_{current_time}"

        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        query = """
            INSERT INTO lumos.activity_log
            (lumos_user,
             db_user,
             db_schema,
             act_id,
             act_date,
             action_type,
             testcasename,
             blockname,
             ip_address,
             hostname)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        execute_query(
            query,
            (
                username,
                db_user,
                db_schema,
                act_id,
                act_date,
                action,
                testcasename,
                blockname,
                ip_address,
                hostname
            ),
            commit=True
        )

    except Exception as e:
        print(f"Activity logging failed: {e}")
