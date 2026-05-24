from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash

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


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not username or not password:
            flash('用户名和密码不能为空', 'danger')
            return render_template('register.html')

        if len(username) < 2:
            flash('用户名至少需要2个字符', 'danger')
            return render_template('register.html')

        if len(password) < 4:
            flash('密码至少需要4个字符', 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'danger')
            return render_template('register.html')

        db = SessionLocal()
        try:
            existing = db.query(User).filter_by(username=username).first()
            if existing:
                flash('用户名已存在', 'danger')
                return render_template('register.html')

            user = User(
                username=username,
                email=f'{username}@local',
                password=generate_password_hash(password)
            )
            db.add(user)
            db.commit()

            login_user(user)
            flash('注册成功，欢迎使用 QuickForm！', 'success')
            return redirect(url_for('main.dashboard'))
        finally:
            db.close()

    return render_template('register.html')
