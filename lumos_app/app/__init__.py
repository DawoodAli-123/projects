from flask import Flask
from .routes import register_blueprints
from .config import load_db_config, Config
from .extensions import init_db_pool


def create_app():
    app = Flask(__name__)

    # Load BASE_DIR and other app config
    app.config.from_object(Config)

    # Load DB config separately
    db_config = load_db_config()
    init_db_pool(db_config)

    # Register routes
    register_blueprints(app)

    return app


