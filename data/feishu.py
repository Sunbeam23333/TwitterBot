import requests
import json

# 飞书 API凭证
APP_ID = "cli_a72cf73ea8f8100d"
APP_SECRET = "f4wNuPtiZtHtBnSx0rXeef3n5LXPcqwr"

# 飞书 API 地址
FEISHU_API_URL = "https://open.feishu.cn/open-apis"

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
        # 打印响应内容，帮助调试
        print("获取 tenant_access_token 响应：", json.dumps(result, indent=4, ensure_ascii=False))
        
        # 正常响应，直接返回 token
        if result.get('code') == 0:
            return result['tenant_access_token']
        else:
            print(f"获取 tenant_access_token 失败: {result.get('msg')}")
    else:
        print(f"请求失败: {response.status_code} - {response.text}")
    return None

# 发送消息到飞书
def send_message_to_feishu(tenant_access_token, session_id, message_content):
    url = f"{FEISHU_API_URL}/aily/v1/sessions/{session_id}/messages"
    
    # 构造消息体
    message_data = {
        "idempotent_id": "idempotent_id_1",  # 可以替换为当前时间戳或UUID来确保幂等性
        "content_type": "TEXT",  # 纯文本消息
        "content": message_content,
    }
    
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    response = requests.post(url, data=json.dumps(message_data), headers=headers)

    if response.status_code == 200:
        result = response.json()
        if result.get('code') == 0:
            print(f"消息发送成功: {result['data']['message']['content']}")
        else:
            print(f"消息发送失败: {result.get('msg')}")
    else:
        print(f"请求失败: {response.status_code} - {response.text}")

def main():
    # 获取 tenant_access_token
    tenant_access_token = get_tenant_access_token()
    
    if not tenant_access_token:
        print("无法获取 tenant_access_token，程序终止。")
        return
    
    # 指定会话ID
    session_id = "session_4dfunz7sp1g8m"  # 替换为你实际的会话ID

    # 发送消息
    message_content = "你好，飞书！这是通过API发送的消息。"
    send_message_to_feishu(tenant_access_token, session_id, message_content)

if __name__ == "__main__":
    main()
