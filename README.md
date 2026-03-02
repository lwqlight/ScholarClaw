# 📡 EmboRadar (具身雷达) - WebUI 可视化版

![Python Version](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Gradio](https://img.shields.io/badge/UI-Gradio-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**专为具身智能 (Embodied AI) 与机器人学打造的 24 小时 AI 前沿文献探测器。**

告别繁琐的代码配置！EmboRadar 现已全面升级为 **Web 可视化版本**。无论你是否懂编程，只需一键启动，即可通过优雅的网页控制台配置你的专属学术管家。它将 24 小时在后台替你“盯盘”全球顶会，并使用大语言模型（如智谱 GLM-4）将晦涩的英文摘要提炼为极具极客美感的中文硬核卡片，直接推送到你的飞书工作台。

---

## 📸 效果展示 (Demo)

### 1. 极简 Web 控制台 (0 代码配置)
只需在网页上点点点，即可完成所有复杂的 API 和监控规则配置，配置会自动持久化保存。
![EmboRadar WebUI 控制台](data/webui_demo.png)

### 2. 硬核飞书推送 (三分段提炼)
强制大模型采用**“🎯核心痛点 ➡️ 🛠️技术路线 ➡️ ✨创新突破”**的三段式结构，直接降维打击传统的水文罗列：
![EmboRadar 推送效果展示](data/img.jpg)

---

## ✨ 核心特性

- 🖥️ **全可视化操作**：引入 Gradio WebUI，无需手动修改 `.env` 或 `yaml`，密钥和业务配置在网页端一键管理。
- 📦 **傻瓜式一键部署**：内置智能启动脚本，自动识别并利用 Conda 创建隔离环境，自动安装依赖，小白零门槛启动。
- 🎯 **顶会精准雷达**：直连 Semantic Scholar API，精准捕捉 CoRL, ICRA, IROS, RSS 等顶级会议的最新发表动态。
- 🧠 **冷酷 AI 提炼**：严苛的 Prompt 约束，彻底干掉大模型“废话前缀”，精准提取论文的痛点与技术路线。
- 🗄️ **本地永久去重**：内置 `history.json` 记忆中枢，看过的论文绝不推第二遍，支持多领域公平抓取（防截断机制）。
- ☕ **防焦虑报备机制**：当全网探测不到新论文时，管家会主动推送灰色的“平安报备”卡片，确认系统存活，缓解信息焦虑。

---

## 🚀 极速部署指引 (小白友好)

### 1. 基础准备
- 你的电脑上需要安装好 [Miniconda](https://docs.conda.io/en/latest/miniconda.html) 或 Anaconda。
- 准备好你的 **智谱 API Key**（[免费获取](https://open.bigmodel.cn/)） 以及 **飞书群机器人 Webhook 链接**（⚠️ 飞书机器人安全设置请务必包含关键词：`管家`）。

### 2. 下载项目

git clone https://github.com/lwqlight/ScholarClaw
cd ScholarClaw

#### 3. 一键启动
我们为您准备了全自动的启动脚本，会自动安装所有环境并弹开网页：

Windows 用户：双击运行 start.bat

Mac/Linux/WSL 用户：

Bash
chmod +x start.sh
./start.sh
### 4. 网页端配置与运行
终端运行成功后，浏览器会自动打开 http://127.0.0.1:7860。

在 【⚙️ 1. 基础密钥设置】 中填入你的 API Key 和飞书链接。

在 【🧠 2. 雷达扫描规则】 中随心所欲地添加你关心的关键词（如 VLA, Humanoid 等）。

点击 【💾 保存所有配置】。

点击 【⚡ 立刻手动执行一次全网扫描】，去飞书里验收你的硬核情报卡片吧！

💡 提示： 只要这个黑色终端窗口不关，你的 AI 管家就会根据你设定的时间（如每天 08:30 和 18:30），默默在后台为你搜集顶会情报。

🛠️ 底层架构说明 (Geek Only)
对于喜欢折腾的开发者，EmboRadar 依然保持了极其优雅的配置解耦架构：

.env：用于存放并隔离你的敏感密钥，已加入 .gitignore 防止泄露。

config.yaml：业务配置清单，Web 端的所有修改最终会落盘于此。

history.json：本地轻量级数据库，记录已推送的论文原始标题。

📄 许可证
本项目采用 MIT 许可证，欢迎自由探索、Fork 与改造