# Cysteria VPN

Cysteria是一个创新的VPN协议实现，专注于提供安全、快速和稳定的网络连接。采用公开访问模式，无需认证即可使用。

## 特点

- 创新的协议设计，提供更好的性能和安全性
- 支持Linux服务端和Windows/Linux客户端
- 简单的配置和部署
- 内置流量混淆功能
- 低延迟和高吞吐量
- 公开访问，无需认证
- 自动随机端口分配，避免端口冲突

## 系统要求

### 服务端
- Linux (推荐 Ubuntu 20.04 或更高版本)
- Python 3.8+
- 开放端口（随机分配）

### 客户端
- Windows 10/11 或 Linux
- Python 3.8+

## 快速开始

### 服务端安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/cysteria.git
cd cysteria

# 安装依赖
pip install -r requirements.txt

# 配置服务端
python server/config.py

# 启动服务
python server/main.py
```

服务端启动后会在 `server/port.txt` 文件中记录实际使用的端口号。

### 客户端安装

Windows用户：
1. 下载最新的客户端发布版本
2. 运行 `cysteria-client.exe`
3. 配置服务器地址和端口（从服务端的port.txt文件中获取）

Linux用户：
```bash
# 克隆仓库
git clone https://github.com/yourusername/cysteria.git
cd cysteria

# 安装依赖
pip install -r requirements.txt

# 配置客户端
python client/config.py

# 启动客户端
python client/main.py
```

## 配置说明

### 服务端配置
- `SERVER_HOST`: 服务器监听地址（默认：0.0.0.0）
- `SERVER_PORT`: 服务器端口（可选，默认随机分配）
- `ENCRYPTION_KEY`: 加密密钥（自动生成）

### 客户端配置
- `SERVER_HOST`: 服务器地址
- `SERVER_PORT`: 服务器端口（从服务端的port.txt文件中获取）
- `ENCRYPTION_KEY`: 加密密钥（需要与服务端匹配）

## 贡献

欢迎提交 Pull Requests 和 Issues！

## 许可证

MIT License 