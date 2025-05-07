import sys
import os
import json
import asyncio
import ssl
import logging
import winreg
import random
import hashlib
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                           QHBoxLayout, QPushButton, QLabel, QLineEdit,
                           QTextEdit, QSystemTrayIcon, QMenu, QAction,
                           QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

def setup_logging():
    """配置日志"""
    # 获取程序运行目录
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        app_dir = Path(sys._MEIPASS)
    else:
        # 如果是开发环境
        app_dir = Path(__file__).parent

    # 创建日志目录
    log_dir = app_dir / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'client.log'),
            logging.StreamHandler()
        ]
    )

# 初始化日志
setup_logging()
logger = logging.getLogger(__name__)

class CysteriaProtocol:
    """Cysteria协议实现"""
    def __init__(self):
        self.version = "1.0"
        self.magic = b"CYS"  # 协议魔数
        
    def generate_handshake(self):
        """生成握手数据"""
        # 生成随机密钥
        key = os.urandom(32)
        # 生成握手数据
        handshake = self.magic + key
        return handshake, key
        
    def encrypt_data(self, data, key):
        """加密数据"""
        # 使用XOR加密
        encrypted = bytearray()
        for i, byte in enumerate(data):
            encrypted.append(byte ^ key[i % len(key)])
        return bytes(encrypted)
        
    def decrypt_data(self, data, key):
        """解密数据"""
        # XOR解密
        return self.encrypt_data(data, key)
        
    def obfuscate_traffic(self, data):
        """混淆流量"""
        # 添加随机填充
        padding = os.urandom(random.randint(1, 10))
        return padding + data

class Config:
    """配置管理器"""
    def __init__(self):
        if getattr(sys, 'frozen', False):
            # 如果是打包后的exe
            self.config_dir = Path(os.environ['APPDATA']) / 'Cysteria'
        else:
            # 如果是开发环境
            self.config_dir = Path(__file__).parent / 'config'
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / 'config.json'
        self.load_config()
    
    def load_config(self):
        """加载配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = {
                    'server': '',
                    'port': '',
                    'last_connected': False
                }
                self.save_config()
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            self.config = {
                'server': '',
                'port': '',
                'last_connected': False
            }
    
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")

class SystemProxy:
    """系统代理管理器"""
    def __init__(self):
        self.INTERNET_SETTINGS = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Internet Settings',
            0, winreg.KEY_ALL_ACCESS)

    def set_proxy(self, host, port):
        """设置系统代理"""
        try:
            # 启用代理
            winreg.SetValueEx(self.INTERNET_SETTINGS, 'ProxyEnable', 0, winreg.REG_DWORD, 1)
            # 设置HTTP和HTTPS代理
            proxy_server = f"http=127.0.0.1:{port};https=127.0.0.1:{port}"
            winreg.SetValueEx(self.INTERNET_SETTINGS, 'ProxyServer', 0, winreg.REG_SZ, proxy_server)
            # 刷新系统设置
            self._refresh_system()
            logger.info(f"系统代理已设置为: {proxy_server}")
            return True
        except Exception as e:
            logger.error(f"设置系统代理失败: {str(e)}")
            return False

    def clear_proxy(self):
        """清除系统代理"""
        try:
            # 禁用代理
            winreg.SetValueEx(self.INTERNET_SETTINGS, 'ProxyEnable', 0, winreg.REG_DWORD, 0)
            # 刷新系统设置
            self._refresh_system()
            logger.info("系统代理已清除")
            return True
        except Exception as e:
            logger.error(f"清除系统代理失败: {str(e)}")
            return False

    def _refresh_system(self):
        """刷新系统代理设置"""
        import ctypes
        INTERNET_OPTION_SETTINGS_CHANGED = 39
        INTERNET_OPTION_REFRESH = 37
        internet_set_option = ctypes.windll.Wininet.InternetSetOptionW
        internet_set_option(0, INTERNET_OPTION_SETTINGS_CHANGED, 0, 0)
        internet_set_option(0, INTERNET_OPTION_REFRESH, 0, 0)

class VPNClient(QThread):
    """VPN客户端线程"""
    status_changed = pyqtSignal(str)
    log_message = pyqtSignal(str)
    
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.running = False
        self.system_proxy = SystemProxy()
        self.protocol = CysteriaProtocol()
        
    def run(self):
        """运行VPN客户端"""
        try:
            self.running = True
            self.status_changed.emit("正在连接...")
            self.log_message.emit(f"正在连接到服务器 {self.host}:{self.port}")
            
            # 设置系统代理
            if self.system_proxy.set_proxy(self.host, self.port):
                self.log_message.emit("系统代理设置成功")
            else:
                self.log_message.emit("系统代理设置失败")
                raise Exception("系统代理设置失败")
            
            # 连接到VPN服务器
            asyncio.run(self.connect())
            
        except Exception as e:
            self.log_message.emit(f"连接错误: {str(e)}")
            self.status_changed.emit("连接失败")
            # 清除系统代理
            self.system_proxy.clear_proxy()
        finally:
            self.running = False
            
    async def connect(self):
        """连接到VPN服务器"""
        # 创建SSL上下文
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # 连接到服务器
        reader, writer = await asyncio.open_connection(
            self.host, self.port, ssl=ssl_context
        )
        
        # 发送握手数据
        handshake, key = self.protocol.generate_handshake()
        writer.write(handshake)
        await writer.drain()
        
        # 等待服务器响应
        response = await reader.read(1024)
        if response != b"OK":
            raise Exception("服务器握手失败")
            
        self.status_changed.emit("已连接")
        self.log_message.emit("成功连接到服务器")
        
        try:
            while self.running:
                # 读取数据
                data = await reader.read(1024)
                if not data:
                    break
                    
                # 解密数据
                decrypted = self.protocol.decrypt_data(data, key)
                
                # 处理数据
                # TODO: 实现实际的数据处理逻辑
                
                # 发送响应
                response = self.protocol.encrypt_data(b"OK", key)
                writer.write(response)
                await writer.drain()
                
        finally:
            writer.close()
            await writer.wait_closed()
            
    def stop(self):
        """停止VPN客户端"""
        self.running = False
        # 清除系统代理
        if self.system_proxy.clear_proxy():
            self.log_message.emit("系统代理已清除")
        else:
            self.log_message.emit("系统代理清除失败")
        self.status_changed.emit("已断开")
        self.log_message.emit("已断开连接")

class MainWindow(QMainWindow):
    """主窗口"""
    def __init__(self):
        super().__init__()
        self.vpn_client = None
        self.config = Config()
        self.init_ui()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('Cysteria VPN')
        self.setFixedSize(400, 300)
        
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建布局
        layout = QVBoxLayout(central_widget)
        
        # 服务器设置
        server_layout = QHBoxLayout()
        server_label = QLabel('服务器地址:')
        self.server_input = QLineEdit()
        self.server_input.setPlaceholderText('输入服务器地址')
        self.server_input.setText(self.config.config['server'])
        server_layout.addWidget(server_label)
        server_layout.addWidget(self.server_input)
        layout.addLayout(server_layout)
        
        # 端口设置
        port_layout = QHBoxLayout()
        port_label = QLabel('端口:')
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText('输入端口号')
        self.port_input.setText(self.config.config['port'])
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_input)
        layout.addLayout(port_layout)
        
        # 连接按钮
        self.connect_button = QPushButton('连接')
        self.connect_button.clicked.connect(self.toggle_connection)
        layout.addWidget(self.connect_button)
        
        # 日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        layout.addWidget(self.log_display)
        
        # 创建系统托盘图标
        self.create_tray_icon()
        
        # 如果上次是连接状态，自动连接
        if self.config.config['last_connected']:
            self.toggle_connection()
        
    def create_tray_icon(self):
        """创建系统托盘图标"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('client/assets/icon.ico'))
        
        # 创建托盘菜单
        tray_menu = QMenu()
        show_action = QAction('显示', self)
        show_action.triggered.connect(self.show)
        quit_action = QAction('退出', self)
        quit_action.triggered.connect(self.close)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def toggle_connection(self):
        """切换连接状态"""
        if self.vpn_client and self.vpn_client.running:
            self.vpn_client.stop()
            self.connect_button.setText('连接')
            self.config.config['last_connected'] = False
            self.config.save_config()
        else:
            host = self.server_input.text()
            try:
                port = int(self.port_input.text())
            except ValueError:
                self.log_display.append("错误：端口必须是数字")
                return
                
            # 保存配置
            self.config.config['server'] = host
            self.config.config['port'] = str(port)
            self.config.config['last_connected'] = True
            self.config.save_config()
                
            self.vpn_client = VPNClient(host, port)
            self.vpn_client.status_changed.connect(self.update_status)
            self.vpn_client.log_message.connect(self.log_display.append)
            self.vpn_client.start()
            self.connect_button.setText('断开')
            
    def update_status(self, status):
        """更新状态显示"""
        self.log_display.append(f"状态: {status}")
        
    def closeEvent(self, event):
        """关闭窗口事件"""
        if self.vpn_client and self.vpn_client.running:
            self.vpn_client.stop()
            self.config.config['last_connected'] = False
            self.config.save_config()
        event.accept()

def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 