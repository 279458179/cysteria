import os
from dotenv import load_dotenv
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 客户端配置
DEFAULT_SERVER_HOST = os.getenv('SERVER_HOST', 'localhost')
DEFAULT_SERVER_PORT = int(os.getenv('SERVER_PORT', 443))

# 创建日志目录
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)

def setup():
    """初始化配置"""
    try:
        logger.info("客户端配置初始化完成")
        return True
    except Exception as e:
        logger.error(f"配置初始化失败: {str(e)}")
        return False

if __name__ == "__main__":
    setup() 