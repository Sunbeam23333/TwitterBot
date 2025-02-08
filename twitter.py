import tweepy
import requests
import schedule
import time
import hashlib
import hmac
import json
import logging
from datetime import datetime

# 飞书 Webhook信息
webhook_url = 'https://open.feishu.cn/open-apis/bot/v2/hook/8f78cc56-2ec4-4733-ae05-1dca691edfa5'  # 你的Webhook地址
secret = '3pxWVhMt5t64h6mGfamHyf'  # 你的签名校验密钥

# Twitter API V2认证信息（Bearer Token）
bearer_token = 'AAAAAAAAAAAAAAAAAAAAAM41ywEAAAAAAvWrLb8Bl7FdoVPl9FnF34S3QxI%3DrDeieu40fY1JP51BQNxGELwxygrWeVjds1LuhJOmnexvVLzU9n'

# 设置日志记录
logging.basicConfig(filename="tweet_monitor.log", level=logging.INFO, 
                    format='%(asctime)s - %(message)s')

# 使用 Bearer Token 进行认证
client = tweepy.Client(bearer_token=bearer_token)

# 生成签名
def generate_sign(timestamp):
    message = f'{timestamp}\n{secret}'
    sign = hmac.new(secret.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).hexdigest()
    return sign

# 发送飞书消息
def send_feishu_message(content):
    timestamp = str(int(time.time() * 1000))  # 获取当前时间戳
    sign = generate_sign(timestamp)  # 生成签名

    headers = {
        'Content-Type': 'application/json'
    }

    message_data = {
        "msg_type": "text",
        "content": {
            "text": content
        }
    }

    # 在URL中添加签名和时间戳
    url_with_sign = f'{webhook_url}&timestamp={timestamp}&sign={sign}'

    response = requests.post(url_with_sign, data=json.dumps(message_data), headers=headers)
    return response.json()

# 获取推文（使用 V2 端点）
def get_twitter_feed():
    try:
        # 使用 search_recent_tweets 获取最新推文，搜索关键词 "elonmusk"
        query = "elonmusk -is:retweet"  # 排除转发的推文
        response = client.search_recent_tweets(query=query, max_results=10)  # 获取最多2条推文
        notification_content = []
        has_new = False

        # 处理返回的推文
        if response.data:
            for tweet in response.data:
                tweet_url = f"https://twitter.com/{tweet.author_id}/status/{tweet.id}"
                tweet_content = (
                    f"🐦 新推文来自 @{tweet.author_id}\n"
                    f"🕒 时间: {tweet.created_at}\n"
                    f"📄 内容: {tweet.text[:200]}...\n"
                    f"🔗 链接: {tweet_url}"
                )
                notification_content.append(tweet_content)
                has_new = True

                # 在命令行打印新的推文
                print(f"新推文来自 @{tweet.author_id}:\n{tweet_content}")

                # 在日志中记录新的推文
                logging.info(f"新推文来自 @{tweet.author_id}: {tweet_content}")

        return notification_content, has_new

    except tweepy.TweepyException as e:
        print(f"获取推文失败: {e}")
        return [], False

# 检查是否有新的推文并发送通知
def check_new_tweets():
    print(f"{datetime.now()} - 开始检查推文...")  # 调试输出
    notification_content, has_new = get_twitter_feed()

    if has_new:
        full_message = "\n\n" + "\n\n".join(notification_content)
        if send_feishu_message(full_message):
            print(f"{datetime.now()} 通知发送成功")
        else:
            print(f"{datetime.now()} 通知发送失败")
    else:
        print(f"{datetime.now()} 没有新的推文")


# 定时任务
CHECK_INTERVAL = 0.1  # 每0.1分钟检查一次推文
if __name__ == "__main__":
    print("启动推特监控服务...")
    scheduler = schedule.Scheduler()
    scheduler.every(CHECK_INTERVAL).minutes.do(check_new_tweets)

    try:
        while True:
            scheduler.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("服务已停止")
