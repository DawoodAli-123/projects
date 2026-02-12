from flask import Flask
from .routes import register_blueprints
from .config import load_db_config
from .extensions import init_db_pool


def create_app():
    app = Flask(__name__)

    # Load DB config
    db_config = load_db_config()

    # Initialize connection pool
    init_db_pool(db_config)

    # Register routes
    register_blueprints(app)

    return app


