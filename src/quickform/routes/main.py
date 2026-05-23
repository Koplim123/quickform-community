from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from ..models import SessionLocal, Task, AIConfig, AIModelConfig, QFConfig, User
from ..config import logger

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('home.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    db = SessionLocal()
    try:
        tasks = db.query(Task).filter_by(user_id=current_user.id).order_by(Task.created_at.desc()).all()
        return render_template('dashboard.html', tasks=tasks)
    finally:
        db.close()


@main_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = SessionLocal()
    try:
        ai_config = db.query(AIConfig).filter_by(user_id=current_user.id).first()

        if request.method == 'POST':
            if 'selected_model' in request.form:
                selected_model = request.form.get('selected_model')

                if not ai_config:
                    ai_config = AIConfig(user_id=current_user.id, selected_model=selected_model)
                    db.add(ai_config)
                    db.flush()
                else:
                    ai_config.selected_model = selected_model

                db.query(AIModelConfig).filter_by(ai_config_id=ai_config.id).delete()

                model_configs = [
                    ('deepseek', request.form.get('deepseek_api_key', ''), '', ''),
                    ('doubao', request.form.get('doubao_api_key', ''), '', ''),
                    ('qwen', request.form.get('qwen_api_key', ''), '', ''),
                    ('glm', request.form.get('glm_api_key', ''), '', ''),
                    ('siliconflow', request.form.get('siliconflow_api_key', ''), '', request.form.get('siliconflow_model', 'Qwen/Qwen2.5-72B-Instruct')),
                    ('ollama', '', request.form.get('ollama_api_url', 'http://localhost:11434'), request.form.get('ollama_model', 'llama3.2')),
                    ('openai', request.form.get('openai_api_key', ''), request.form.get('openai_api_url', 'https://api.openai.com/v1'), request.form.get('openai_model', 'gpt-5.5')),
                ]

                for model_name, api_key, api_url, extra_settings in model_configs:
                    if api_key or api_url:
                        cfg = AIModelConfig(
                            ai_config_id=ai_config.id,
                            model_name=model_name,
                            api_key=api_key,
                            api_url=api_url,
                            extra_settings=extra_settings
                        )
                        db.add(cfg)

                db.commit()
                flash('AI配置更新成功', 'success')

            elif 'update_qf_config' in request.form:
                qf_username = request.form.get('qf_username', '').strip()
                qf_password = request.form.get('qf_password', '').strip()

                qf_config = db.query(QFConfig).filter_by(user_id=current_user.id).first()
                if not qf_config:
                    qf_config = QFConfig(user_id=current_user.id, username=qf_username, password=qf_password)
                    db.add(qf_config)
                else:
                    qf_config.username = qf_username
                    qf_config.password = qf_password

                db.commit()
                flash('QF配置更新成功', 'success')

            elif 'change_username' in request.form:
                new_username = request.form.get('username', '').strip()
                user = db.query(User).filter_by(id=current_user.id).first()
                if user and new_username:
                    user.username = new_username
                    db.commit()
                    flash('用户名修改成功', 'success')
                else:
                    flash('用户名修改失败', 'danger')

            elif 'change_password' in request.form:
                current_password = request.form.get('current_password')
                new_password = request.form.get('new_password')

                user = db.query(User).filter_by(id=current_user.id).first()
                if user and check_password_hash(user.password, current_password):
                    user.password = generate_password_hash(new_password)
                    db.commit()
                    flash('密码修改成功', 'success')
                else:
                    flash('当前密码错误', 'danger')

            active_tab = request.form.get('active_tab', 'config')
            return redirect(url_for('main.profile', active_tab=active_tab))

        model_configs_dict = {}
        if ai_config:
            for mc in ai_config.model_configs:
                model_configs_dict[mc.model_name] = mc

        qf_config = db.query(QFConfig).filter_by(user_id=current_user.id).first()

        return render_template('profile.html', user=current_user, ai_config=ai_config, model_configs_dict=model_configs_dict, qf_config=qf_config)
    finally:
        db.close()
