import jwt
import time
from typing import Dict, Any

class AuthenticationManager:
    """认证管理器"""
    
    def __init__(self, secret_key: str = "public"):
        self.secret_key = secret_key
        
    def authenticate_client(self, client_id: str, auth_info: Dict[str, Any]) -> str:
        """认证客户端"""
        token_data = {
            "client_id": client_id,
            "timestamp": time.time(),
            **auth_info
        }
        return jwt.encode(token_data, self.secret_key, algorithm="HS256")
        
    def verify_token(self, token: str) -> Dict[str, Any]:
        """验证令牌"""
        try:
            return jwt.decode(token, self.secret_key, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            raise ValueError("Invalid token") 