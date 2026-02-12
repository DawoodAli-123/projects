import configparser
import os

def load_db_config():
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config.ini"
    )

    config = configparser.ConfigParser()
    config.read(config_path)

    active_db = config['LUMOS_DB']['active_db']
    db_config = config[active_db]

    return {
        "user": db_config["user"],
        "password": db_config["password"],
        "host": db_config["host"],
        "port": db_config["port"],
        "dbname": db_config["dbname"]
    }
