import openai
import requests
import json
import logging
from datetime import datetime

# 配置 DeepSeek 和飞书的信息
DEEPSEEK_API_KEY = 'sk-ffef30431d49412690e9ce91192b5cb8'  # 替换 DeepSeek API 密钥
WEBHOOK_URL = 'https://open.feishu.cn/open-apis/bot/v2/hook/8f78cc56-2ec4-4733-ae05-1dca691edfa5'  # 飞书 Webhook 地址
SECRET = '3pxWVhMt5t64h6mGfamHyf'  # 飞书签名校验密钥

# 设置日志记录
logging.basicConfig(filename="tweet_backup.log", level=logging.INFO, format='%(asctime)s - %(message)s')

# 配置 OpenAI API (DeepSeek API)
openai.api_key = DEEPSEEK_API_KEY
openai.api_base = 'https://api.deepseek.com/beta'  # 使用 DeepSeek 的 beta 版本 API

# 获取马斯克最近的推文并翻译
def get_musk_tweet_and_translate():
    # 使用 OpenAI SDK 调用 DeepSeek API 获取马斯克的三条最新推文，按时间排序
    response = openai.ChatCompletion.create(
        model="deepseek-chat",  # 使用 DeepSeek 的聊天模型
        messages=[
            {"role": "system", "content": "你是一个有帮助的助手。"},
            {"role": "user", "content": "请给我查询马斯克最近的三条推文，并按时间排序，内容不包括转发。"}
        ],
        stream=False
    )

    tweet_text = response['choices'][0]['message']['content']
    print(f"获取的推文: {tweet_text}")

    # 翻译推文
    translation_response = openai.ChatCompletion.create(
        model="deepseek-reasoner",  # 使用 DeepSeek 的推理模型进行翻译
        messages=[
            {"role": "system", "content": "你是一个翻译助手，负责准确翻译内容。"},
            {"role": "user", "content": f"请将以下内容翻译成中文: {tweet_text}"}
        ],
        stream=False
    )

    translated_text = translation_response['choices'][0]['message']['content']
    print(f"翻译后的推文: {translated_text}")
    return tweet_text, translated_text

# 发送推文到飞书
def send_to_feishu(tweet_text, translated_text):
    # 飞书消息内容
    content = {
        "text": f"🦅 马斯克最近的推文:\n\n{tweet_text}\n\n翻译:\n\n{translated_text}"
    }

    message_data = {
        "receive_id": "oc_820faa21d7ed275b53d1727a0feaa917",  # 替换为目标接收者的 ID
        "content": json.dumps(content),  # 将 content 转换为 JSON 字符串
        "msg_type": "text"  # 发送纯文本消息
    }

    response = requests.post(WEBHOOK_URL, headers={'Content-Type': 'application/json'}, data=json.dumps(message_data))
    if response.status_code == 200:
        print(f"消息成功发送到飞书!")
        return True
    else:
        print(f"发送消息到飞书失败: {response.status_code}")
        return False

# 备份推文内容到日志文件
def backup_tweet(tweet_text, translated_text):
    log_message = f"原始推文: {tweet_text}\n翻译后的推文: {translated_text}\n"
    logging.info(log_message)

# 主函数
def main():
    print(f"{datetime.now()} - 开始检查马斯克推文...")
    tweet_text, translated_text = get_musk_tweet_and_translate()

    if tweet_text and translated_text:
        # 发送到飞书
        if send_to_feishu(tweet_text, translated_text):
            # 备份推文
            backup_tweet(tweet_text, translated_text)
        else:
            print("发送到飞书失败.")
    else:
        print("没有可处理的推文.")

if __name__ == "__main__":
    main()
