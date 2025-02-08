import random
import requests
import json
import openai
import time
import chardet
import codecs
import re

# ======= 飞书 API 配置 =======
APP_ID = "cli_a72cf73ea8f8100d"
APP_SECRET = "f4wNuPtiZtHtBnSx0rXeef3n5LXPcqwr"
FEISHU_API_URL = "https://open.feishu.cn/open-apis"
TARGET_CHAT_ID = "oc_652900f809bc482b3e5e1ad5dab046dd"

# ======= DeepSeek API 配置 =======
DEEPSEEK_API_KEY = 'sk-ffef30431d49412690e9ce91192b5cb8'
openai.api_key = DEEPSEEK_API_KEY
openai.api_base = 'https://api.deepseek.com/beta'

# ✅ 获取 tenant_access_token
def get_tenant_access_token():
    url = f"{FEISHU_API_URL}/auth/v3/tenant_access_token/internal/"
    payload = {"app_id": APP_ID, "app_secret": APP_SECRET}
    response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            return result['tenant_access_token']
    print(f"❌ 获取 tenant_access_token 失败: {response.text}")
    return None

# ✅ 发送消息到指定群聊
def send_message_to_group(tenant_access_token, chat_id, message):
    url = f"{FEISHU_API_URL}/message/v4/send/"
    headers = {"Authorization": f"Bearer {tenant_access_token}", "Content-Type": "application/json; charset=utf-8"}
    payload = {"chat_id": chat_id, "msg_type": "text", "content": {"text": message}}

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200 and response.json().get('code') == 0:
        print("✅ 消息发送成功")
    else:
        print(f"❌ 消息发送失败: {response.text}")

# ✅ 读取最新推文
def read_latest_tweets_from_log(log_file='tweet_monitor.log', num_tweets=10):
    try:
        with open(log_file, 'rb') as f:
            raw_data = f.read(10000)
            file_encoding = chardet.detect(raw_data)['encoding'] or 'utf-8'

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
                temp_tweet, temp_url = None, None

        print(f"✅ 成功提取推文 {len(tweets)} 条")
        return tweets[-num_tweets:]
    except Exception as e:
        print(f"❌ 读取日志文件失败: {e}")
        return []

# ✅ 翻译推文（增加 API 响应调试）
def translate_tweet(tweet_text):
    try:
        response = openai.ChatCompletion.create(
            model="deepseek-reasoner",
            messages=[
                {"role": "system", "content": "你是一个翻译助手，负责准确翻译内容。"},
                {"role": "user", "content": f"请将以下内容翻译成中文: {tweet_text}"}
            ],
            stream=False
        )

        print("🔍 DeepSeek API 响应:", response)  # ✅ 调试 API 返回数据

        # 修正：检查响应内容
        if 'choices' in response and response['choices']:
            return response['choices'][0].get('message', {}).get('content', "翻译失败")
        return "翻译失败"
    except Exception as e:
        print(f"❌ 翻译失败: {e}")
        return "翻译失败"

# ✅ 发送翻译推文到飞书
def send_to_feishu(tweet_text, translated_text, tweet_url, tenant_access_token, target_chat_id):
    message = f"🦅 最近的推文:\n\n{tweet_text}\n\n翻译:\n\n{translated_text}\n\n🔗 {tweet_url}"
    send_message_to_group(tenant_access_token, target_chat_id, message)

# ✅ 处理推文并发送到飞书
def process_tweets_from_log():
    tweets = read_latest_tweets_from_log()
    if not tweets:
        print("⚠️ 没有找到推文内容。")
        return

    # 修正：如果推文不足 3 条，避免 random.sample() 失败
    selected_tweets = random.sample(tweets, min(len(tweets), 3))

    tenant_access_token = get_tenant_access_token()
    if not tenant_access_token:
        print("❌ 无法获取 tenant_access_token，程序终止。")
        return

    for tweet_text, tweet_url in selected_tweets:
        translated_text = translate_tweet(tweet_text)
        send_to_feishu(tweet_text, translated_text, tweet_url, tenant_access_token, TARGET_CHAT_ID)

if __name__ == "__main__":
    print("🚀 启动日志推文处理程序...")
    process_tweets_from_log()
