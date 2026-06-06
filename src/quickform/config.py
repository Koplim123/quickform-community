import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# 读 config.json
_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'config.json'
)
with open(_path, 'r', encoding='utf-8') as f:
    _cfg = json.load(f)


def readCfg(key):
    """从 config.json 读取"""
    return _cfg[key]


def readEnv(key):
    """从环境变量读取，不存在则回退到 config.json"""
    return os.getenv(key, _cfg[key])


# --- 业务配置 ---
APP_NAME           = readCfg('APP_NAME')
UPLOAD_FOLDER      = readCfg('UPLOAD_FOLDER')
ALLOWED_EXTENSIONS = set(readCfg('ALLOWED_EXTENSIONS'))

# --- 启动配置 ---
DEBUG              = readCfg('DEBUG')
HOST               = readCfg('HOST')
PORT               = readCfg('PORT')
LOG_LEVEL          = readCfg('LOG_LEVEL')

# --- 敏感配置 ---
SECRET_KEY         = readEnv('SECRET_KEY')
DATABASE_URL       = readEnv('DATABASE_URL')

# --- 日志 ---
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)