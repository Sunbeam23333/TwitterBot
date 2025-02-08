import random
import requests
import json
import openai
import time
import chardet
import tweepy
import logging
import schedule
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

# ===== 飞书 API 相关函数 =====

# 获取 Tenant Access Token
def get_tenant_access_token():
    url = f"{FEISHU_API_URL}/auth/v3/tenant_access_token/internal/"
    payload = {
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }
    response = requests.post(url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            return result['tenant_access_token']
        else:
            print(f"获取 tenant_access_token 失败: {result.get('msg')}")
    else:
        print(f"请求失败: {response.status_code} - {response.text}")
    
    return None

# 发送消息到指定群聊
def send_feishu_message(tenant_access_token, chat_id, content):
    url = f"{FEISHU_API_URL}/message/v4/send/"

    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    payload = {
        "chat_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": content})
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            print("消息发送成功")
        else:
            print(f"消息发送失败: {result.get('msg')}")
    else:
        print(f"请求失败: {response.status_code} - {response.text}")

# ===== 推文获取与日志记录 =====

# 获取最新的马斯克推文并记录到日志
def fetch_and_log_tweets():
    try:
        query = "elonmusk -is:retweet"
        response = client.search_recent_tweets(query=query, max_results=10)  # 获取最多10条推文

        if response.data:
            with open("tweet_monitor.log", "a", encoding="utf-8") as log_file:
                for tweet in response.data:
                    tweet_url = f"https://twitter.com/{tweet.author_id}/status/{tweet.id}"
                    tweet_text = tweet.text.replace("\n", " ")  # 去除换行符
                    log_entry = f"📄 内容: {tweet_text}\n🔗 链接: {tweet_url}\n"
                    log_file.write(log_entry)
                    logging.info(log_entry)
            print("推文已记录到日志。")
        else:
            print("未获取到新的推文。")

    except tweepy.TweepyException as e:
        print(f"获取推文失败: {e}")

# **从日志中读取最近的推文**
def read_latest_tweets_from_log(log_file='tweet_monitor.log', num_tweets=10):
    try:
        with open(log_file, 'rb') as f:
            raw_data = f.read(10000)
            result = chardet.detect(raw_data)
            file_encoding = result['encoding']

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

        print(f"成功提取推文 {len(tweets)} 条")
        return tweets[-num_tweets:]  # 返回最近的 num_tweets 条
    except Exception as e:
        print(f"读取日志文件失败: {e}")
        return []

# ===== 翻译推文 =====

# 翻译推文
def translate_tweet(tweet_text):
    translation_response = openai.ChatCompletion.create(
        model="deepseek-reasoner",
        messages=[
            {"role": "system", "content": "你是一个翻译助手，负责准确翻译内容。"},
            {"role": "user", "content": f"请将以下内容翻译成中文: {tweet_text}"}
        ],
        stream=False
    )

    translated_text = translation_response['choices'][0]['message']['content']
    print(f"翻译后的推文: {translated_text}")
    return translated_text

# 处理推文并发送到飞书
def process_tweets_from_log():
    tweets = read_latest_tweets_from_log()

    if not tweets:
        print("没有找到推文内容。")
        return

    num_selected = min(len(tweets), 3)
    selected_tweets = random.sample(tweets, num_selected)

    tenant_access_token = get_tenant_access_token()
    if not tenant_access_token:
        print("无法获取 tenant_access_token，程序终止。")
        return

    for tweet_text, tweet_url in selected_tweets:
        translated_text = translate_tweet(tweet_text)
        message_content = (
            f"🦅 马斯克最近的推文:\n\n"
            f"{tweet_text}\n\n"
            f"翻译:\n{translated_text}\n\n"
            f"🔗 {tweet_url}"
        )
        send_feishu_message(tenant_access_token, TARGET_CHAT_ID, message_content)

# ===== 定时任务 =====
CHECK_INTERVAL = 0.1  # 每 0.1 分钟（6 秒）检查一次推文，可以换成180min

if __name__ == "__main__":
    print("启动推特监控服务...")
    scheduler = schedule.Scheduler()
    
    scheduler.every(CHECK_INTERVAL).minutes.do(fetch_and_log_tweets)  # 先抓取推文并写入日志
    scheduler.every(CHECK_INTERVAL).minutes.do(process_tweets_from_log)  # 读取最新推文并翻译

    try:
        while True:
            scheduler.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("服务已停止")
