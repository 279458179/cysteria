import asyncio
import logging
from typing import Dict, List
import time
from collections import deque
import statistics

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.latency_history: Dict[str, deque] = {}
        self.throughput_history: Dict[str, deque] = {}
        self.error_count: Dict[str, int] = {}
        
    def record_latency(self, client_id: str, latency: float):
        """记录延迟数据"""
        if client_id not in self.latency_history:
            self.latency_history[client_id] = deque(maxlen=self.window_size)
        self.latency_history[client_id].append(latency)
        
    def record_throughput(self, client_id: str, bytes_transferred: int):
        """记录吞吐量数据"""
        if client_id not in self.throughput_history:
            self.throughput_history[client_id] = deque(maxlen=self.window_size)
        self.throughput_history[client_id].append(bytes_transferred)
        
    def record_error(self, client_id: str):
        """记录错误"""
        self.error_count[client_id] = self.error_count.get(client_id, 0) + 1
        
    def get_client_stats(self, client_id: str) -> dict:
        """获取客户端统计信息"""
        stats = {
            'latency': {
                'current': 0,
                'average': 0,
                'max': 0,
                'min': 0
            },
            'throughput': {
                'current': 0,
                'average': 0,
                'max': 0
            },
            'error_rate': 0
        }
        
        # 计算延迟统计
        if client_id in self.latency_history and self.latency_history[client_id]:
            latencies = list(self.latency_history[client_id])
            stats['latency'].update({
                'current': latencies[-1],
                'average': statistics.mean(latencies),
                'max': max(latencies),
                'min': min(latencies)
            })
            
        # 计算吞吐量统计
        if client_id in self.throughput_history and self.throughput_history[client_id]:
            throughputs = list(self.throughput_history[client_id])
            stats['throughput'].update({
                'current': throughputs[-1],
                'average': statistics.mean(throughputs),
                'max': max(throughputs)
            })
            
        # 计算错误率
        total_requests = len(self.latency_history.get(client_id, []))
        if total_requests > 0:
            stats['error_rate'] = self.error_count.get(client_id, 0) / total_requests
            
        return stats
        
    def get_global_stats(self) -> dict:
        """获取全局统计信息"""
        all_latencies = []
        all_throughputs = []
        total_errors = sum(self.error_count.values())
        total_requests = sum(len(history) for history in self.latency_history.values())
        
        for client_id in self.latency_history:
            all_latencies.extend(self.latency_history[client_id])
            all_throughputs.extend(self.throughput_history.get(client_id, []))
            
        return {
            'total_clients': len(self.latency_history),
            'latency': {
                'average': statistics.mean(all_latencies) if all_latencies else 0,
                'max': max(all_latencies) if all_latencies else 0,
                'min': min(all_latencies) if all_latencies else 0
            },
            'throughput': {
                'average': statistics.mean(all_throughputs) if all_throughputs else 0,
                'max': max(all_throughputs) if all_throughputs else 0
            },
            'error_rate': total_errors / total_requests if total_requests > 0 else 0
        }
        
    def log_performance_metrics(self):
        """记录性能指标"""
        global_stats = self.get_global_stats()
        logger.info(f"Performance Metrics - "
                   f"Clients: {global_stats['total_clients']}, "
                   f"Avg Latency: {global_stats['latency']['average']:.2f}ms, "
                   f"Avg Throughput: {global_stats['throughput']['average']:.2f} bytes/s, "
                   f"Error Rate: {global_stats['error_rate']*100:.2f}%") 