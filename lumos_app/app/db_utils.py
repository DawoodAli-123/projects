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
