# Right now, I’m guessing in routes you are doing:

# conn = connection_pool.getconn()
# cursor = conn.cursor()
# cursor.execute(...)

# This will be repeated everywhere.

from app.extensions import connection_pool

def execute_query(query, params=None, fetch=False):
    conn = connection_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)

        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = None

        return result
    finally:
        connection_pool.putconn(conn)


# Then routes become clean:

# from app.db_utils import execute_query

# @user_bp.route("/")
# def get_users():
#     users = execute_query("SELECT * FROM users", fetch=True)
#     return {"data": users}
