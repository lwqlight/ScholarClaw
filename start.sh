#!/bin/bash

# 打印颜色配置，让终端输出更好看
GREEN='\033[0;32m'
NC='\033[0m' # 无颜色

echo -e "${GREEN}>>> 正在检查并安装环境依赖...${NC}"
# 静默安装依赖，如果已经装过会直接跳过
pip install requests feedparser zhipuai schedule python-dotenv PyYAML -q

echo -e "${GREEN}>>> 环境准备完毕，正在唤醒 AI 管家...${NC}"
# 执行 Python 脚本
python ai_butler.py