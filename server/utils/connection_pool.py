import asyncio
from typing import Dict, Set
import time
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ConnectionInfo:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    last_active: datetime
    client_id: str
    token: str

class ConnectionPool:
    def __init__(self, max_connections: int = 1000, idle_timeout: int = 300):
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout
        self.connections: Dict[str, ConnectionInfo] = {}
        self.active_connections: Set[str] = set()
        self._cleanup_task = None
        
    async def add_connection(self, client_id: str, reader: asyncio.StreamReader, 
                           writer: asyncio.StreamWriter, token: str) -> bool:
        """添加新连接到连接池"""
        if len(self.connections) >= self.max_connections:
            logger.warning(f"Connection pool is full, rejecting connection from {client_id}")
            return False
            
        if client_id in self.connections:
            await self.remove_connection(client_id)
            
        self.connections[client_id] = ConnectionInfo(
            reader=reader,
            writer=writer,
            last_active=datetime.now(),
            client_id=client_id,
            token=token
        )
        self.active_connections.add(client_id)
        logger.info(f"New connection added: {client_id}")
        return True
        
    async def remove_connection(self, client_id: str):
        """从连接池中移除连接"""
        if client_id in self.connections:
            conn = self.connections[client_id]
            conn.writer.close()
            await conn.writer.wait_closed()
            del self.connections[client_id]
            self.active_connections.discard(client_id)
            logger.info(f"Connection removed: {client_id}")
            
    async def update_activity(self, client_id: str):
        """更新连接的最后活动时间"""
        if client_id in self.connections:
            self.connections[client_id].last_active = datetime.now()
            
    async def cleanup_idle_connections(self):
        """清理空闲连接"""
        while True:
            await asyncio.sleep(60)  # 每分钟检查一次
            current_time = datetime.now()
            for client_id, conn in list(self.connections.items()):
                idle_time = (current_time - conn.last_active).total_seconds()
                if idle_time > self.idle_timeout:
                    logger.info(f"Removing idle connection: {client_id}")
                    await self.remove_connection(client_id)
                    
    def start_cleanup_task(self):
        """启动清理任务"""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self.cleanup_idle_connections())
            
    def stop_cleanup_task(self):
        """停止清理任务"""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            self._cleanup_task = None
            
    def get_connection(self, client_id: str) -> ConnectionInfo:
        """获取连接信息"""
        return self.connections.get(client_id)
        
    def get_active_connections_count(self) -> int:
        """获取活动连接数"""
        return len(self.active_connections) 