import random
import requests
import json
import openai
import time
import chardet

# 飞书 API 凭证
APP_ID = "cli_a72cf73ea8f8100d"
APP_SECRET = "f4wNuPtiZtHtBnSx0rXeef3n5LXPcqwr"

# 飞书 API 地址
FEISHU_API_URL = "https://open.feishu.cn/open-apis"

# DeepSeek API 配置
DEEPSEEK_API_KEY = 'sk-ffef30431d49412690e9ce91192b5cb8'
openai.api_key = DEEPSEEK_API_KEY
openai.api_base = 'https://api.deepseek.com/beta'

# 获取 tenant_access_token
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
def send_message_to_group(tenant_access_token, chat_id, message):
    url = f"{FEISHU_API_URL}/message/v4/send/"

    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }

    payload = {
        "chat_id": chat_id,
        "msg_type": "text",
        "content": {
            "text": message
        }
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

# **从日志中读取最近的推文**
def read_latest_tweets_from_log(log_file='tweet_monitor.log', num_tweets=10):
    try:
        # 自动检测文件编码
        with open(log_file, 'rb') as f:
            raw_data = f.read(10000)  # 读取部分文件内容以检测编码
            result = chardet.detect(raw_data)
            file_encoding = result['encoding']

        # 读取文件
        with open(log_file, 'r', encoding=file_encoding) as f:
            lines = f.readlines()

        print(f"日志文件内容（前20行）：{lines[:20]}")  # 调试日志格式

        tweets = []
        temp_tweet = None
        temp_url = None

        for line in lines:
            line = line.replace("\\U0001f4c4", "📄").replace("\\U0001f517", "🔗")  # 修正 Unicode 编码问题
            print(f"解析的日志行: {line.strip()}")  # 打印日志行，确保替换成功

            if "📄 内容:" in line:
                temp_tweet = line.split("📄 内容:")[1].strip()
            elif "🔗 链接:" in line and temp_tweet:
                temp_url = line.split("🔗 链接:")[1].strip()
                tweets.append((temp_tweet, temp_url))
                temp_tweet = None  # 重置变量
                temp_url = None

        print(f"成功提取推文 {len(tweets)} 条")
        return tweets[-num_tweets:]  # 返回最近的 num_tweets 条
    except Exception as e:
        print(f"读取日志文件失败: {e}")
        return []

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

# 发送推文和翻译结果到飞书
def send_to_feishu(tweet_text, translated_text, tweet_url, tenant_access_token, target_chat_id):
    message = f"🦅 最近的推文:\n\n{tweet_text}\n\n翻译:\n\n{translated_text}\n\n🔗 {tweet_url}"
    send_message_to_group(tenant_access_token, target_chat_id, message)

# 处理日志中的推文并发送到飞书
def process_tweets_from_log():
    tweets = read_latest_tweets_from_log()

    if not tweets:
        print("没有找到推文内容。")
        return

    # **修正: 确保 tweets 至少有 3 条**
    num_selected = min(len(tweets), 3)
    selected_tweets = random.sample(tweets, num_selected)

    # 获取 tenant_access_token
    tenant_access_token = get_tenant_access_token()
    if not tenant_access_token:
        print("无法获取 tenant_access_token，程序终止。")
        return

    # 目标群聊 ID
    target_chat_id = "oc_652900f809bc482b3e5e1ad5dab046dd"

    for tweet_text, tweet_url in selected_tweets:
        translated_text = translate_tweet(tweet_text)
        send_to_feishu(tweet_text, translated_text, tweet_url, tenant_access_token, target_chat_id)

if __name__ == "__main__":
    print("启动日志推文处理程序...")
    process_tweets_from_log()
