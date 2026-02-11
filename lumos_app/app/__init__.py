from flask import Flask
from config import Config
from extensions import db, jwt, migrate
from .routes.testcases import testcases_bp
from .routes.testblocks import testblocks_bp
from .routes.testpacks import testpacks_bp
from .routes.testelements import testelements_bp
from .routes.test_configurations import configurations_bp
from .routes.testexecutions import executions_bp
from .routes.testreports import testreports_bp
from .routes.user_details import user_bp
from .routes.userstory import userstory_bp
from .routes.ut_cst import utcst_bp
import git
import os
import psycopg2
from psycopg2 import pool
import configparser

app = Flask(__name__)
