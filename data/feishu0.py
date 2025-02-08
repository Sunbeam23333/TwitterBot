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
        if result.get('code') == 0:
            return result['tenant_access_token']
        else:
            print(f"获取 tenant_access_token 失败: {result.get('msg')}")
    else:
        print(f"请求失败: {response.status_code} - {response.text}")
    return None

# 获取群聊列表
def get_chat_list(tenant_access_token):
    url = f"{FEISHU_API_URL}/chat/v4/list/"
    
    headers = {
        "Authorization": f"Bearer {tenant_access_token}",
        "Content-Type": "application/json; charset=utf-8"
    }
    
    payload = {
        "page_size": "50"  # 修改为字符串类型
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        # 打印完整的响应内容，查看实际数据结构
        print("获取群聊列表的响应：", json.dumps(result, indent=4, ensure_ascii=False))
        if result.get('code') == 0:
            # 使用 'groups' 而不是 'items'
            if 'data' in result and 'groups' in result['data']:
                return result['data']['groups']
            else:
                print("未找到 'groups' 字段。响应格式可能已更改。")
        else:
            print(f"获取群聊列表失败: {result.get('msg')}")
    else:
        print(f"请求失败: {response.status_code} - {response.text}")
    return []

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

def main():
    # 获取 tenant_access_token
    tenant_access_token = get_tenant_access_token()
    
    if not tenant_access_token:
        print("无法获取 tenant_access_token，程序终止。")
        return
    
    # 获取群聊列表
    chats = get_chat_list(tenant_access_token)
    
    if not chats:
        print("没有找到群聊")
        return

    # 打印群聊列表并选择指定群聊
    print("可用的群聊:")
    target_chat_id = "oc_652900f809bc482b3e5e1ad5dab046dd"  # 指定的群聊ID
    print(f"选择的群聊 ID: {target_chat_id}")

    # 发送消息到指定群聊
    message = "这是一个来自推特小助手的消息！"  # 你可以根据需求修改消息内容
    send_message_to_group(tenant_access_token, target_chat_id, message)

if __name__ == "__main__":
    main()
