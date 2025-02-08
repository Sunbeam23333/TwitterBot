import random
import requests
import json
import openai
import time
import chardet
import tweepy
import logging
import schedule
import threading
from datetime import datetime

# ===== 飞书 API 配置 =====
APP_ID = "cli_a72cf73ea8f8100d"
APP_SECRET = "f4wNuPtiZtHtBnSx0rXeef3n5LXPcqwr"
FEISHU_API_URL = "https://open.feishu.cn/open-apis"
TARGET_CHAT_ID = "oc_652900f809bc482b3e5e1ad5dab046dd"  # 目标群聊 ID

# ===== Twitter API V2 配置 =====
BEARER_TOKEN = 'YOUR_TWITTER_BEARER_TOKEN'
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# ===== DeepSeek API 配置 =====
DEEPSEEK_API_KEY = 'YOUR_DEEPSEEK_API_KEY'
openai.api_key = DEEPSEEK_API_KEY
openai.api_base = 'https://api.deepseek.com/beta'

# ===== 日志配置 =====
logging.basicConfig(filename="tweet_monitor.log", level=logging.INFO, format='%(asctime)s - %(message)s')

# 记录已获取的推文，避免重复处理（持久化存储）
SEEN_TWEETS_FILE = "seen_tweets.json"

def load_seen_tweets():
    """ 读取已记录的推文 ID """
    try:
        with open(SEEN_TWEETS_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_seen_tweets(seen_tweets):
    """ 保存已记录的推文 ID """
    with open(SEEN_TWEETS_FILE, "w") as f:
        json.dump(list(seen_tweets), f)

seen_tweets = load_seen_tweets()

# ===== 飞书 API 相关函数 =====

def get_tenant_access_token():
    """ 获取 Tenant Access Token """
    url = f"{FEISHU_API_URL}/auth/v3/tenant_access_token/internal/"
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        result = response.json()
        return result.get('tenant_access_token') if result.get('code') == 0 else None
    return None

def send_feishu_message(tenant_access_token, chat_id, content):
    """ 发送消息到飞书群聊，失败时自动重试 3 次 """
    url = f"{FEISHU_API_URL}/message/v4/send/"
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    # 确保内容不会超出 Feishu 限制（2000 字符）
    if len(content) > 2000:
        content = content[:2000] + "..."

    payload = {
        "chat_id": chat_id,
        "msg_type": "text",
        "content": {"text": content}  # 确保 Feishu API 解析正确
    }
    
    for _ in range(3):  # 失败重试 3 次
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        if response.status_code == 200 and result.get('code') == 0:
            print("✅ 消息发送成功")
            return
        
        print(f"⚠️ 消息发送失败: {result}")
        time.sleep(2)  # 重试前等待 2 秒

# ===== 推文获取与日志记录 =====

def fetch_and_log_tweets():
    """ 获取最新的马斯克推文并记录到日志 """
    try:
        query = "elonmusk -is:retweet"
        response = client.search_recent_tweets(query=query, max_results=10)

        if response.data:
            with open("tweet_monitor.log", "a", encoding="utf-8-sig", errors="replace") as log_file:
                for tweet in response.data:
                    tweet_id = str(tweet.id)
                    if tweet_id in seen_tweets:
                        continue  # 避免重复记录相同推文
                    seen_tweets.add(tweet_id)

                    tweet_url = f"https://twitter.com/{tweet.author_id}/status/{tweet_id}"
                    tweet_text = tweet.text.replace("\n", " ")  # 去除换行符
                    tweet_text = tweet_text.encode('utf-8', 'ignore').decode('utf-8')  # 处理编码问题

                    log_entry = f"📄 内容: {tweet_text}\n🔗 链接: {tweet_url}\n"
                    log_file.write(log_entry)
                    logging.info(log_entry)
            
            save_seen_tweets(seen_tweets)  # 记录已处理的推文，防止重复
            print("✅ 推文已记录到日志")
        else:
            print("⚠️ 未获取到新的推文")
    except tweepy.TweepyException as e:
        print(f"❌ 获取推文失败: {e}")

def read_latest_tweets_from_log(log_file='tweet_monitor.log', num_tweets=10):
    """ 从日志文件读取最新的 10 条推文 """
    try:
        with open(log_file, 'r', encoding="utf-8-sig", errors="replace") as f:
            lines = f.readlines()

        tweets = []
        temp_tweet = None
        temp_url = None

        for line in lines:
            if "📄 内容:" in line:
                temp_tweet = line.split("📄 内容:")[1].strip()
            elif "🔗 链接:" in line and temp_tweet:
                temp_url = line.split("🔗 链接:")[1].strip()
                tweets.append((temp_tweet, temp_url))
                temp_tweet = None
                temp_url = None

        print(f"✅ 成功提取推文 {len(tweets)} 条")
        return tweets[-num_tweets:]  # 返回最近的 num_tweets 条
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")
        return []

# ===== 翻译推文 =====

def translate_tweet(tweet_text):
    """ 使用 DeepSeek 翻译推文 """
    try:
        response = openai.ChatCompletion.create(
            model="deepseek-reasoner",
            messages=[{"role": "system", "content": "你是一个翻译助手，负责准确翻译内容。"},
                      {"role": "user", "content": f"请将以下内容翻译成中文: {tweet_text}"}],
            stream=False
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"翻译失败: {e}")
        return "翻译失败"

def process_tweets_from_log():
    """ 从日志读取推文、翻译并发送到飞书 """
    tweets = read_latest_tweets_from_log()
    if not tweets:
        print("没有找到推文内容。")
        return

    selected_tweets = random.sample(tweets, min(len(tweets), 3))
    tenant_access_token = get_tenant_access_token()
    if not tenant_access_token:
        return

    for tweet_text, tweet_url in selected_tweets:
        translated_text = translate_tweet(tweet_text)
        message = f"🦅 马斯克最新推文:\n\n{tweet_text}\n\n翻译:\n{translated_text}\n\n🔗 {tweet_url}"
        send_feishu_message(tenant_access_token, TARGET_CHAT_ID, message)

# ===== 定时任务 =====
scheduler = schedule.Scheduler()
scheduler.every(180).minutes.do(fetch_and_log_tweets)
scheduler.every(180).minutes.do(process_tweets_from_log)

while True:
    scheduler.run_pending()
    time.sleep(1)
