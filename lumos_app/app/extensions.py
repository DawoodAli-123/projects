# db, jwt, migrate, etc. related code will store here
import psycopg2
from psycopg2 import pool
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

jwt = JWTManager()
migrate = Migrate()

connection_pool = None

def init_db_pool(db_config):
    global connection_pool

    connection_pool = pool.ThreadedConnectionPool(
        1,
        20,
        user=db_config["user"],
        password=db_config["password"],
        host=db_config["host"],
        port=db_config["port"],
        database=db_config["dbname"]
    )

