import asyncio
import ssl
import logging
from cryptography.fernet import Fernet
import json
import os
from dotenv import load_dotenv
import sys
import platform
import time
from typing import Optional, Tuple

from utils.obfuscator import TrafficObfuscator
from utils.error_handler import ErrorHandler

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CysteriaClient:
    def __init__(self, server_host: str, server_port: int, encryption_key: bytes):
        self.server_host = server_host
        self.server_port = server_port
        self.encryption_key = encryption_key
        self.cipher = Fernet(encryption_key)
        self.obfuscator = TrafficObfuscator()
        self.error_handler = ErrorHandler()
        self.marker: Optional[bytes] = None
        
        # 配置SSL上下文
        self.ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    async def connect(self):
        try:
            # 建立SSL连接
            reader, writer = await asyncio.open_connection(
                self.server_host,
                self.server_port,
                ssl=self.ssl_context
            )
            
            logger.info("Successfully connected to server")
            
            # 主循环
            while True:
                # 读取用户输入或系统数据
                data = await self.get_data_to_send()
                if not data:
                    continue
                    
                # 添加混淆
                obfuscated_data, self.marker = self.obfuscator.obfuscate(data)
                
                # 加密数据
                encrypted_data = self.cipher.encrypt(obfuscated_data)
                
                # 发送数据
                writer.write(encrypted_data)
                await writer.drain()
                
                # 接收服务器响应
                response = await reader.read(8192)
                if not response:
                    break
                    
                # 解密响应
                decrypted_response = self.cipher.decrypt(response)
                
                # 去除混淆
                real_response = self.obfuscator.deobfuscate(decrypted_response, self.marker)
                
                # 处理响应
                await self.handle_response(real_response)
                
        except Exception as e:
            self.error_handler.handle_error(e, {
                'server_host': self.server_host,
                'server_port': self.server_port
            })
            logger.error(f"Connection error: {str(e)}")
        finally:
            if 'writer' in locals():
                writer.close()
                await writer.wait_closed()

    async def get_data_to_send(self) -> bytes:
        """获取要发送的数据"""
        try:
            # 这里实现具体的数据获取逻辑
            return b"test data"
        except Exception as e:
            self.error_handler.handle_error(e)
            return b""

    async def handle_response(self, response: bytes):
        """处理服务器响应"""
        try:
            logger.info(f"Received response: {response.decode()}")
        except Exception as e:
            self.error_handler.handle_error(e, {'response': response})

def main():
    # 加载环境变量
    load_dotenv()
    
    # 获取配置
    server_host = os.getenv('SERVER_HOST', 'localhost')
    server_port = int(os.getenv('SERVER_PORT', 443))
    encryption_key = os.getenv('ENCRYPTION_KEY', '').encode()
    
    if not encryption_key:
        logger.error("Encryption key not found in environment variables")
        sys.exit(1)
    
    # 创建客户端实例
    client = CysteriaClient(server_host, server_port, encryption_key)
    
    # 启动客户端
    asyncio.run(client.connect())

if __name__ == "__main__":
    main() 