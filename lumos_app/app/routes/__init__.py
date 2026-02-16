from .testcases import testcases_bp
from .testblocks import testblocks_bp
from .testpacks import testpacks_bp
from .testelements import testelements_bp
from .test_configurations import configurations_bp
from .testexecutions import executions_bp
from .testreports import testreports_bp
from .user_details import user_bp
from .userstory import userstory_bp
from .ut_cst import utcst_bp
from .reports import reports_bp

def register_blueprints(app):
    app.register_blueprint(testcases_bp, url_prefix="/testcases")
    app.register_blueprint(testblocks_bp, url_prefix="/testblocks")
    app.register_blueprint(testpacks_bp, url_prefix="/testpacks")
    app.register_blueprint(testelements_bp, url_prefix="/testelements")
    app.register_blueprint(configurations_bp, url_prefix="/configurations")
    app.register_blueprint(executions_bp, url_prefix="/executions")
    app.register_blueprint(testreports_bp, url_prefix="/testreports")
    app.register_blueprint(user_bp, url_prefix="/users")
    app.register_blueprint(userstory_bp, url_prefix="/user-stories")
    app.register_blueprint(utcst_bp, url_prefix="/ut-cst")
    app.register_bleprint(reports_bp, url_prifix="/reports")
