import json
import os
import queue
import requests
import logging
from flask import Blueprint, request, jsonify, make_response, redirect, url_for, Response
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash

from ..models import SessionLocal, Task, Submission, AIConfig, AIModelConfig, QFConfig, User, Attachment
from ..config import logger
from ..crypto import decrypt_value
from ..ai_service import call_ai_model
from ..sse import publish, subscribe, unregister

api_bp = Blueprint('api', __name__)


@api_bp.route('/test_api_key', methods=['POST', 'OPTIONS'])
@login_required
def test_api_key():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    try:
        data = request.get_json()
        model = data.get('model')
        api_key = data.get('api_key', '')
        api_url = data.get('api_url', '')
        model_name = data.get('model_name', '')

        if not model:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400

        class TestModelConfig:
            def __init__(self, model_name, api_key, api_url, extra_settings):
                self.model_name = model_name
                self.api_key = api_key
                self.api_url = api_url
                self.extra_settings = extra_settings

        class TestAIConfig:
            def __init__(self, model, api_key, api_url, model_name):
                self.selected_model = model
                self.model_configs = [TestModelConfig(model, api_key, api_url, model_name or ('llama3.2' if model == 'ollama' else ''))]

        test_config = TestAIConfig(model, api_key, api_url, model_name)

        test_prompt = '这是一个API密钥测试，请回复"测试成功"'

        result = call_ai_model(test_prompt, test_config)

        if result and ('测试成功' in result or 'success' in result.lower()):
            return jsonify({'success': True, 'message': 'API密钥有效'}), 200
        else:
            return jsonify({'success': True, 'message': 'API密钥有效，但返回内容不符合预期'}), 200

    except Exception as e:
        logger.error(f"API密钥测试失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/api/<string:task_id>/all', methods=['GET', 'OPTIONS'])
def get_all_submissions(task_id):
    # 永久重定向到/api/<string:task_id>路由
    return redirect(url_for('api.submit_form', task_id=task_id), code=301)


@api_bp.route('/api/<string:task_id>', methods=['GET', 'POST', 'OPTIONS'])
def submit_form(task_id):
    # 处理预检请求
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    db = SessionLocal()
    try:
        task = db.query(Task).filter_by(task_id=task_id).first()
        if not task:
            response = jsonify({'error': '任务不存在'})
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 404

        if request.method == 'GET':
            # 返回所有回收的数据
            submissions = db.query(Submission).filter_by(task_id=task.id).all()
            all_data = []
            for sub in submissions:
                try:
                    data = json.loads(sub.data)
                except:
                    data = sub.data
                all_data.append({
                    'data': data,
                    'id': sub.id,
                    'submitted_at': sub.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            # 直接构建JSON字符串以确保键的顺序
            submission_count = len(all_data)
            response_data = {
                'note': f'Total {submission_count} submission(s).',
                'submissions': all_data,
                'task_id': task_id,
                'task_title': task.title,
                'total_submissions': submission_count
            }
            # 使用json.dumps确保键的顺序
            json_response = json.dumps(response_data, ensure_ascii=False, sort_keys=False)
            response = make_response(json_response)
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response, 200

        # 处理POST请求 - 回收数据
        form_data = {}

        # 检查Content-Type并选择合适的数据获取方式
        if request.is_json:
            # 如果是JSON请求，尝试获取JSON数据
            try:
                form_data = request.get_json() or {}
            except Exception as e:
                logger.error(f"解析JSON数据失败: {str(e)}")
                form_data = {}
        else:
            # 如果不是JSON请求，获取表单数据
            form_data = request.form.to_dict()

        # 如果表单数据仍然为空，尝试从请求体获取原始数据并解析为dict
        if not form_data:
            try:
                raw = request.get_data(as_text=True)
                try:
                    form_data = json.loads(raw)
                except:
                    form_data = {'raw': raw}
            except Exception as e:
                logger.error(f"获取请求体数据失败: {str(e)}")
                form_data = {}

        submission = Submission(task_id=task.id, data=json.dumps(form_data, ensure_ascii=False))
        db.add(submission)
        db.commit()

        publish(task.id, {
            'type': 'new_submission',
            'id': submission.id,
            'data': form_data,
            'submitted_at': submission.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
        })

        response = jsonify({'message': '提交成功'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 200
    finally:
        db.close()


@api_bp.route('/api/qf/test_connection', methods=['POST'])
@login_required
def test_qf_connection():
    import requests
    db = SessionLocal()
    try:
        qf_config = db.query(QFConfig).filter_by(user_id=current_user.id).first()
        if not qf_config or not qf_config.username or not qf_config.password:
            return jsonify({'success': False, 'message': '请先保存用户名和密码'})

        try:
            response = requests.post(
                'https://quickform.cn/cli/list',
                json={'username': qf_config.username, 'password': decrypt_value(qf_config.password)},
                timeout=10
            )
            result = response.json()
            if result.get('success'):
                return jsonify({'success': True, 'message': '连接成功', 'tasks': result.get('tasks', [])})
            else:
                return jsonify({'success': False, 'message': result.get('message', '认证失败')})
        except Exception as e:
            return jsonify({'success': False, 'message': f'连接失败: {str(e)}'})
    finally:
        db.close()


@api_bp.route('/api/qf/list', methods=['GET'])
@login_required
def get_qf_task_list():
    import requests
    db = SessionLocal()
    try:
        qf_config = db.query(QFConfig).filter_by(user_id=current_user.id).first()
        if not qf_config or not qf_config.username or not qf_config.password:
            return jsonify({'success': False, 'message': '请先在设置中配置QF数据互联'})

        try:
            response = requests.post(
                'https://quickform.cn/cli/list',
                json={'username': qf_config.username, 'password': decrypt_value(qf_config.password)},
                timeout=10
            )
            result = response.json()
            if result.get('success'):
                return jsonify({'success': True, 'tasks': result.get('tasks', [])})
            else:
                return jsonify({'success': False, 'message': result.get('message', '认证失败')})
        except Exception as e:
            return jsonify({'success': False, 'message': f'连接失败: {str(e)}'})
    finally:
        db.close()


@api_bp.route('/api/system/init', methods=['POST'])
@login_required
def system_init():
    import os
    db = SessionLocal()
    try:
        try:
            ai_config = db.query(AIConfig).filter_by(user_id=current_user.id).first()
            if ai_config:
                db.query(AIModelConfig).filter(
                    AIModelConfig.ai_config_id == ai_config.id,
                    AIModelConfig.model_name != 'ollama'
                ).delete(synchronize_session=False)
                ollama_cfg = db.query(AIModelConfig).filter(
                    AIModelConfig.ai_config_id == ai_config.id,
                    AIModelConfig.model_name == 'ollama'
                ).first()
                if ollama_cfg:
                    ollama_cfg.api_key = ''
                if not ollama_cfg:
                    ollama_cfg = AIModelConfig(
                        ai_config_id=ai_config.id,
                        model_name='ollama',
                        api_key='',
                        api_url='http://localhost:11434',
                        extra_settings='llama3'
                    )
                    db.add(ollama_cfg)

            qf_configs = db.query(QFConfig).filter_by(user_id=current_user.id).all()
            for qf in qf_configs:
                db.delete(qf)

            user = db.query(User).filter_by(id=current_user.id).first()
            if user:
                user.username = 'wst'
                user.password = generate_password_hash('quickform')

            all_tasks = db.query(Task).filter_by(user_id=current_user.id).order_by(Task.id).all()
            tasks_to_delete = all_tasks[3:] if len(all_tasks) > 3 else []

            for task in tasks_to_delete:
                attachments = db.query(Attachment).filter_by(task_id=task.id).all()
                for att in attachments:
                    if os.path.exists(att.file_path):
                        os.remove(att.file_path)
                    db.delete(att)
                db.delete(task)

            db.commit()
            return jsonify({'success': True, 'message': '系统初始化成功'})
        except Exception as e:
            db.rollback()
            return jsonify({'success': False, 'message': f'初始化失败: {str(e)}'})
    finally:
        db.close()


@api_bp.route('/api/<string:task_id>/stream')
def sse_stream(task_id):
    """SSE 实时推送端点 - 连接时推送全量数据，之后实时推送新数据"""
    db = SessionLocal()
    try:
        task = db.query(Task).filter_by(task_id=task_id).first()
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        internal_task_id = task.id
        task_title = task.title

        # 读取全量数据快照
        submissions = db.query(Submission).filter_by(task_id=task.id).all()
        snapshot = []
        for sub in submissions:
            try:
                data = json.loads(sub.data)
            except:
                data = sub.data
            snapshot.append({
                'id': sub.id,
                'data': data,
                'submitted_at': sub.submitted_at.strftime('%Y-%m-%d %H:%M:%S')
            })
    finally:
        db.close()

    def generate():
        # 连接建立时先推送全量快照
        yield f"data: {json.dumps({'type': 'snapshot', 'task_id': task_id, 'task_title': task_title, 'total_submissions': len(snapshot), 'submissions': snapshot}, ensure_ascii=False)}\n\n"

        sse_id, q = subscribe(internal_task_id)
        try:
            while True:
                try:
                    data = q.get(timeout=15)
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    yield ":heartbeat\n\n"
        except GeneratorExit:
            pass
        finally:
            unregister(sse_id, internal_task_id)

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no',
                             'Access-Control-Allow-Origin': '*'})
