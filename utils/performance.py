import time
from typing import Dict
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.latencies: Dict[str, float] = defaultdict(float)
        self.throughputs: Dict[str, int] = defaultdict(int)
        self.errors: Dict[str, int] = defaultdict(int)
        
    def record_latency(self, client_id: str, latency: float):
        """记录延迟"""
        self.latencies[client_id] = latency
        
    def record_throughput(self, client_id: str, bytes_count: int):
        """记录吞吐量"""
        self.throughputs[client_id] += bytes_count
        
    def record_error(self, client_id: str):
        """记录错误"""
        self.errors[client_id] += 1
        
    def log_performance_metrics(self):
        """记录性能指标"""
        for client_id in self.latencies.keys():
            logger.info(
                f"Client {client_id} metrics:\n"
                f"  Latency: {self.latencies[client_id]:.2f}ms\n"
                f"  Throughput: {self.throughputs[client_id]/1024:.2f}KB\n"
                f"  Errors: {self.errors[client_id]}"
            ) 