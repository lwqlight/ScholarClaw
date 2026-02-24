# 🤖 AI 学术管家 (Embodied AI Paper Tracker)

![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

ScholarClaw 是一个专为“具身智能 (Embodied AI)”与“机器人学”研究者打造的极简 AI 学术管家。它能 24 小时静默运行在你的闲置设备上，精准雷达式扫描 CoRL、ICRA、RSS 等顶级会议。通过接入大语言模型，它能将晦涩的长篇英文摘要一键转化为“痛点+创新点”的精美中文卡片，并准时推送到你的手机，让你彻底告别学术信息焦虑，把时间留给真正的深度思考。

专为**具身智能 (Embodied AI)** 和**机器人学 (Robotics)** 研究者打造的轻量级、全自动文献追踪与 AI 总结助手。

通过整合全球顶级学术文献数据库和云端大语言模型，它能 24 小时在后台替你“盯盘”。一旦有符合你研究方向的顶会/顶刊论文发表，它会自动提取核心创新点，并以排版精美的卡片推送到你的聊天软件（飞书）中。

---

## ✨ 核心特性

- 🎯 **精准雷达**：直连 Semantic Scholar API，精准捕捉 CoRL, ICRA, IROS, RSS 等顶会以及 Science Robotics 等顶刊的最新发表动态，彻底告别水文。
- 🧠 **AI 深度提炼**：接入智谱 GLM-4 大模型，自动阅读晦涩的英文摘要，并提炼为“行业痛点 + 核心创新点”的精炼中文卡片。
- 📱 **极佳的阅读体验**：原生对接飞书 (Feishu) Webhook，支持图文并茂的 Markdown 交互式卡片推送，手机端阅读体验极佳。
- ☕ **防焦虑报备机制**：当探测不到新论文时，管家会主动推送灰色的“平安报备”卡片，确认系统正常存活，缓解信息焦虑。
- 🔒 **隐私与工程化**：极简的代码架构，通过 `.env` 文件隔离所有敏感密钥，支持 Bash 脚本一键傻瓜式启动。

---

## 🚀 极速部署指引

### 1. 环境要求
- 任意一台闲置电脑或服务器（Windows/Mac/Linux 均可，**无需独立显卡**）。
- 已安装 Python 3.8 或以上版本。

### 2. 获取密钥
- **智谱 API Key**：前往 [智谱 AI 开放平台](https://open.bigmodel.cn/) 免费注册并获取 API Key。
- **飞书 Webhook**：在飞书群聊中添加“自定义机器人”，安全设置选择“自定义关键词”，并**务必填入关键词：`管家`**，随后复制 Webhook 链接。

### 3. 克隆与配置

将本仓库克隆到本地：

git clone [https://github.com/你的用户名/你的仓库名.git](https://github.com/你的用户名/你的仓库名.git)
cd 你的仓库名
在项目根目录下新建一个名为 .env 的文件，并填入你的私密信息：

ZHIPU_API_KEY="your_zhipu_api_key_here"  

FEISHU_WEBHOOK_URL="your_feishu_webhook_url_here" 

### 4. 自定义雷达设置 (灵活)
打开 config.yaml，你可以自由修改你想要监控的学术关键词、顶会名单，以及每天推送的时间：

YAML
keywords:
  - "VLA"
  - "Humanoid"
venues: "CoRL,ICRA,IROS"
schedule_times:
  - "08:30"
  - "18:30"
### 5. 一键启动
赋予脚本执行权限并运行：

Bash
chmod +x start.sh
./start.sh


📄 许可证
本项目采用 MIT 许可证，欢迎自由探索与改造。