import os
import logging
from flask import Flask
from flask_login import LoginManager

from .config import SECRET_KEY, UPLOAD_FOLDER, APP_NAME
from .models import SessionLocal, User

logger = logging.getLogger(__name__)

login_manager = LoginManager()


def create_app():
    # 计算基础目录（src/），因为本文件在 src/quickform/__init__.py
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, 'templates'),
        static_folder=os.path.join(base_dir, 'static'),
        root_path=base_dir
    )

    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 限制
    app.config['JSON_AS_ASCII'] = False  # 确保JSON响应中的中文正确显示，不转义为Unicode

    # 初始化Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        db = SessionLocal()
        try:
            return db.query(User).get(int(user_id))
        finally:
            db.close()

    # 注册模板全局变量
    @app.template_global()
    def get_app_name():
        return APP_NAME

    # 注册蓝图
    from .routes import register_routes
    register_routes(app)

    # 创建必要的目录
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists('static/reports'):
        os.makedirs('static/reports')

    return app
