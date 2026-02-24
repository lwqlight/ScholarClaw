import os
import requests
import yaml
import json
from zhipuai import ZhipuAI
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv

# ================= 1. 环境与配置初始化 =================
load_dotenv()
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY")
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL")

if not ZHIPU_API_KEY or not FEISHU_WEBHOOK_URL:
    print("❌ 致命错误：未检测到 API Key 或 Webhook 链接！")
    exit(1)

try:
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        TARGET_KEYWORDS = config.get("keywords", [])
        TARGET_VENUES = config.get("venues", "")
        SCHEDULE_TIMES = config.get("schedule_times", ["08:30", "18:30"])
        # 💡 读取配置文件里的推送数量，默认是 3
        MAX_PAPERS = config.get("max_papers_per_push", 3)
except FileNotFoundError:
    print("❌ 致命错误：找不到 config.yaml 配置文件！")
    exit(1)

client = ZhipuAI(api_key=ZHIPU_API_KEY)

# ================= 2. 历史记忆读取 (真正的永久去重) =================
HISTORY_FILE = "history.json"

def load_history():
    """读取已经推送过的论文标题记录"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history_list):
    """保存推送过的论文标题到本地"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)

# ================= 3. 核心功能函数 =================
def fetch_top_tier_papers():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📡 具身雷达启动！正在扫描全球机器人顶会/顶刊...")
    unique_papers = {} 
    current_year = datetime.now().year
    year_range = f"{current_year-1}-{current_year}" 
    
    # 加载小本本，看看以前推过什么
    pushed_history = load_history()

    for keyword in TARGET_KEYWORDS:
        print(f"  -> 正在检索关键词: {keyword} ...")
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": keyword,
            "venue": TARGET_VENUES,
            "year": year_range,
            "fields": "title,abstract,url,venue,year",
            # 这里的 limit 设得稍微大一点(比如10)，为了获取足够多的基数来进行去重过滤
            "limit": 10 
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    for paper in data['data']:
                        if not paper.get('abstract'): 
                            continue
                            
                        raw_title = paper.get('title')
                        
                        # 💡 终极去重逻辑：不仅本次循环没出现过，而且历史小本本里也没出现过！
                        if raw_title not in unique_papers and raw_title not in pushed_history:
                            venue_name = paper.get('venue', '顶级会议')
                            year = paper.get('year', current_year)
                            unique_papers[raw_title] = {
                                "title": f"[{venue_name} {year}] {raw_title}", 
                                "link": paper.get('url', 'https://www.semanticscholar.org/'),
                                "summary": paper.get('abstract'),
                                "raw_title": raw_title # 保存原始标题用于记录历史
                            }
            time.sleep(1) 
        except Exception as e:
            print(f"检索 {keyword} 时网络开小差了: {e}")
            
    # 💡 使用配置项 MAX_PAPERS 控制最终返回的数量
    return list(unique_papers.values())[:MAX_PAPERS] 

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
                    "content": "**报告老板：**\n\n刚刚完成了一次全球机器人顶会/顶刊的深度扫描。\n\n**🔍 结果：** 过去几个小时内，在您的关注领域**没有**发现未读的高价值新论文。\n\n您可以安心喝杯咖啡，具身雷达会继续在后台为您盯盘！☕️"
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
        
    pushed_history = load_history()
    
    for paper in papers:
        summary = ai_summarize(paper)
        push_to_feishu(paper["title"], summary, paper["link"])
        
        # 💡 推送成功后，把论文原始标题记入本地历史库
        pushed_history.append(paper["raw_title"])
        save_history(pushed_history)
        
        time.sleep(2)
        
    print("顶会情报汇报完毕！")

# ================= 4. 主程序入口 =================
if __name__ == "__main__":
    print("启动成功！EmboRadar (具身雷达) 已在后台待命...")
    
    for t in SCHEDULE_TIMES:
        schedule.every().day.at(t).do(job)
        print(f"已设定定时任务: 每天 {t} 自动扫描")

    print("正在进行首次雷达扫描，请稍候...")
    job() 

    while True:
        schedule.run_pending()
        time.sleep(60)