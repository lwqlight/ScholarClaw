@echo off
chcp 65001 >nul
echo =====================================
echo   🚀 欢迎使用 EmboRadar 具身雷达
echo =====================================

IF NOT EXIST venv (
    echo 📦 未检测到运行环境，正在为您自动创建虚拟环境并安装依赖 (仅需一次)...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt -q
    echo ✅ 环境安装完毕！
) ELSE (
    echo ⚡ 检测到已有环境，直接启动...
    call venv\Scripts\activate.bat
)

echo 🌐 正在启动 Web 控制台，请稍候...
python webui.py
pause