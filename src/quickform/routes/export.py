import os
import json
import io
import pandas as pd
from flask import Blueprint, render_template, redirect, url_for, request, flash, send_file
from flask_login import login_required, current_user
from datetime import datetime

from ..models import SessionLocal, Task, Submission

export_bp = Blueprint('export', __name__)


@export_bp.route('/export/<int:task_id>')
@login_required
def export_data(task_id):
    db = SessionLocal()
    try:
        task = db.query(Task).get(task_id)
        if not task or task.user_id != current_user.id:
            flash('无权访问此数据', 'danger')
            return redirect(url_for('main.dashboard'))

        submission = db.query(Submission).filter_by(task_id=task.id).all()

        if not submission:
            flash('没有可导出的数据', 'info')
            return redirect(url_for('task.task_detail', task_id=task_id))

        # 尝试解析提交数据并转换为DataFrame
        data_list = []
        for sub in submission:
            try:
                data = json.loads(sub.data)
                data['submitted_at'] = sub.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
                data_list.append(data)
            except:
                # 如果解析失败，添加原始数据
                data_list.append({
                    'submitted_at': sub.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'raw_data': sub.data
                })

        df = pd.DataFrame(data_list)

        # 创建CSV文件
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)

        # 发送文件（兼容不同版本的Flask）
        filename = f"{task.title}_数据导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            # 尝试使用新版本Flask的参数
            return send_file(output, download_name=filename, as_attachment=True, mimetype='text/csv; charset=utf-8')
        except TypeError:
            # 如果新参数不被支持，回退到旧版本的参数
            return send_file(output, attachment_filename=filename, as_attachment=True, mimetype='text/csv; charset=utf-8')
    except Exception as e:
        flash(f'导出数据时出错: {str(e)}', 'danger')
        return redirect(url_for('task.task_detail', task_id=task_id))
    finally:
        db.close()


@export_bp.route('/export_json/<int:task_id>')
@login_required
def export_json(task_id):
    """
    导出任务提交数据为JSON格式
    """
    db = SessionLocal()
    try:
        task = db.query(Task).get(task_id)
        if not task or task.user_id != current_user.id:
            flash('无权访问此数据', 'danger')
            return redirect(url_for('main.dashboard'))

        submission = db.query(Submission).filter_by(task_id=task.id).all()

        if not submission:
            flash('没有可导出的数据', 'info')
            return redirect(url_for('task.task_detail', task_id=task_id))

        # 构建JSON数据
        data_list = []
        for sub in submission:
            try:
                data = json.loads(sub.data)
                data['_submitted_at'] = sub.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
                data['_submission_id'] = sub.id
                data_list.append(data)
            except:
                # 如果解析失败，添加原始数据
                data_list.append({
                    '_submitted_at': sub.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
                    '_submission_id': sub.id,
                    '_raw_data': sub.data
                })

        # 创建JSON输出
        output = io.BytesIO()
        json_data = {
            'task_title': task.title,
            'task_id': task.id,
            'export_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_records': len(data_list),
            'data': data_list
        }
        output.write(json.dumps(json_data, ensure_ascii=False, indent=2).encode('utf-8'))
        output.seek(0)

        # 发送文件（兼容不同版本的Flask）
        filename = f"{task.title}_数据导出_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            # 尝试使用新版本Flask的参数
            return send_file(output, download_name=filename, as_attachment=True, mimetype='application/json; charset=utf-8')
        except TypeError:
            # 如果新参数不被支持，回退到旧版本的参数
            return send_file(output, attachment_filename=filename, as_attachment=True, mimetype='application/json; charset=utf-8')
    except Exception as e:
        flash(f'导出数据时出错: {str(e)}', 'danger')
        return redirect(url_for('task.task_detail', task_id=task_id))
    finally:
        db.close()
