#!/bin/bash

echo "开始安装系统依赖..."
# 更新包列表并安装CUDA相关依赖
apt update
# apt install -y libcudnn9-cuda-12

echo "开始安装Python依赖..."

# 升级pip
pip install --upgrade pip

# 先尝试安装基础依赖
pip install wheel setuptools

# 单独安装可能有冲突的包
echo "安装bcrypt..."
pip install bcrypt --ignore-installed

# echo "安装PyJWT..."
# pip install PyJWT --ignore-installed

# 安装其他依赖，忽略已安装的包
echo "安装requirements.txt中的其他依赖..."
pip install -r requirements.txt --ignore-installed --no-warn-script-location

echo "依赖安装完成!" 