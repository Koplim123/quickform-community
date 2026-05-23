from flask import Blueprint, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user

from ..models import SessionLocal, Task, Submission

submission_bp = Blueprint('submission', __name__)


@submission_bp.route('/delete_submission/<int:submission_id>', methods=['POST', 'GET'])
@login_required
def delete_submission(submission_id):
    """删除单个提交数据"""
    db = SessionLocal()
    try:
        submission = db.query(Submission).get(submission_id)
        if not submission:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': '提交数据不存在'})
            flash('提交数据不存在', 'danger')
            return redirect(url_for('main.dashboard'))

        task = db.query(Task).get(submission.task_id)
        if not task:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': '任务不存在'})
            flash('任务不存在', 'danger')
            return redirect(url_for('main.dashboard'))

        if task.user_id != current_user.id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': '无权删除此提交数据'})
            flash('无权删除此提交数据', 'danger')
            return redirect(url_for('main.dashboard'))

        db.delete(submission)
        db.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': '提交数据已删除'})

        flash('提交数据已删除', 'success')
        return redirect(url_for('task.task_data_view', task_id=task.id))
    finally:
        db.close()


@submission_bp.route('/clear_all_submissions/<int:task_id>', methods=['GET'])
@login_required
def clear_all_submissions(task_id):
    """清空所有提交数据"""
    db = SessionLocal()
    try:
        task = db.query(Task).get(task_id)
        if not task:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': '任务不存在'})
            flash('任务不存在', 'danger')
            return redirect(url_for('main.dashboard'))

        if task.user_id != current_user.id:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': '无权删除此任务数据'})
            flash('无权删除此任务数据', 'danger')
            return redirect(url_for('main.dashboard'))

        db.query(Submission).filter_by(task_id=task.id).delete()
        db.commit()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'message': '已清空所有提交数据'})

        flash('已清空所有提交数据', 'success')
        return redirect(url_for('task.task_data_view', task_id=task.id))
    finally:
        db.close()


@submission_bp.route('/delete_multiple_submissions/<int:task_id>', methods=['POST'])
@login_required
def delete_multiple_submissions(task_id):
    """批量删除提交数据"""
    db = SessionLocal()
    try:
        # 查询任务
        task = db.query(Task).get(task_id)
        if not task:
            flash('任务不存在', 'danger')
            return redirect(url_for('main.dashboard'))

        # 检查用户权限
        if task.user_id != current_user.id:
            flash('无权删除此任务的提交数据', 'danger')
            return redirect(url_for('main.dashboard'))

        # 获取要删除的提交数据ID列表
        submission_ids = request.form.getlist('submission_ids')
        if not submission_ids:
            flash('请选择要删除的提交数据', 'warning')
            return redirect(url_for('task.task_detail', task_id=task_id))

        # 转换为整数并过滤
        submission_ids = [int(sid) for sid in submission_ids if sid.isdigit()]

        # 查询这些提交数据
        submissions = db.query(Submission).filter(
            Submission.id.in_(submission_ids),
            Submission.task_id == task_id
        ).all()

        # 检查是否所有提交数据都属于当前用户
        for sub in submissions:
            if sub.task.user_id != current_user.id:
                flash('无权删除部分提交数据', 'danger')
                return redirect(url_for('task.task_detail', task_id=task_id))

        # 删除提交数据
        for submission in submissions:
            db.delete(submission)

        db.commit()
        flash(f'已删除 {len(submissions)} 条提交数据', 'success')
        return redirect(url_for('task.task_detail', task_id=task_id))
    except ValueError:
        flash('无效的提交数据ID', 'danger')
        return redirect(url_for('task.task_detail', task_id=task_id))
    finally:
        db.close()
