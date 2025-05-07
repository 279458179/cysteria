# Cysteria VPN

Cysteria是一个创新的VPN协议实现，专注于提供安全、快速和稳定的网络连接。

## 特点

- 创新的协议设计，提供更好的性能和安全性
- 支持Linux服务端和Windows/Linux客户端
- 简单的配置和部署
- 内置流量混淆功能
- 低延迟和高吞吐量

## 系统要求

### 服务端
- Linux (推荐 Ubuntu 20.04 或更高版本)
- Python 3.8+
- 开放端口（默认443）

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

### 客户端安装

Windows用户：
1. 下载最新的客户端发布版本
2. 运行 `cysteria-client.exe`
3. 按照向导完成配置

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

详细的配置说明请参考 [配置文档](docs/configuration.md)

## 贡献

欢迎提交 Pull Requests 和 Issues！

## 许可证

MIT License 