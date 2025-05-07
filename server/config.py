import os
from dotenv import load_dotenv
import logging
from pathlib import Path
import socket
import random

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 服务器配置
SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')

def find_available_port(start_port=1024, end_port=65535):
    """查找可用端口"""
    while True:
        port = random.randint(start_port, end_port)
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((SERVER_HOST, port))
                logger.info(f"找到可用端口: {port}")
                return port
        except OSError:
            continue

# 获取随机端口
SERVER_PORT = int(os.getenv('SERVER_PORT', find_available_port()))

# SSL证书配置
CERT_DIR = Path(__file__).parent
CERT_FILE = CERT_DIR / 'cert.pem'
KEY_FILE = CERT_DIR / 'key.pem'

# 创建证书目录（如果不存在）
CERT_DIR.mkdir(parents=True, exist_ok=True)

def generate_self_signed_cert():
    """生成自签名SSL证书"""
    from OpenSSL import crypto
    
    # 检查证书是否已存在
    if CERT_FILE.exists() and KEY_FILE.exists():
        logger.info("SSL证书已存在")
        return
        
    # 生成密钥
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)
    
    # 生成证书
    cert = crypto.X509()
    cert.get_subject().CN = "Cysteria VPN"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # 有效期1年
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')
    
    # 保存证书和密钥
    with open(CERT_FILE, 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    with open(KEY_FILE, 'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))
        
    logger.info("已生成新的SSL证书")

def setup():
    """初始化配置"""
    try:
        # 生成SSL证书
        generate_self_signed_cert()
        
        # 创建日志目录
        log_dir = Path(__file__).parent / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存端口信息到文件
        port_file = Path(__file__).parent / 'port.txt'
        with open(port_file, 'w') as f:
            f.write(str(SERVER_PORT))
        
        logger.info(f"配置初始化完成，服务器端口: {SERVER_PORT}")
        return True
    except Exception as e:
        logger.error(f"配置初始化失败: {str(e)}")
        return False

if __name__ == "__main__":
    setup() 