import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user

from ..models import SessionLocal, Task, Attachment, Submission
from ..utils import save_uploaded_file, read_file_content
from ..config import logger

task_bp = Blueprint('task', __name__)


@task_bp.route('/create_task', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')

        db = SessionLocal()
        try:
            task = Task(title=title, description=description, user_id=current_user.id)
            db.add(task)
            db.commit()

            # 处理多附件上传
            # 支持file、file_2、file_3等多个文件字段
            file_fields = ['file', 'file_2', 'file_3']
            for field_name in file_fields:
                if field_name in request.files and request.files[field_name].filename != '':
                    file = request.files[field_name]
                    unique_filename, filepath = save_uploaded_file(file)
                    if unique_filename:
                        attachment = Attachment(
                            task_id=task.id,
                            file_name=file.filename,
                            file_path=filepath
                        )
                        db.add(attachment)

            db.commit()

            flash('数据任务创建成功', 'success')
            return redirect(url_for('task.task_detail', task_id=task.id))
        finally:
            db.close()
    return render_template('create_task.html')


@task_bp.route('/task/<int:task_id>')
@login_required
def task_detail(task_id):
    db = SessionLocal()
    try:
        task = db.query(Task).get(task_id)
        if not task:
            flash('任务不存在', 'danger')
            return redirect(url_for('main.dashboard'))
        if task.user_id != current_user.id:
            flash('无权访问此任务', 'danger')
            return redirect(url_for('main.dashboard'))

        submission = db.query(Submission).filter_by(task_id=task.id).order_by(Submission.submitted_at.desc()).all()
        return render_template('task_detail.html', task=task, submission=submission)
    finally:
        db.close()


@task_bp.route('/task/<int:task_id>/data')
@login_required
def task_data_view(task_id):
    db = SessionLocal()
    try:
        task = db.query(Task).get(task_id)
        if not task:
            flash('任务不存在', 'danger')
            return redirect(url_for('main.dashboard'))
        if task.user_id != current_user.id:
            flash('无权访问此任务', 'danger')
            return redirect(url_for('main.dashboard'))

        submission = db.query(Submission).filter_by(task_id=task.id).order_by(Submission.submitted_at.desc()).all()

        class SimplePagination:
            def __init__(self, page, per_page, total):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = 1

        total_submissions = len(submission)
        pagination = SimplePagination(1, 10, total_submissions)

        return render_template('task_data_view.html', task=task, submissions=submission, total_submissions=total_submissions, pagination=pagination)
    finally:
        db.close()


@task_bp.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    db = SessionLocal()
    try:
        task = db.query(Task).get(task_id)
        if not task:
            flash('任务不存在', 'danger')
            return redirect(url_for('main.dashboard'))
        if task.user_id != current_user.id:
            flash('无权编辑此任务', 'danger')
            return redirect(url_for('main.dashboard'))

        if request.method == 'POST':
            title = request.form.get('title')
            description = request.form.get('description')

            # 更新任务信息
            task.title = title
            task.description = description

            # 处理删除附件
            remove_attachments = request.form.getlist('remove_attachments')
            for attachment_id in remove_attachments:
                attachment = db.query(Attachment).get(int(attachment_id))
                if attachment and attachment.task_id == task.id:
                    # 删除物理文件
                    if os.path.exists(attachment.file_path):
                        os.remove(attachment.file_path)
                    db.delete(attachment)

            # 处理新附件上传
            # 支持file、file_2、file_3等多个文件字段
            file_fields = ['file', 'file_2', 'file_3']
            for field_name in file_fields:
                if field_name in request.files and request.files[field_name].filename != '':
                    file = request.files[field_name]
                    unique_filename, filepath = save_uploaded_file(file)
                    if unique_filename:
                        attachment = Attachment(
                            task_id=task.id,
                            file_name=file.filename,
                            file_path=filepath
                        )
                        db.add(attachment)

            db.commit()
            flash('任务更新成功', 'success')
            return redirect(url_for('task.task_detail', task_id=task.id))

        return render_template('edit_task.html', task=task)
    finally:
        db.close()


@task_bp.route('/task/<int:task_id>/upload', methods=['POST'])
@login_required
def upload_task_attachment(task_id):
    db = SessionLocal()
    try:
        task = db.query(Task).get(task_id)
        if not task:
            return jsonify({'success': False, 'message': '任务不存在'})
        if task.user_id != current_user.id:
            return jsonify({'success': False, 'message': '无权访问此任务'})

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有文件'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})

        unique_filename, filepath = save_uploaded_file(file)
        if unique_filename:
            attachment = Attachment(
                task_id=task.id,
                file_name=file.filename,
                file_path=filepath
            )
            db.add(attachment)
            db.commit()
            return jsonify({'success': True, 'message': '文件上传成功'})
        else:
            return jsonify({'success': False, 'message': '文件保存失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        db.close()


@task_bp.route('/delete_task/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    import os
    from flask import current_app
    db = SessionLocal()
    try:
        task = db.query(Task).get(task_id)
        if not task:
            flash('任务不存在', 'danger')
            return redirect(url_for('main.dashboard'))
        if task.user_id != current_user.id:
            flash('无权删除此任务', 'danger')
            return redirect(url_for('main.dashboard'))

        attachments = db.query(Attachment).filter_by(task_id=task.id).all()
        for attachment in attachments:
            file_path = os.path.join(current_app.root_path, 'static', attachment.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.delete(task)
        db.commit()
        flash('任务已删除', 'success')
        return redirect(url_for('main.dashboard'))
    finally:
        db.close()


@task_bp.route('/delete_attachment/<int:attachment_id>', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    import os
    db = SessionLocal()
    try:
        attachment = db.query(Attachment).get(attachment_id)
        if not attachment:
            return jsonify({'success': False, 'message': '附件不存在'})

        task = db.query(Task).get(attachment.task_id)
        if not task or task.user_id != current_user.id:
            return jsonify({'success': False, 'message': '无权删除此附件'})

        file_path = attachment.file_path
        if os.path.exists(file_path):
            os.remove(file_path)

        db.delete(attachment)
        db.commit()
        return jsonify({'success': True, 'message': '删除成功'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        db.close()
