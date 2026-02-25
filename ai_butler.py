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
    print("❌ 致命错误：未检测到 API Key 或 Webhook 链接！请检查 .env 文件。")
    exit(1)

try:
    with open("config.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        TARGET_KEYWORDS = config.get("keywords", [])
        TARGET_VENUES = config.get("venues", "")
        SCHEDULE_TIMES = config.get("schedule_times", ["08:30", "18:30"])
        
        # 💡 新的配置读取逻辑
        MAX_PER_KEYWORD = config.get("max_papers_per_keyword", 1)
        MAX_TOTAL_PUSH = config.get("max_total_push", 5)
except FileNotFoundError:
    print("❌ 致命错误：找不到 config.yaml 配置文件！")
    exit(1)

client = ZhipuAI(api_key=ZHIPU_API_KEY)

# ================= 2. 历史记忆读取 (永久去重) =================
HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history_list):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history_list, f, ensure_ascii=False, indent=2)

# ================= 3. 核心功能函数 =================
def fetch_top_tier_papers():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📡 具身雷达启动！正在扫描全球机器人顶会/顶刊...")
    unique_papers = {} 
    current_year = datetime.now().year
    year_range = f"{current_year-1}-{current_year}" 
    
    pushed_history = load_history()

    for keyword in TARGET_KEYWORDS:
        print(f"  -> 正在检索关键词: {keyword} ...")
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": keyword,
            "venue": TARGET_VENUES,
            "year": year_range,
            "fields": "title,abstract,url,venue,year,authors,publicationDate",
            "limit": 10 
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'data' in data:
                    added_for_this_keyword = 0  # 💡 记录当前关键词找到了几篇新论文
                    
                    for paper in data['data']:
                        if not paper.get('abstract'): 
                            continue
                            
                        raw_title = paper.get('title')
                        
                        # 如果这篇论文之前没被推过
                        if raw_title not in unique_papers and raw_title not in pushed_history:
                            # 💡 核心修复：如果这个领域已经抓够了名额，就跳出循环，把机会留给下一个领域！
                            if added_for_this_keyword >= MAX_PER_KEYWORD:
                                break 
                                
                            venue_name = paper.get('venue', '顶级会议')
                            pub_date = paper.get('publicationDate') or str(paper.get('year', current_year))
                            
                            authors_list = paper.get('authors', [])
                            author_names = [a.get('name') for a in authors_list if a.get('name')]
                            if len(author_names) > 3:
                                author_str = ", ".join(author_names[:3]) + " 等"
                            else:
                                author_str = ", ".join(author_names) if author_names else "未知"
                            
                            unique_papers[raw_title] = {
                                "title": raw_title, 
                                "venue": venue_name,
                                "date": pub_date,
                                "authors": author_str,
                                "link": paper.get('url', 'https://www.semanticscholar.org/'),
                                "summary": paper.get('abstract'),
                                "raw_title": raw_title 
                            }
                            added_for_this_keyword += 1
                            
            time.sleep(1) 
        except Exception as e:
            print(f"检索 {keyword} 时网络开小差了: {e}")
            
    # 💡 最终限制总数，防止一次性轰炸飞书
    return list(unique_papers.values())[:MAX_TOTAL_PUSH] 

def ai_summarize(paper):
    print(f"正在请智谱AI精读顶会文章: {paper['title'][:30]}...")
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
    论文标题：{paper['title']}
    论文摘要：{paper['summary']}
    """
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": "你是一个冷酷、精炼的顶级学术机器，绝对遵循输出格式规范。"},
                {"role": "user", "content": prompt}
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"**⚠️ AI总结失败：** {e}"

def push_to_feishu(paper):
    print("正在推送硬核情报到飞书...")
    venue = paper.get('venue', '顶级会议')
    title = paper['title']
    authors = paper['authors']
    date = paper['date']
    ai_summary = paper['ai_summary']
    link = paper['link']

    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "title": {"tag": "plain_text", "content": f"👑 {venue} 最新收录 (管家特供)"},
                "template": "red" 
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"**《{title}》**\n\n<font color='grey'>👥 作者：{authors}</font>\n<font color='grey'>📅 发表日期：{date}</font>\n\n---\n\n{ai_summary}"
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "🔗 点击阅读原文"},
                            "type": "primary",
                            "url": link
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
                    "content": "**报告老板：**\n\n刚刚完成了一次全球机器人顶会/顶刊的深度扫描。\n\n**🔍 结果：** 过去几个小时内，在您的**所有关注领域**均未发现未读的高价值新论文。\n\n您可以安心喝杯咖啡，EmboRadar 会继续在后台为您盯盘！☕️"
                }
            ]
        }
    }
    requests.post(FEISHU_WEBHOOK_URL, json=payload)
    print("✅ 无更新平安报备推送成功！")

def job():
    papers = fetch_top_tier_papers()
    
    # 💡 只有当所有领域加起来都没有1篇新论文时，才会触发平安逻辑
    if not papers:
        push_empty_notice_to_feishu()
        return
        
    pushed_history = load_history()
    
    for paper in papers:
        paper['ai_summary'] = ai_summarize(paper)
        push_to_feishu(paper)
        
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