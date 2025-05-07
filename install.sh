#!/bin/bash

# 检查Python版本
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is required"
    exit 1
fi

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建必要的目录
mkdir -p server client

# 复制配置文件
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# 生成SSL证书（如果不存在）
if [ ! -f server/cert.pem ] || [ ! -f server/key.pem ]; then
    openssl req -x509 -newkey rsa:4096 -nodes -out server/cert.pem -keyout server/key.pem -days 365 -subj "/CN=localhost"
fi

echo "Installation completed successfully!"
echo "To start the server: python server/main.py"
echo "To start the client: python client/main.py" 