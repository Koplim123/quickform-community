from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash

from ..models import SessionLocal, User
from ..config import logger

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = SessionLocal()
        try:
            user = db.query(User).filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                login_user(user)

                if password == 'quickform':
                    flash('请修改您的默认密码', 'warning')
                    return redirect(url_for('main.profile'))

                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
            else:
                flash('用户名或密码错误', 'danger')
        finally:
            db.close()

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
