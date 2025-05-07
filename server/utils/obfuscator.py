import random
import string
from typing import Tuple

class TrafficObfuscator:
    def __init__(self):
        self.padding_chars = string.ascii_letters + string.digits
        self.min_padding = 16
        self.max_padding = 64
        
    def obfuscate(self, data: bytes) -> Tuple[bytes, bytes]:
        """混淆数据，添加随机填充"""
        # 生成随机填充
        padding_length = random.randint(self.min_padding, self.max_padding)
        padding = ''.join(random.choices(self.padding_chars, k=padding_length)).encode()
        
        # 在数据前后添加填充
        obfuscated_data = padding + data + padding
        
        # 生成混淆标记（用于识别真实数据）
        marker = random.randbytes(4)
        
        return obfuscated_data, marker
        
    def deobfuscate(self, data: bytes, marker: bytes) -> bytes:
        """去除混淆，提取真实数据"""
        # 查找标记位置
        start = data.find(marker)
        if start == -1:
            return data
            
        # 提取真实数据
        real_data = data[start:start+len(data)-self.max_padding*2]
        return real_data 