import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class ErrorHandler:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.error_log_file = self.log_dir / "error.log"
        self.setup_logging()
        
    def setup_logging(self):
        """配置日志记录"""
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # 文件处理器
        file_handler = logging.FileHandler(self.error_log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.ERROR)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.ERROR)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """处理错误并记录"""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # 记录错误
        logger.error(
            f"Error occurred: {error_info['error_type']} - {error_info['error_message']}\n"
            f"Context: {json.dumps(error_info['context'], indent=2)}\n"
            f"Traceback: {error_info['traceback']}"
        )
        
        # 保存错误信息到文件
        self._save_error_to_file(error_info)
        
        # 根据错误类型采取相应措施
        self._take_action(error)
        
    def _save_error_to_file(self, error_info: Dict[str, Any]):
        """保存错误信息到文件"""
        try:
            with open(self.error_log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(error_info, indent=2) + '\n')
        except Exception as e:
            logger.error(f"Failed to save error to file: {str(e)}")
            
    def _take_action(self, error: Exception):
        """根据错误类型采取相应措施"""
        if isinstance(error, ConnectionError):
            # 处理连接错误
            self._handle_connection_error(error)
        elif isinstance(error, TimeoutError):
            # 处理超时错误
            self._handle_timeout_error(error)
        elif isinstance(error, ValueError):
            # 处理值错误
            self._handle_value_error(error)
        else:
            # 处理其他错误
            self._handle_unknown_error(error)
            
    def _handle_connection_error(self, error: ConnectionError):
        """处理连接错误"""
        logger.error(f"Connection error occurred: {str(error)}")
        # 可以添加重试逻辑或其他恢复措施
        
    def _handle_timeout_error(self, error: TimeoutError):
        """处理超时错误"""
        logger.error(f"Timeout error occurred: {str(error)}")
        # 可以添加超时处理逻辑
        
    def _handle_value_error(self, error: ValueError):
        """处理值错误"""
        logger.error(f"Value error occurred: {str(error)}")
        # 可以添加数据验证或清理逻辑
        
    def _handle_unknown_error(self, error: Exception):
        """处理未知错误"""
        logger.error(f"Unknown error occurred: {str(error)}")
        # 可以添加通用错误处理逻辑
        
    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误统计摘要"""
        try:
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                errors = [json.loads(line) for line in f if line.strip()]
                
            error_types = {}
            for error in errors:
                error_type = error['error_type']
                error_types[error_type] = error_types.get(error_type, 0) + 1
                
            return {
                'total_errors': len(errors),
                'error_types': error_types,
                'latest_error': errors[-1] if errors else None
            }
        except Exception as e:
            logger.error(f"Failed to get error summary: {str(e)}")
            return {
                'total_errors': 0,
                'error_types': {},
                'latest_error': None
            } 