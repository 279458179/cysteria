import asyncio
import ssl
import logging
from cryptography.fernet import Fernet
from typing import Dict, Optional
import json
import os
from dotenv import load_dotenv
import time
import sys
import signal
import daemon
from pathlib import Path
from config import SERVER_HOST, SERVER_PORT, setup
import random

from utils.obfuscator import TrafficObfuscator
from utils.auth import AuthenticationManager
from utils.connection_pool import ConnectionPool
from utils.performance import PerformanceMonitor
from utils.error_handler import ErrorHandler

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent / 'logs' / 'server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CysteriaProtocol:
    """Cysteria协议实现"""
    def __init__(self):
        self.version = "1.0"
        self.magic = b"CYS"  # 协议魔数
        
    def verify_handshake(self, data):
        """验证握手数据"""
        if len(data) < 3:
            return False, None
        if data[:3] != self.magic:
            return False, None
        return True, data[3:]
        
    def encrypt_data(self, data, key):
        """加密数据"""
        # 使用XOR加密
        encrypted = bytearray()
        for i, byte in enumerate(data):
            encrypted.append(byte ^ key[i % len(key)])
        return bytes(encrypted)
        
    def decrypt_data(self, data, key):
        """解密数据"""
        # XOR解密
        return self.encrypt_data(data, key)
        
    def obfuscate_traffic(self, data):
        """混淆流量"""
        # 添加随机填充
        padding = os.urandom(random.randint(1, 10))
        return padding + data

class CysteriaServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 443):
        self.host = host
        self.port = port
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # 初始化各个组件
        self.obfuscator = TrafficObfuscator()
        self.auth_manager = AuthenticationManager()  # 使用默认的公开访问密钥
        self.connection_pool = ConnectionPool()
        self.performance_monitor = PerformanceMonitor()
        self.error_handler = ErrorHandler()
        
        # 加载SSL证书
        self.ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        self.ssl_context.load_cert_chain(
            certfile='server/cert.pem',
            keyfile='server/key.pem'
        )

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_id = None
        start_time = time.time()
        
        try:
            # 获取客户端信息
            addr = writer.get_extra_info('peername')
            client_id = f"{addr[0]}:{addr[1]}"
            
            # 处理客户端连接
            auth_info = {
                'client_id': client_id,
                'connected_at': time.time()
            }
            
            # 生成访问令牌
            token = self.auth_manager.authenticate_client(client_id, auth_info)
            
            # 添加到连接池
            if not await self.connection_pool.add_connection(client_id, reader, writer, token):
                writer.write(b"Connection pool full")
                await writer.drain()
                return
                
            logger.info(f"New client connected: {client_id}")
            
            # 主循环处理客户端数据
            while True:
                data = await reader.read(8192)
                if not data:
                    break
                    
                # 更新活动时间
                await self.connection_pool.update_activity(client_id)
                
                # 解密数据
                decrypted_data = self.cipher.decrypt(data)
                
                # 去除混淆
                real_data = self.obfuscator.deobfuscate(decrypted_data, auth_info.get('marker', b''))
                
                # 处理数据
                response = await self.process_client_data(real_data)
                
                # 添加混淆
                obfuscated_response, marker = self.obfuscator.obfuscate(response)
                
                # 加密响应
                encrypted_response = self.cipher.encrypt(obfuscated_response)
                
                # 发送响应
                writer.write(encrypted_response)
                await writer.drain()
                
                # 记录性能指标
                latency = (time.time() - start_time) * 1000
                self.performance_monitor.record_latency(client_id, latency)
                self.performance_monitor.record_throughput(client_id, len(data))
                
        except Exception as e:
            if client_id:
                self.error_handler.handle_error(e, {'client_id': client_id})
                self.performance_monitor.record_error(client_id)
            logger.error(f"Error handling client {client_id}: {str(e)}")
        finally:
            if client_id:
                await self.connection_pool.remove_connection(client_id)
            writer.close()
            await writer.wait_closed()
            logger.info(f"Client disconnected: {client_id}")

    async def process_client_data(self, data: bytes) -> bytes:
        """处理客户端数据"""
        try:
            # 这里实现具体的数据处理逻辑
            return b"OK"
        except Exception as e:
            self.error_handler.handle_error(e, {'data': data})
            return b"Error processing data"

    async def start(self):
        """启动服务器"""
        try:
            # 启动连接池清理任务
            self.connection_pool.start_cleanup_task()
            
            # 启动服务器
            server = await asyncio.start_server(
                self.handle_client,
                self.host,
                self.port,
                ssl=self.ssl_context
            )
            
            logger.info(f"Server started on {self.host}:{self.port}")
            
            # 定期记录性能指标
            async def log_performance():
                while True:
                    await asyncio.sleep(60)
                    self.performance_monitor.log_performance_metrics()
                    
            asyncio.create_task(log_performance())
            
            async with server:
                await server.serve_forever()
                
        except Exception as e:
            self.error_handler.handle_error(e)
            raise
        finally:
            self.connection_pool.stop_cleanup_task()

def run_server():
    """运行服务器"""
    try:
        # 初始化配置
        if not setup():
            sys.exit(1)
            
        # 创建服务器实例
        server = CysteriaServer(SERVER_HOST, SERVER_PORT)
        
        # 运行服务器
        logger.info(f"Server started on {SERVER_HOST}:{SERVER_PORT}")
        asyncio.run(server.start())
        
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        sys.exit(1)

def main():
    """主函数"""
    # 检查是否以守护进程模式运行
    if len(sys.argv) > 1 and sys.argv[1] == '--daemon':
        # 创建守护进程
        with daemon.DaemonContext(
            working_directory=os.getcwd(),
            umask=0o022,
            signal_map={
                signal.SIGTERM: lambda signo, frame: sys.exit(0)
            }
        ):
            run_server()
    else:
        run_server()

if __name__ == "__main__":
    main() 