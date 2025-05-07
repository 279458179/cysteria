import asyncio
import ssl
import logging
from cryptography.fernet import Fernet
from typing import Dict, Optional
import json
import os
from dotenv import load_dotenv
import time

from utils.obfuscator import TrafficObfuscator
from utils.auth import AuthenticationManager
from utils.connection_pool import ConnectionPool
from utils.performance import PerformanceMonitor
from utils.error_handler import ErrorHandler

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CysteriaServer:
    def __init__(self, host: str = '0.0.0.0', port: int = 443):
        self.host = host
        self.port = port
        self.encryption_key = Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        
        # 初始化各个组件
        self.obfuscator = TrafficObfuscator()
        self.auth_manager = AuthenticationManager(os.getenv('AUTH_SECRET_KEY', 'default_secret_key'))
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
            
            # 处理客户端认证
            auth_data = await reader.read(1024)
            if not auth_data:
                return
                
            # 解密认证数据
            decrypted_data = self.cipher.decrypt(auth_data)
            auth_info = json.loads(decrypted_data)
            
            # 验证客户端
            token = self.auth_manager.authenticate_client(client_id, auth_info)
            if not token:
                writer.write(b"Authentication failed")
                await writer.drain()
                return
                
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

def main():
    # 加载环境变量
    load_dotenv()
    
    # 创建服务器实例
    server = CysteriaServer(
        host=os.getenv('SERVER_HOST', '0.0.0.0'),
        port=int(os.getenv('SERVER_PORT', 443))
    )
    
    # 启动服务器
    asyncio.run(server.start())

if __name__ == "__main__":
    main() 