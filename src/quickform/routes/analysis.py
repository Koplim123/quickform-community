import os
import threading
import logging
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from datetime import datetime

from ..models import SessionLocal, Task, Submission, AIConfig, AIModelConfig
from ..utils import read_file_content, generate_analysis_prompt, timeout
from ..ai_service import call_ai_model
from ..services import save_analysis_report

analysis_bp = Blueprint('analysis', __name__)
logger = logging.getLogger(__name__)


@analysis_bp.route('/smart_analyze/<int:task_id>', methods=['GET'])
@login_required
def smart_analyze(task_id):
    """
    智能分析页面 - 显示分析选项和数据统计
    """
    db = SessionLocal()
    try:
        # 检查用户是否拥有该任务
        task = db.query(Task).filter_by(id=task_id, user_id=current_user.id).first()
        if not task:
            flash('任务不存在', 'danger')
            return redirect(url_for('main.dashboard'))

        # 获取提交数据数量和列表
        submission = db.query(Submission).filter_by(task_id=task_id).all()
        submission_count = len(submission)

        # 检查是否有AI配置
        ai_config = db.query(AIConfig).filter_by(user_id=current_user.id).first()

        # 检查是否有APIKEY
        has_api_key = False
        if ai_config and ai_config.selected_model:
            model_cfg = db.query(AIModelConfig).filter_by(
                ai_config_id=ai_config.id,
                model_name=ai_config.selected_model
            ).first()
            if model_cfg:
                if model_cfg.api_key:
                    has_api_key = True
                elif model_cfg.api_url and ai_config.selected_model == 'ollama':
                    has_api_key = True

        # 读取附件内容（如果有）
        file_content = None
        if task.attachments:
            # 读取第一个附件的内容
            first_attachment = task.attachments[0]
            if os.path.exists(first_attachment.file_path):
                file_content = read_file_content(first_attachment.file_path)

        # 生成预览提示词
        preview_prompt = generate_analysis_prompt(task, submission, file_content)

        # 获取报告内容（如果存在）
        report = task.analysis_report if task and task.analysis_report else None

        return render_template('smart_analyze.html',
                             task=task,
                             report=report,
                             preview_prompt=preview_prompt,
                             submission_count=submission_count,
                             has_api_key=has_api_key,
                             now=datetime.now())
    finally:
        db.close()


@analysis_bp.route('/generate_report/<int:task_id>', methods=['GET', 'POST'])
@login_required
def generate_report(task_id):
    """
    在新页面中生成分析报告
    """
    # 添加详细的请求日志
    logger.info(f"收到生成报告请求 - Task ID: {task_id}, Method: {request.method}")
    logger.info(f"请求URL: {request.url}")
    logger.info(f"请求参数: {dict(request.args)}")
    logger.info(f"表单数据: {dict(request.form)}")
    logger.info(f"请求头: {dict(request.headers)}")

    db = SessionLocal()
    try:
        # 检查任务权限
        task = db.query(Task).filter_by(id=task_id, user_id=current_user.id).first()
        if not task:
            logger.warning(f"任务不存在或无权访问 - Task ID: {task_id}, User ID: {current_user.id}")
            return render_template('generate_report.html', error='任务不存在或无权访问')

        # 获取AI配置
        ai_config = db.query(AIConfig).filter_by(user_id=current_user.id).first()
        if not ai_config or not ai_config.selected_model:
            flash('请先在配置页面设置AI模型和API密钥', 'warning')
            return redirect(url_for('main.profile'))

        # 针对不同模型验证必需的API密钥
        if ai_config.selected_model == 'deepseek' and not ai_config.deepseek_api_key:
            flash('请先配置DeepSeek API密钥', 'warning')
            return redirect(url_for('main.profile'))
        elif ai_config.selected_model == 'doubao' and not ai_config.doubao_api_key:
            flash('请先配置豆包API密钥', 'warning')
            return redirect(url_for('main.profile'))
        elif ai_config.selected_model == 'qwen' and not ai_config.qwen_api_key:
            flash('请先配置阿里云百炼API密钥', 'warning')
            return redirect(url_for('main.profile'))

        # 获取提示词
        custom_prompt = None
        if request.method == 'GET' and 'prompt' in request.args:
            custom_prompt = request.args.get('prompt')
            logger.info(f"从GET参数获取提示词，长度: {len(custom_prompt) if custom_prompt else 0}")
        elif request.method == 'POST' and 'custom_prompt' in request.form:
            custom_prompt = request.form.get('custom_prompt')
            logger.info(f"从POST表单获取提示词，长度: {len(custom_prompt) if custom_prompt else 0}")

        # 如果没有提示词，生成默认提示词
        if not custom_prompt:
            logger.info("未提供自定义提示词，生成默认提示词")
            submission = db.query(Submission).filter_by(task_id=task_id).all()
            file_content = None
            if task.attachments:
                # 读取第一个附件的内容
                first_attachment = task.attachments[0]
                if os.path.exists(first_attachment.file_path):
                    file_content = read_file_content(first_attachment.file_path)
            custom_prompt = generate_analysis_prompt(task, submission, file_content)
            logger.info(f"生成默认提示词，长度: {len(custom_prompt) if custom_prompt else 0}")
        else:
            logger.info(f"使用自定义提示词，长度: {len(custom_prompt)}")

        # 验证提示词不为空
        if not custom_prompt or not custom_prompt.strip():
            logger.warning("提示词为空或只包含空白字符")
            return render_template('generate_report.html', task=task, error="提示词不能为空", ai_config=ai_config)

        logger.info(f"开始生成报告任务 {task_id}，使用模型 {ai_config.selected_model}")

        # 执行分析
        try:
            # 进度显示
            progress_message = "正在使用AI模型分析数据..."

            # 设置超时时间
            timeout_seconds = 120 if ai_config.selected_model == 'deepseek' else 90

            # 调用AI模型
            @timeout(seconds=timeout_seconds, error_message=f"调用{ai_config.selected_model}模型超时（{timeout_seconds}秒）")
            def call_ai_with_timeout(prompt, config):
                return call_ai_model(prompt, config)

            # 执行分析
            analysis_report = call_ai_with_timeout(custom_prompt, ai_config)

            # 保存报告
            save_analysis_report(task_id, analysis_report)

            # 成功显示报告
            return render_template('generate_report.html',
                                 task=task,
                                 report=analysis_report,
                                 preview_prompt=custom_prompt,
                                 ai_config=ai_config)

        except Exception as e:
            logger.error(f"生成报告失败: {str(e)}")
            return render_template('generate_report.html',
                                 task=task,
                                 error=f'生成报告失败: {str(e)}',
                                 preview_prompt=custom_prompt,
                                 ai_config=ai_config)

    except Exception as e:
        logger.error(f"访问生成报告页面失败: {str(e)}")
        flash('生成报告时出现错误', 'danger')
        return redirect(url_for('task.task_detail', task_id=task_id))
    finally:
        db.close()


@analysis_bp.route('/download_report/<int:task_id>')
@login_required
def download_report(task_id):
    """
    下载分析报告
    """
    db = SessionLocal()
    try:
        task = db.query(Task).get(task_id)
        if not task:
            flash('任务不存在', 'danger')
            return redirect(url_for('main.dashboard'))
        if task.user_id != current_user.id:
            flash('无权访问此任务', 'danger')
            return redirect(url_for('main.dashboard'))

        # 保存任务信息
        report_file_path = task.report_file_path
        task_title = task.title
        report_content = task.analysis_report

        # 如果有报告文件且存在，直接发送
        if report_file_path and os.path.exists(report_file_path):
            db.close()
            import re
            safe_title = re.sub(r'[^a-zA-Z0-9_一-龥]', '_', task_title)
            safe_filename = f"{safe_title}_分析报告.html"

            from flask import send_file
            try:
                return send_file(
                    report_file_path,
                    as_attachment=True,
                    download_name=safe_filename,
                    mimetype='text/html; charset=utf-8'
                )
            except TypeError:
                return send_file(
                    report_file_path,
                    as_attachment=True,
                    attachment_filename=safe_filename,
                    mimetype='text/html; charset=utf-8'
                )

        # 如果没有报告文件，但有数据库中的报告内容，直接生成HTML并下载
        if report_content and report_content.strip():
            import re
            from io import BytesIO
            from flask import send_file
            safe_title = re.sub(r'[^a-zA-Z0-9_一-龥]', '_', task_title)
            safe_filename = f"{safe_title}_分析报告.html"

            # 使用模板渲染HTML报告
            report_time = task.report_generated_at.strftime('%Y-%m-%d %H:%M:%S') if task.report_generated_at else '未知'
            html_content = render_template('simple_report.html',
                                         task_title=task_title,
                                         report_time=report_time,
                                         report_content=report_content)

            db.close()

            # 直接返回HTML内容作为下载
            html_bytes = html_content.encode('utf-8')
            return send_file(
                BytesIO(html_bytes),
                as_attachment=True,
                download_name=safe_filename,
                mimetype='text/html; charset=utf-8'
            )

        db.close()
        # 没有报告内容
        flash('该任务尚未生成分析报告，请先进行智能分析', 'info')
        return redirect(url_for('analysis.smart_analyze', task_id=task_id))

    except Exception as e:
        flash(f'下载报告时出错: {str(e)}', 'danger')
        return redirect(url_for('main.dashboard'))
    finally:
        if 'db' in locals() and db:
            db.close()
