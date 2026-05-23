import os
import json
import threading
import traceback
import logging
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

from .models import SessionLocal, Task, Submission, AIConfig
from .utils import read_file_content, timeout
from .ai_service import call_ai_model

logger = logging.getLogger(__name__)

# 用于存储分析任务进度的字典（在生产环境中应使用Redis等）
analysis_progress = {}
analysis_results = {}
# 用于跟踪已成功生成报告的任务ID，避免重复生成
completed_reports = set()
# 线程锁，确保对共享数据的安全访问
progress_lock = threading.Lock()

# 创建Jinja2环境用于后台线程渲染模板
_template_env = None


def get_template_env():
    """获取Jinja2模板环境（延迟初始化）"""
    global _template_env
    if _template_env is None:
        # 模板目录在 src/templates/
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
        _template_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(['html', 'xml'])
        )
    return _template_env


def save_analysis_report(task_id, report_content):
    """
    保存分析报告到文件系统和数据库
    """
    db = SessionLocal()
    try:
        task = db.query(Task).filter_by(id=task_id).first()
        if task:
            # 检查报告内容是否为空或只包含空白字符
            if not report_content or not report_content.strip():
                # 如果报告内容为空，生成友好的提示内容
                report_content = "本次分析未能生成有效内容。可能是由于以下原因：\n\n- 提交的数据量不足\n- 数据质量问题\n- AI模型处理异常\n\n请尝试提交更多数据或修改提示词后重新分析。"

            # 使用模板生成HTML报告内容
            template = get_template_env().get_template('simple_report.html')
            html_report = template.render(
                task_title=task.title,
                report_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                report_content=report_content
            )

            # 保存HTML报告到文件
            report_dir = 'static/reports'
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)

            report_filename = f"report_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            report_path = os.path.join(report_dir, report_filename)

            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(html_report)

            # 更新数据库中的报告信息
            task.analysis_report = report_content
            task.report_file_path = report_path
            task.report_generated_at = datetime.now()
            db.commit()

            # 添加到已完成报告集合
            with progress_lock:
                completed_reports.add(task_id)

            logger.info(f"任务 {task_id} 的分析报告已保存")
    except Exception as e:
        logger.error(f"保存分析报告失败: {str(e)}")
    finally:
        db.close()


def perform_analysis_with_custom_prompt(task_id, user_id, ai_config_id, custom_prompt):
    """
    使用自定义提示词执行分析任务
    """
    db = SessionLocal()
    try:
        # 获取任务信息
        task = db.query(Task).filter_by(id=task_id, user_id=user_id).first()
        if not task:
            with progress_lock:
                analysis_progress[task_id] = {
                    'status': 'error',
                    'message': '任务不存在'
                }
            return

        # 获取提交数据
        submission = db.query(Submission).filter_by(task_id=task_id).all()

        # 读取附件内容（如果有）
        file_content = None
        if task.attachments:
            # 读取第一个附件的内容
            first_attachment = task.attachments[0]
            if os.path.exists(first_attachment.file_path):
                file_content = read_file_content(first_attachment.file_path)

        # 获取AI配置
        ai_config = db.query(AIConfig).filter_by(id=ai_config_id).first()
        if not ai_config:
            with progress_lock:
                analysis_progress[task_id] = {
                    'status': 'error',
                    'message': 'AI配置不存在'
                }
            return

        # 验证AI配置是否正确
        if ai_config.selected_model == 'deepseek' and not ai_config.deepseek_api_key:
            with progress_lock:
                analysis_progress[task_id] = {
                    'status': 'error',
                    'message': 'DeepSeek API密钥未配置'
                }
            logging.error(f"任务 {task_id}：DeepSeek API密钥未配置")
            return
        elif ai_config.selected_model == 'doubao' and not ai_config.doubao_api_key:
            with progress_lock:
                analysis_progress[task_id] = {
                    'status': 'error',
                    'message': '豆包API密钥未配置完整'
                }
            logging.error(f"任务 {task_id}：豆包API密钥未配置完整")
            return

        logging.info(f"任务 {task_id}：使用模型 {ai_config.selected_model}")

        # 进度1：正在生成提示词
        with progress_lock:
            analysis_progress[task_id] = {
                'status': 'in_progress',
                'progress': 0,
                'message': '正在生成提示词...'
            }

        # 生成分析提示词
        prompt = custom_prompt

        # 进度2：大模型分析中
        with progress_lock:
            analysis_progress[task_id] = {
                'status': 'in_progress',
                'progress': 1,
                'message': '大模型分析中，这可能需要几分钟时间...'
            }
        logging.info(f"任务 {task_id}：调用AI模型进行分析")

        # 设置AI调用的超时时间，根据模型类型调整
        timeout_seconds = 120 if ai_config.selected_model == 'deepseek' else (120 if ai_config.selected_model == 'qwen' else 90)

        # 带超时的AI模型调用
        @timeout(seconds=timeout_seconds, error_message=f"调用{ai_config.selected_model}模型超时（{timeout_seconds}秒）")
        def call_ai_with_timeout(prompt, config):
            logging.info(f"开始调用 {config.selected_model} API，提示词长度: {len(prompt)} 字符，超时设置: {timeout_seconds}秒")
            return call_ai_model(prompt, config)

        # 调用AI模型
        try:
            analysis_report = call_ai_with_timeout(prompt, ai_config)
            logging.info(f"成功获取 {ai_config.selected_model} API 响应，报告长度: {len(analysis_report)} 字符")
        except TimeoutError as timeout_error:
            # 处理超时错误
            error_msg = str(timeout_error)
            logging.error(f"任务 {task_id}：{error_msg}")
            with progress_lock:
                analysis_progress[task_id] = {
                    'status': 'error',
                    'message': f"分析超时：{error_msg}，请检查网络连接或稍后重试"
                }
            return
        except Exception as api_error:
            logging.error(f"任务 {task_id}：AI模型调用失败: {str(api_error)}")
            logging.error(f"详细错误堆栈: {traceback.format_exc()}")
            with progress_lock:
                analysis_progress[task_id] = {
                    'status': 'error',
                    'message': f'API调用失败: {str(api_error)}'
                }
            return

        # 检查是否是错误消息
        if analysis_report.startswith("错误：") or \
           (analysis_report.startswith("DeepSeek API调用") and "失败" in analysis_report) or \
           (analysis_report.startswith("豆包API调用") and "失败" in analysis_report):
            logging.error(f"任务 {task_id}：AI模型返回错误: {analysis_report}")
            raise Exception(analysis_report)

        # 保存结果到文件和数据库
        with progress_lock:
            save_analysis_report(task_id, analysis_report)
            analysis_results[task_id] = analysis_report
            analysis_progress[task_id] = {
                'status': 'completed',
                'progress': 3,
                'message': '分析完成，请查看报告'
            }

    except Exception as e:
        # 处理错误
        with progress_lock:
            analysis_progress[task_id] = {
                'status': 'error',
                'message': f'分析过程中出错: {str(e)}'
            }
    finally:
        db.close()
