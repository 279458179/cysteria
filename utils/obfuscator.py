import random
import struct

class TrafficObfuscator:
    """流量混淆器"""
    
    def __init__(self):
        self.marker_size = 4
        
    def obfuscate(self, data: bytes) -> tuple[bytes, bytes]:
        """混淆数据"""
        marker = random.randbytes(self.marker_size)
        obfuscated = marker + data
        return obfuscated, marker
        
    def deobfuscate(self, data: bytes, marker: bytes) -> bytes:
        """去除混淆"""
        if not data.startswith(marker):
            raise ValueError("Invalid marker")
        return data[self.marker_size:] 