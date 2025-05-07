import logging
import traceback
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ErrorHandler:
    """错误处理器"""
    
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """处理错误"""
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # 记录错误信息
        logger.error(
            f"Error occurred:\n"
            f"Type: {error_type}\n"
            f"Message: {error_message}\n"
            f"Context: {context}\n"
            f"Stack trace:\n{stack_trace}"
        ) 