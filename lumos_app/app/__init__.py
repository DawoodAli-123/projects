from flask import Flask
from config import Config
from extensions import db, jwt, migrate
from .routes.auth import auth_bp
from .routes.user import user_bp
import git
import os
import psycopg2
from psycopg2 import pool
import configparser

app = Flask(__name__)
