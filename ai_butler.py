import os
import requests
from zhipuai import ZhipuAI
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

# ================= 1. 环境初始化 =================
# 加载 .env 文件中的变量
load_dotenv()

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL")

# 安全校验：如果没有读到密钥，直接报错停止，防止瞎跑
if not ZHIPU_API_KEY or not FEISHU_WEBHOOK_URL:
    print("❌ 致命错误：未检测到 API Key 或 Webhook 链接！请检查 .env 文件。")
    exit(1)

# ================= 2. 专属配置区 =================
TARGET_KEYWORDS = [
    "VLA", "End-to-End", "Embodied", "Humanoid", "Manipulation", 
    "Sim-to-Real", "Reinforcement Learning", "Dexterous", "Diffusion"
]
TARGET_VENUES = "CoRL,ICRA,IROS,RSS,Science Robotics,IEEE Transactions on Robotics"

client = ZhipuAI(api_key=ZHIPU_API_KEY)

# ================= 3. 核心功能函数 =================
def fetch_top_tier_papers():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 雷达升级！正在扫描全球机器人顶会/顶刊...")
    unique_papers = {} 
    current_year = datetime.now().year
    year_range = f"{current_year-1}-{current_year}" 

    for keyword in TARGET_KEYWORDS:
        print(f"  -> 正在检索关键词: {keyword} ...")
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": keyword,
            "venue": TARGET_VENUES,
            "year": year_range,
            "fields": "title,abstract,url,venue,year",
            "limit": 3 
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    for paper in data['data']:
                        if not paper.get('abstract'): 
                            continue
                        title = paper.get('title')
                        if title not in unique_papers:
                            venue_name = paper.get('venue', '顶级会议')
                            year = paper.get('year', current_year)
                            unique_papers[title] = {
                                "title": f"[{venue_name} {year}] {title}", 
                                "link": paper.get('url', 'https://www.semanticscholar.org/'),
                                "summary": paper.get('abstract')
                            }
            time.sleep(1) 
        except Exception as e:
            print(f"检索 {keyword} 时网络开小差了: {e}")
            
    return list(unique_papers.values())[:3] 

def ai_summarize(paper):
    print(f"正在请智谱AI精读顶会文章: {paper['title'][:30]}...")
    prompt = f"""
    你是一个顶级的具身智能与机器人学术助理。请阅读以下这篇最新发表在顶级会议/期刊上的论文摘要，用中文为我总结。
    要求：
    1. 用一句大白话概括它解决了什么行业痛点。
    2. 列出2-3个核心创新点。
    3. 语气专业且精炼。
    
    论文标题：{paper['title']}
    论文摘要：{paper['summary']}
    """
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "你是一个严谨的学术助手。"},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"AI总结失败: {e}"

def push_to_feishu(paper_title, ai_summary, paper_link):
    print("正在推送硬核情报到飞书...")
    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": "👑 顶会情报速递 (管家特供)"},
                "template": "red" 
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"**📄 论文标题：**\n{paper_title}\n\n**💡 核心提炼：**\n{ai_summary}"
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "🔗 点击阅读原文"},
                            "type": "primary",
                            "url": paper_link
                        }
                    ]
                }
            ]
        }
    }
    response = requests.post(FEISHU_WEBHOOK_URL, json=payload)
    if response.json().get("code") == 0:
        print("✅ 飞书情报推送成功！")
    else:
        print(f"❌ 飞书推送失败被拦截！报错信息: {response.json()}")

def push_empty_notice_to_feishu():
    print("没有发现新论文，正在向飞书汇报平安...")
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
                    "content": "**报告老板：**\n\n刚刚完成了一次全球机器人顶会/顶刊的深度扫描。\n\n**🔍 结果：** 在您设定的核心关键词领域内，过去几个小时内**没有**探测到高价值的新论文发布。\n\n您可以安心喝杯咖啡，管家会继续在后台为您盯盘！☕️"
                }
            ]
        }
    }
    requests.post(FEISHU_WEBHOOK_URL, json=payload)
    print("✅ 无更新平安报备推送成功！")

def job():
    papers = fetch_top_tier_papers()
    if not papers:
        push_empty_notice_to_feishu()
        return
    for paper in papers:
        summary = ai_summarize(paper)
        push_to_feishu(paper["title"], summary, paper["link"])
        time.sleep(2)
    print("顶会情报汇报完毕！")

# ================= 4. 主程序入口 =================
if __name__ == "__main__":
    print("启动成功！工程化 AI管家已在后台待命...")
    schedule.every().day.at("08:30").do(job)
    schedule.every().day.at("18:30").do(job)

    print("正在进行首次顶会扫描，请稍候...")
    job() 

    while True:
        schedule.run_pending()
        time.sleep(60)