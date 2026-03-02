import gradio as gr
import os
import yaml
import json
import time
import threading
import schedule
from datetime import datetime
from dotenv import load_dotenv, set_key
import requests
from zhipuai import ZhipuAI

# ================= 1. 基础配置管理 =================
ENV_FILE = ".env"
CONFIG_FILE = "config.yaml"
HISTORY_FILE = "history.json"

# 初始化空文件
if not os.path.exists(ENV_FILE):
    open(ENV_FILE, 'w').close()
if not os.path.exists(CONFIG_FILE):
    default_config = {
        "keywords": ["VLA", "Humanoid", "Sim-to-Real", "End-to-End"],
        "venues": "CoRL,ICRA,IROS,RSS",
        "schedule_times": ["08:30", "18:30"],
        "max_papers_per_keyword": 1,
        "max_total_push": 5
    }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, allow_unicode=True)

load_dotenv(ENV_FILE)

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history_list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)

# ================= 2. 雷达核心逻辑 =================
def run_radar_scan():
    logs = []
    def log(msg):
        timestamp = datetime.now().strftime('%H:%M:%S')
        full_msg = f"[{timestamp}] {msg}"
        print(full_msg)
        logs.append(full_msg)

    log("📡 具身雷达开始扫描...")
    
    load_dotenv(ENV_FILE)
    ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
    FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")
    
    if not ZHIPU_API_KEY or not FEISHU_WEBHOOK_URL:
        log("❌ 错误：请先在【基础设置】中填写 API Key 和 Webhook！")
        return "\n".join(logs)
        
    client = ZhipuAI(api_key=ZHIPU_API_KEY)
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    keywords = config.get("keywords", [])
    venues = config.get("venues", "")
    max_per_kw = config.get("max_papers_per_keyword", 1)
    max_total = config.get("max_total_push", 5)
    
    unique_papers = {}
    pushed_history = load_history()
    year_range = f"{datetime.now().year-1}-{datetime.now().year}"

    for kw in keywords:
        log(f"-> 正在检索关键词: {kw}")
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {"query": kw, "venue": venues, "year": year_range, "fields": "title,abstract,url,venue,year,authors,publicationDate", "limit": 10}
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code == 200:
                data = res.json()
                added = 0
                for paper in data.get('data', []):
                    if not paper.get('abstract'): continue
                    raw_title = paper.get('title')
                    if raw_title not in unique_papers and raw_title not in pushed_history:
                        if added >= max_per_kw: break
                        unique_papers[raw_title] = paper
                        added += 1
            time.sleep(1)
        except Exception as e:
            log(f"⚠️ 检索 {kw} 失败: {e}")

    papers_to_push = list(unique_papers.values())[:max_total]
    
    # 💡 完美还原的平安报备卡片
    if not papers_to_push:
        log("☕ 未发现新论文，发送平安报备...")
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": "☕ 顶会雷达扫描完毕 (管家报备)"},
                    "template": "grey"
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": "**报告老板：**\n\n刚刚完成了一次全球机器人顶会/顶刊的深度扫描。\n\n**🔍 结果：** 过去几个小时内，在您的**所有关注领域**均未发现未读的高价值新论文。\n\n您可以安心喝杯咖啡，EmboRadar 会继续在后台为您盯盘！☕️"
                    }
                ]
            }
        }
        requests.post(FEISHU_WEBHOOK_URL, json=payload)
        return "\n".join(logs)
        
    for p in papers_to_push:
        log(f"🧠 正在请 AI 总结: {p['title'][:20]}...")
        
        # 💡 完美还原的严苛大模型提示词
        prompt = f"""
        你是一个顶级的具身智能与机器人学术助理。请阅读以下论文摘要，并严格按照我提供的 Markdown 格式输出总结。
        
        ⚠️ 注意：禁止输出任何“好的”、“这篇论文”等前缀废话，严格保持客观冷酷的学术语调，直接输出以下结构：
        
        **🎯 核心痛点：**
        (用一句话极其精炼地指出传统方法或当前行业的局限性)
        
        **🛠️ 技术路线：**
        (用1-2句话概括作者使用了什么核心算法、架构、数据集或物理设计来解决上述问题)
        
        **✨ 创新突破：**
        • (核心创新点或实验跑分结果1，不超过30个字)
        • (核心创新点或实验跑分结果2，不超过30个字)
        
        ---
        论文标题：{p['title']}
        论文摘要：{p['abstract']}
        """
        
        try:
            ai_res = client.chat.completions.create(
                model="glm-4-flash", 
                messages=[
                    {"role": "system", "content": "你是一个冷酷、精炼的顶级学术机器，绝对遵循输出格式规范。"},
                    {"role": "user", "content": prompt}
                ]
            )
            ai_summary = ai_res.choices[0].message.content
        except Exception as e:
            ai_summary = f"**⚠️ AI总结失败：** {e}"
            
        authors_list = [a.get('name') for a in p.get('authors', []) if a.get('name')]
        author_str = ", ".join(authors_list[:3]) + (" 等" if len(authors_list)>3 else "")
        date_str = p.get('publicationDate') or str(p.get('year', '未知'))
        venue_str = p.get('venue', '顶级会议')
        
        # 💡 完美还原的论文推送红色卡片
        payload = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": f"👑 {venue_str} 最新收录 (管家特供)"},
                    "template": "red" 
                },
                "elements": [
                    {
                        "tag": "markdown",
                        "content": f"**《{p['title']}》**\n\n<font color='grey'>👥 作者：{author_str}</font>\n<font color='grey'>📅 发表日期：{date_str}</font>\n\n---\n\n{ai_summary}"
                    },
                    {"tag": "hr"},
                    {
                        "tag": "action",
                        "actions": [
                            {
                                "tag": "button",
                                "text": {"tag": "plain_text", "content": "🔗 点击阅读原文"},
                                "type": "primary",
                                "url": p.get('url', '')
                            }
                        ]
                    }
                ]
            }
        }
        
        res = requests.post(FEISHU_WEBHOOK_URL, json=payload)
        if res.json().get("code") == 0:
            log(f"✅ 推送成功: {p['title'][:15]}...")
            pushed_history.append(p['title'])
            save_history(pushed_history)
        else:
            log(f"❌ 推送被拦截: {res.json()}")
        
        time.sleep(5) # 防风控

    log("🎉 扫描及推送任务全部完成！")
    return "\n".join(logs)

# ================= 3. 后台定时任务线程 =================
def run_scheduler():
    while True:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        schedule.clear()
        for t in config.get("schedule_times", ["08:30", "18:30"]):
            schedule.every().day.at(t).do(run_radar_scan)
            
        schedule.run_pending()
        time.sleep(30)

# 启动后台守护线程
threading.Thread(target=run_scheduler, daemon=True).start()

# ================= 4. Gradio Web UI =================
def load_settings():
    load_dotenv(ENV_FILE)
    zhipu = os.getenv("ZHIPU_API_KEY", "")
    feishu = os.getenv("FEISHU_WEBHOOK_URL", "")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        c = yaml.safe_load(f)
    kws = "\n".join(c.get("keywords", []))
    venues = c.get("venues", "")
    times = "\n".join(c.get("schedule_times", []))
    max_k = c.get("max_papers_per_keyword", 1)
    max_t = c.get("max_total_push", 5)
    return zhipu, feishu, kws, venues, times, max_k, max_t

def save_settings(zhipu, feishu, kws, venues, times, max_k, max_t):
    set_key(ENV_FILE, "ZHIPU_API_KEY", zhipu)
    set_key(ENV_FILE, "FEISHU_WEBHOOK_URL", feishu)
    
    new_config = {
        "keywords": [k.strip() for k in kws.split('\n') if k.strip()],
        "venues": venues.strip(),
        "schedule_times": [t.strip() for t in times.split('\n') if t.strip()],
        "max_papers_per_keyword": int(max_k),
        "max_total_push": int(max_t)
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        yaml.dump(new_config, f, allow_unicode=True)
    return "✅ 配置已成功保存！后台定时任务将在1分钟内自动应用新时间。"

with gr.Blocks(title="EmboRadar 控制台", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📡 EmboRadar (具身雷达) 智能体控制台")
    gr.Markdown("无需改代码，填入下方信息即可生成你的专属 24 小时 AI 学术管家。")
    
    with gr.Tabs():
        with gr.TabItem("⚙️ 1. 基础密钥设置"):
            zhipu_input = gr.Textbox(label="智谱 API Key (必填)", type="password", placeholder="填入从智谱开放平台获取的 API Key")
            feishu_input = gr.Textbox(label="飞书 Webhook 链接 (必填)", type="password", placeholder="填入带'管家'关键词的飞书机器人链接")
            
        with gr.TabItem("🧠 2. 雷达扫描规则"):
            with gr.Row():
                with gr.Column():
                    keywords_input = gr.Textbox(label="感兴趣的领域关键词 (每行一个)", lines=6, placeholder="VLA\nHumanoid\nEnd-to-End")
                    venues_input = gr.Textbox(label="监控的顶会/顶刊 (英文逗号隔开)", placeholder="CoRL,ICRA,IROS")
                with gr.Column():
                    times_input = gr.Textbox(label="每日定时推送时间 (每行一个，24小时制)", lines=3, placeholder="08:30\n18:30")
                    max_k_input = gr.Number(label="单个领域每次最多推送几篇？", value=1, precision=0)
                    max_t_input = gr.Number(label="单次运行全局最多推送几篇？", value=5, precision=0)
                    
        with gr.TabItem("🚀 3. 运行与控制"):
            save_btn = gr.Button("💾 保存所有配置", variant="primary")
            save_status = gr.Markdown("")
            
            gr.Markdown("---")
            run_btn = gr.Button("⚡ 立刻手动执行一次全网扫描")
            log_output = gr.Textbox(label="运行日志", lines=10, interactive=False)
            
    # 绑定逻辑
    demo.load(load_settings, inputs=[], outputs=[zhipu_input, feishu_input, keywords_input, venues_input, times_input, max_k_input, max_t_input])
    save_btn.click(save_settings, inputs=[zhipu_input, feishu_input, keywords_input, venues_input, times_input, max_k_input, max_t_input], outputs=[save_status])
    run_btn.click(run_radar_scan, inputs=[], outputs=[log_output])

if __name__ == "__main__":
    print("🌐 正在启动 Web 服务...")
    demo.launch(inbrowser=True, server_port=7860)