import os
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 输出到控制台
    ]
)

logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 创建上传文件目录
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'pdf', 'html', 'htm', 'jpg', 'zip'}

SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
DATABASE_URL = 'sqlite:///quickform.db'
APP_NAME = 'QuickForm社区版'