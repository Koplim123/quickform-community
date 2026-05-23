import os
import json
import uuid
import threading
from functools import wraps

from .config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, logger
from .models import SessionLocal, Submission


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    try:
        if file and allowed_file(file.filename):
            unique_filename = str(uuid.uuid4()) + '_' + file.filename
            filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(filepath)
            # 确保路径使用正斜杠，以便在URL中正确使用
            filepath = filepath.replace('\\', '/')
            return unique_filename, filepath
    except Exception as e:
        logger.error(f"保存文件失败: {str(e)}")
    return None, None


def read_file_content(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return f"二进制文件 (大小: {len(content)} 字节)"
        except Exception as e:
            logger.error(f"读取文件内容失败: {str(e)}")
            return f"无法读取文件内容: {str(e)}"
    except Exception as e:
        logger.error(f"读取文件内容失败: {str(e)}")
        return f"无法读取文件内容: {str(e)}"


def generate_analysis_prompt(task, submission=None, file_content=None):
    """
    根据任务信息生成分析提示词
    """
    # 获取提交数据
    if not submission:
        db = SessionLocal()
        try:
            submission = db.query(Submission).filter_by(task_id=task.id).all()
        finally:
            db.close()

    # 构建提示词
    prompt = f"""你是一个数据分析专家，请基于以下表单数据提供详细的分析报告：

任务标题：{task.title}
任务描述：{task.description or '无'}

提交数据摘要：
"""

    # 添加提交数据摘要
    if submission:
        prompt += f"共有 {len(submission)} 条提交记录\n"

        # 分析前3条提交数据作为示例
        for i, sub in enumerate(submission[:3]):
            try:
                data = json.loads(sub.data)
                prompt += f"\n提交 #{i+1}:\n"
                for key, value in data.items():
                    prompt += f"  - {key}: {value}\n"
            except:
                prompt += f"\n提交 #{i+1}: {sub.data[:100]}...\n"
    else:
        prompt += "暂无提交数据\n"

    # 添加文件信息
    if file_content:
        prompt += f"\n附件内容摘要：\n{file_content[:500]}...\n" if len(file_content) > 500 else f"\n附件内容：\n{file_content}\n"

    # 添加分析要求
    prompt += """

请提供一个全面的数据分析报告，包括但不限于：
1. 数据概览：总提交量、关键数据分布等
2. 主要发现：数据中的趋势、模式和异常
3. 深入分析：基于数据的详细洞察
4. 建议和结论：基于分析结果的实用建议

请以中文撰写报告，使用Markdown格式，包括适当的标题、列表和表格来增强可读性。
"""

    return prompt


def timeout(seconds, error_message="函数执行超时"):
    """
    超时装饰器（使用线程实现，避免信号处理问题）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 结果容器
            result = [None]
            exception = [None]

            # 目标函数
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            # 创建并启动线程
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(seconds)

            # 检查线程是否仍在运行
            if thread.is_alive():
                # 线程超时，抛出异常
                raise TimeoutError(error_message)
            elif exception[0]:
                # 函数执行中出现异常
                raise exception[0]
            else:
                # 正常返回结果
                return result[0]

        return wrapper

    return decorator
