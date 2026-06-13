import os
import re
import json
import uuid
import requests
import logging
import io
import zipfile
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user

from ..models import SessionLocal, Task, Attachment, QFConfig
from ..models import generate_custom_id
from ..config import logger
from ..crypto import validate_url_safe, decrypt_value

import_bp = Blueprint('import_task', __name__)


@import_bp.route('/import_task', methods=['GET', 'POST'])
@login_required
def import_task():
    tasks = []
    error = None

    host = request.host.lower()
    if '127.0.0.1' in host or 'localhost' in host:
        flash('导入任务不能使用127.0.0.1的方式访问网站', 'danger')
        return render_template('import_task.html', tasks=[], error=None)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        try:
            session['quickform_username'] = username
            session['quickform_password'] = password

            url = 'https://quickform.cn/cli/list'
            data = {
                'username': username,
                'password': password
            }
            response = requests.post(url, data=data)
            response.raise_for_status()

            result = response.json()
            if result.get('success'):
                tasks = result.get('tasks', [])
            else:
                error = result.get('message', '获取任务列表失败')
        except Exception as e:
            error = f'请求失败: {str(e)}'
    else:
        tasks_param = request.args.get('tasks')
        if tasks_param:
            try:
                tasks = json.loads(tasks_param)
            except:
                tasks = []

    return render_template('import_task.html', tasks=tasks, error=error)


@import_bp.route('/import_task_action/<string:apiid>')
@login_required
def import_task_action(apiid):
    import requests
    import re
    import os
    import uuid
    from flask import current_app

    task_name = request.args.get('task_name', '导入的任务')

    host = request.host.lower()
    if '127.0.0.1' in host or 'localhost' in host:
        flash('导入任务不能使用127.0.0.1的方式访问网站', 'danger')
        return redirect(url_for('import_task.import_task'))

    db = SessionLocal()
    try:
        quickform_username = session.get('quickform_username')
        quickform_password = session.get('quickform_password')

        if not quickform_username or not quickform_password:
            qf_config = db.query(QFConfig).filter_by(user_id=current_user.id).first()
            if qf_config and qf_config.username and qf_config.password:
                quickform_username = qf_config.username
                quickform_password = decrypt_value(qf_config.password)
            else:
                flash('请先获取任务列表以验证quickform.cn账号', 'danger')
                return redirect(url_for('import_task.import_task'))

        quickform_url = 'https://quickform.cn'
        show_data = {
            'username': quickform_username,
            'password': quickform_password,
            'apiid': apiid
        }

        try:
            response = requests.post(
                f'{quickform_url}/cli/show',
                data=show_data,
                timeout=30,
                allow_redirects=True
            )
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"CLI show response status: {response.status_code}")
            logger.info(f"CLI show response headers: {dict(response.headers)}")
            logger.info(f"CLI show response text: {response.text[:500] if response.text else 'empty'}")

            if response.status_code != 200:
                flash(f'获取任务信息失败: HTTP {response.status_code}', 'danger')
                return redirect(url_for('import_task.import_task'))

            task_info = response.json()
        except json.JSONDecodeError as e:
            flash(f'获取任务信息失败: 响应格式错误', 'danger')
            return redirect(url_for('import_task.import_task'))
        except Exception as e:
            flash(f'获取任务信息失败: {str(e)}', 'danger')
            return redirect(url_for('import_task.import_task'))

        if not task_info.get('success'):
            flash(f'获取任务信息失败: {task_info.get("message", "未知错误")}', 'danger')
            return redirect(url_for('import_task.import_task'))

        task_title = task_info.get('name', task_name)
        task_intro = task_info.get('intro', '')
        tutorial_link = task_info.get('tutorial', '')
        share_url = task_info.get('share_url', '')
        attachments_info = task_info.get('attachments', [])

        existing_task = db.query(Task).filter_by(task_id=apiid).first()
        if existing_task:
            new_api_id = generate_custom_id()
            flash(f'API {apiid} 已存在，已生成新API: {new_api_id}', 'info')
        else:
            new_api_id = apiid

        new_task = Task(
            title=task_title,
            description=task_intro,
            user_id=current_user.id,
            task_id=new_api_id
        )
        db.add(new_task)
        db.flush()

        for attachment in attachments_info:
            attachment_name = attachment.get('name', '')
            attachment_url = attachment.get('url', '')

            if not attachment_url or not attachment_name.endswith('.html'):
                continue

            try:
                validate_url_safe(attachment_url)
                html_response = requests.get(attachment_url, timeout=30)
                html_content = html_response.text

                pattern = rf'https?://quickform\.cn/api/([a-zA-Z0-9]+)'
                new_api_pattern = request.host_url.rstrip('/') + '/api/' + new_api_id
                modified_html = re.sub(pattern, new_api_pattern, html_content)

                unique_filename = f"{uuid.uuid4().hex}_{attachment_name}"
                uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(uploads_dir, exist_ok=True)
                file_path = os.path.join(uploads_dir, unique_filename)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_html)

                relative_path = f'uploads/{unique_filename}'

                db_attachment = Attachment(
                    task_id=new_task.id,
                    file_name=attachment_name,
                    file_path=relative_path
                )
                db.add(db_attachment)
            except Exception as e:
                flash(f'下载附件 {attachment_name} 失败: {str(e)}', 'warning')

        db.commit()
        flash(f'任务"{task_title}"导入成功，API ID: {new_api_id}', 'success')
        return redirect(url_for('task.task_detail', task_id=new_task.id))
    except Exception as e:
        flash(f'任务导入失败: {str(e)}', 'danger')
        return redirect(url_for('import_task.import_task'))
    finally:
        db.close()


@import_bp.route('/import_task_by_url')
@login_required
def import_task_by_url():
    host = request.host.lower()
    if '127.0.0.1' in host or 'localhost' in host:
        flash('导入任务不能使用127.0.0.1的方式访问网站', 'danger')
        return redirect(url_for('import_task.import_task'))

    task_url = request.args.get('url', '')

    match = re.search(r'/api/([a-zA-Z0-9]+)', task_url)
    if not match:
        flash('无效的任务URL格式', 'danger')
        return redirect(url_for('import_task.import_task'))

    apiid = match.group(1)

    return redirect(url_for('import_task.import_task_action', apiid=apiid, task_name=f'任务{apiid}'))


@import_bp.route('/import_task_from_file', methods=['POST'])
@login_required
def import_task_from_file():
    import zipfile
    import io
    import re
    import os
    import logging
    from flask import current_app

    logger = logging.getLogger(__name__)
    logger.info(f"Request files: {request.files}")
    logger.info(f"Request form: {request.form}")

    if 'task_file' not in request.files:
        flash('没有文件上传', 'danger')
        return redirect(url_for('import_task.import_task'))

    file = request.files['task_file']
    if file.filename == '':
        flash('没有选择文件', 'danger')
        return redirect(url_for('import_task.import_task'))

    host = request.host.lower()
    if '127.0.0.1' in host or 'localhost' in host:
        flash('导入任务不能使用127.0.0.1的方式访问网站', 'danger')
        return redirect(url_for('import_task.import_task'))

    try:
        zip_bytes = file.read()
        zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))

        json_content = zip_file.read('quickform-task-migration.json').decode('utf-8')
        import json
        task_data = json.loads(json_content)

        original_api_id = task_data.get('api_id', '')
        title = task_data.get('title', '未命名任务')
        description = task_data.get('description', '')
        html_files = task_data.get('html_files', [])
        export_api_base = task_data.get('export_api_base', 'https://quickform.cn')

        db = SessionLocal()
        try:
            existing_task = db.query(Task).filter_by(task_id=original_api_id).first()

            if existing_task:
                new_api_id = generate_custom_id()
                flash(f'API {original_api_id} 已存在，已生成新API: {new_api_id}', 'info')
            else:
                new_api_id = original_api_id

            new_task = Task(
                title=title,
                description=description,
                user_id=current_user.id,
                task_id=new_api_id
            )
            db.add(new_task)
            db.flush()

            for html_file_info in html_files:
                archive_name = html_file_info.get('archive_name', '')
                original_name = html_file_info.get('original_name', '')

                if archive_name and archive_name in zip_file.namelist():
                    html_content = zip_file.read(archive_name).decode('utf-8')

                    export_api_base = task_data.get('export_api_base', 'https://quickform.cn').rstrip('/')
                    new_api_pattern = request.host_url.rstrip('/') + '/api/' + new_api_id
                    pattern = rf'https?://quickform\.cn/api/([a-zA-Z0-9]+)'
                    modified_html = re.sub(pattern, new_api_pattern, html_content)

                    unique_filename = f"{uuid.uuid4().hex}_{original_name}"
                    uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
                    os.makedirs(uploads_dir, exist_ok=True)
                    file_path = os.path.join(uploads_dir, unique_filename)

                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(modified_html)

                    relative_path = f'uploads/{unique_filename}'

                    attachment = Attachment(
                        task_id=new_task.id,
                        file_name=original_name,
                        file_path=relative_path
                    )
                    db.add(attachment)

            db.commit()
            flash(f'任务"{title}"导入成功，API ID: {new_api_id}', 'success')
            return redirect(url_for('task.task_detail', task_id=new_task.id))
        finally:
            db.close()
    except zipfile.BadZipFile:
        flash('无效的压缩包文件', 'danger')
    except KeyError as e:
        flash(f'压缩包内缺少必要文件: {str(e)}', 'danger')
    except Exception as e:
        flash(f'导入失败: {str(e)}', 'danger')

    return redirect(url_for('import_task.import_task'))
