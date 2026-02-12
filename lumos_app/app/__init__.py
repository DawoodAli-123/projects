from flask import Flask
from config import Config
from extensions import db, jwt, migrate
from routes import register_blueprints
import git
import os
import psycopg2
from psycopg2 import pool

def create_app(config_class=Config):
    app = Flask(__name__)

    # Load config
    app.config.from_object(config_class)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    register_blueprints(app)

    return app


