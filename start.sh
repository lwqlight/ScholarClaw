#!/bin/bash
# 赋予执行权限：chmod +x start.sh

echo "====================================="
echo "  🚀 欢迎使用 EmboRadar (Conda版)"
echo "====================================="

echo "🔌 正在唤醒本地 Conda 引擎..."
# 让 Bash 脚本能够识别并使用 conda activate 命令
eval "$(conda shell.bash hook)"

echo "🔄 正在切换到 base 环境..."
conda activate yolov10

echo "📦 正在检查并安装缺失的依赖 (已有依赖会自动跳过)..."
pip install -r requirements.txt -q
echo "✅ 环境安装与检测完毕！"

echo "🌐 正在启动 Web 控制台，请稍候..."
python webui.py