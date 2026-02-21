from ..db_utils import execute_query


def authenticate_user(username, password):
    """
    Authenticate user from lumos.userlist table.
    Returns user dict if valid, otherwise None.
    """

    try:
        user = execute_query("""
            SELECT username, type
            FROM lumos.userlist
            WHERE username = %s
              AND password = %s
              AND inactiveflag = 'N'
        """, (username, password), fetch="one")

        if user:
            return {
                "username": user[0],
                "type": user[1]
            }

        return None

    except Exception as e:
        print(f"Error during authentication: {e}")
        return None
