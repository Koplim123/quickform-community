import random
import string
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from .config import DATABASE_URL

# 初始化SQLAlchemy
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def generate_custom_id():
    """
    生成11位自定义ID：9位数字和字母组合 + 2位大写字母
    例如：oU59mLzPJPU
    """
    chars = string.ascii_letters + string.digits
    prefix = ''.join(random.choices(chars, k=9))
    suffix = ''.join(random.choices(string.ascii_uppercase, k=2))
    return prefix + suffix


# 数据库模型
class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    tasks = relationship('Task', back_populates='author')
    ai_config = relationship('AIConfig', back_populates='user', uselist=False)


class Task(Base):
    __tablename__ = 'task'
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey('user.id'))
    author = relationship('User', back_populates='tasks')
    submission = relationship('Submission', back_populates='task', cascade='all, delete-orphan')
    attachments = relationship('Attachment', back_populates='task', cascade='all, delete-orphan')
    task_id = Column(String(11), unique=True, default=generate_custom_id)
    analysis_report = Column(Text)
    report_file_path = Column(String(500))
    report_generated_at = Column(DateTime)


class Attachment(Base):
    __tablename__ = 'attachment'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'), nullable=False)
    task = relationship('Task', back_populates='attachments')
    file_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class Submission(Base):
    __tablename__ = 'submission'
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey('task.id'))
    task = relationship('Task', back_populates='submission')
    data = Column(Text, nullable=False)
    submitted_at = Column(DateTime, default=datetime.now)


class AIConfig(Base):
    __tablename__ = 'ai_config'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), unique=True)
    user = relationship('User', back_populates='ai_config')
    selected_model = Column(String(50), default='deepseek')
    model_configs = relationship('AIModelConfig', back_populates='ai_config', cascade='all, delete-orphan')


class AIModelConfig(Base):
    __tablename__ = 'ai_model_config'
    id = Column(Integer, primary_key=True)
    ai_config_id = Column(Integer, ForeignKey('ai_config.id'))
    ai_config = relationship('AIConfig', back_populates='model_configs')
    model_name = Column(String(50))
    api_key = Column(String(200))
    api_url = Column(String(200))
    extra_settings = Column(Text)


class QFConfig(Base):
    __tablename__ = 'qf_config'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), unique=True)
    user = relationship('User', back_populates='qf_config')
    username = Column(String(100))
    password = Column(String(200))


User.qf_config = relationship('QFConfig', back_populates='user', uselist=False)

# 创建数据库表
Base.metadata.create_all(engine)
