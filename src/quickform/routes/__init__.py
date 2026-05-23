from .auth import auth_bp
from .main import main_bp
from .task import task_bp
from .import_task import import_bp
from .submission import submission_bp
from .api import api_bp
from .analysis import analysis_bp
from .export import export_bp


def register_routes(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(task_bp)
    app.register_blueprint(import_bp)
    app.register_blueprint(submission_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(export_bp)
