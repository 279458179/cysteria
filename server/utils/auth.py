import hashlib
import hmac
import time
import json
from typing import Dict, Optional
import jwt
from datetime import datetime, timedelta

class AuthenticationManager:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()
        self.token_expiry = timedelta(hours=24)
        self.client_tokens: Dict[str, str] = {}
        
    def generate_token(self, client_id: str, client_info: dict) -> str:
        """生成JWT令牌"""
        payload = {
            'client_id': client_id,
            'client_info': client_info,
            'exp': datetime.utcnow() + self.token_expiry
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
        
    def verify_token(self, token: str) -> Optional[dict]:
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.InvalidTokenError:
            return None
            
    def generate_challenge(self, client_id: str) -> str:
        """生成认证挑战"""
        timestamp = str(int(time.time()))
        challenge = hmac.new(
            self.secret_key,
            f"{client_id}:{timestamp}".encode(),
            hashlib.sha256
        ).hexdigest()
        return challenge
        
    def verify_challenge_response(self, client_id: str, challenge: str, response: str) -> bool:
        """验证挑战响应"""
        expected_response = hmac.new(
            self.secret_key,
            challenge.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(response, expected_response)
        
    def authenticate_client(self, client_id: str, auth_data: dict) -> Optional[str]:
        """完整的客户端认证流程"""
        # 验证客户端信息
        if not self._validate_client_info(auth_data):
            return None
            
        # 生成并验证挑战
        challenge = self.generate_challenge(client_id)
        if not self.verify_challenge_response(client_id, challenge, auth_data.get('challenge_response', '')):
            return None
            
        # 生成令牌
        token = self.generate_token(client_id, auth_data)
        self.client_tokens[client_id] = token
        return token
        
    def _validate_client_info(self, client_info: dict) -> bool:
        """验证客户端信息"""
        required_fields = ['version', 'platform', 'client_id']
        return all(field in client_info for field in required_fields) 