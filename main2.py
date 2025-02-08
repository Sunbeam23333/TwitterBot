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
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAAM41ywEAAAAAAvWrLb8Bl7FdoVPl9FnF34S3QxI%3DrDeieu40fY1JP51BQNxGELwxygrWeVjds1LuhJOmnexvVLzU9n'
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# ===== DeepSeek API 配置 =====
DEEPSEEK_API_KEY = 'sk-ffef30431d49412690e9ce91192b5cb8'
openai.api_key = DEEPSEEK_API_KEY
openai.api_base = 'https://api.deepseek.com/beta'

# ===== 日志配置 =====
logging.basicConfig(filename="tweet_monitor.log", level=logging.INFO, format='%(asctime)s - %(message)s')

# 记录已获取的推文，避免重复处理
seen_tweets = set()

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
    payload = {"chat_id": chat_id, "msg_type": "text", "content": json.dumps({"text": content})}
    
    for _ in range(3):  # 失败重试 3 次
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200 and response.json().get('code') == 0:
            print("消息发送成功")
            return
        time.sleep(2)
    print(f"消息发送失败: {response.text}")

# ===== 推文获取与日志记录 =====

def fetch_and_log_tweets():
    """ 获取最新的马斯克推文并记录到日志 """
    try:
        query = "elonmusk -is:retweet"
        response = client.search_recent_tweets(query=query, max_results=10)

        if response.data:
            with open("tweet_monitor.log", "a", encoding="utf-8") as log_file:
                for tweet in response.data:
                    tweet_id = tweet.id
                    if tweet_id in seen_tweets:
                        continue  # 避免重复记录相同推文
                    seen_tweets.add(tweet_id)

                    tweet_url = f"https://twitter.com/{tweet.author_id}/status/{tweet_id}"
                    tweet_text = tweet.text.replace("\n", " ")  # 去除换行符
                    log_entry = f"📄 内容: {tweet_text}\n🔗 链接: {tweet_url}\n"
                    log_file.write(log_entry)
                    logging.info(log_entry)
            print("推文已记录到日志。")
        else:
            print("未获取到新的推文。")
    except tweepy.TweepyException as e:
        print(f"获取推文失败: {e}")

def read_latest_tweets_from_log(log_file='tweet_monitor.log', num_tweets=10):
    """ 从日志文件读取最新的 10 条推文 """
    try:
        with open(log_file, 'rb') as f:
            raw_data = f.read(10000)
            file_encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'

        with open(log_file, 'r', encoding=file_encoding) as f:
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

        return tweets[-num_tweets:]  # 返回最近的 num_tweets 条
    except Exception as e:
        print(f"读取日志文件失败: {e}")
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
        message = f"🦅 马斯克最近的推文:\n\n{tweet_text}\n\n翻译:\n{translated_text}\n\n🔗 {tweet_url}"
        send_feishu_message(tenant_access_token, TARGET_CHAT_ID, message)

# ===== 定时任务 =====
CHECK_INTERVAL = 180  # 改为 180 分钟（3 小时）
scheduler = schedule.Scheduler()
scheduler.every(CHECK_INTERVAL).minutes.do(fetch_and_log_tweets)
scheduler.every(CHECK_INTERVAL).minutes.do(process_tweets_from_log)

while True:
    scheduler.run_pending()
    time.sleep(1)
