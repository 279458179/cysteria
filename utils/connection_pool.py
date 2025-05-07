import asyncio
import time
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ConnectionPool:
    """连接池管理器"""
    
    def __init__(self, max_connections: int = 100, cleanup_interval: int = 60):
        self.max_connections = max_connections
        self.cleanup_interval = cleanup_interval
        self.connections: Dict[str, Tuple[asyncio.StreamReader, asyncio.StreamWriter, str, float]] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        
    async def add_connection(self, client_id: str, reader: asyncio.StreamReader,
                           writer: asyncio.StreamWriter, token: str) -> bool:
        """添加连接"""
        if len(self.connections) >= self.max_connections:
            return False
            
        self.connections[client_id] = (reader, writer, token, time.time())
        return True
        
    async def remove_connection(self, client_id: str):
        """移除连接"""
        if client_id in self.connections:
            _, writer, _, _ = self.connections[client_id]
            writer.close()
            await writer.wait_closed()
            del self.connections[client_id]
            
    async def update_activity(self, client_id: str):
        """更新活动时间"""
        if client_id in self.connections:
            reader, writer, token, _ = self.connections[client_id]
            self.connections[client_id] = (reader, writer, token, time.time())
            
    def start_cleanup_task(self):
        """启动清理任务"""
        if not self.cleanup_task:
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
    def stop_cleanup_task(self):
        """停止清理任务"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            self.cleanup_task = None
            
    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_inactive_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {str(e)}")
                
    async def _cleanup_inactive_connections(self):
        """清理不活跃的连接"""
        current_time = time.time()
        inactive_clients = [
            client_id for client_id, (_, _, _, last_activity) in self.connections.items()
            if current_time - last_activity > self.cleanup_interval
        ]
        
        for client_id in inactive_clients:
            await self.remove_connection(client_id)
            logger.info(f"Removed inactive connection: {client_id}") 