import json
import time
import random
import execjs
import requests
from loguru import logger
import pandas as pd
import os
from datetime import datetime

# 确保数据存储目录存在
data_dir = "./data"
os.makedirs(data_dir, exist_ok=True)

output_file_path = os.path.join(data_dir, "result.csv")

# 初始化 CSV 文件并写入表头
if not os.path.exists(output_file_path):
    with open(output_file_path, mode="w", encoding="utf-8-sig", newline="") as f:
        f.write("note_url,last_update_time,note_id,xsec_token,type,title,text,topics,likes,comments,collects,shares\n")


def base36encode(number, digits='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
    base36 = ""
    while number:
        number, i = divmod(number, 36)
        base36 = digits[i] + base36
    return base36.lower()


def generate_search_id():
    timestamp = int(time.time() * 1000) << 64
    random_value = int(random.uniform(0, 2147483646))
    return base36encode(timestamp + random_value)


def parse_data(data):
    items = data.get('data', {}).get('items', [])
    parsed_info = []

    for item in items:
        note = item.get('note_card', {})
        title = note.get('title', '')
        desc = note.get('desc', '')

        # 提取并清理话题
        topics = [word.strip('#').replace('[话题]', '').strip() for word in desc.split() if '[话题]' in word]
        desc_cleaned = ' '.join([word for word in desc.split() if '[话题]' not in word]).strip()

        interact_info = note.get('interact_info', {})
        liked_count = interact_info.get('liked_count', 0)
        comment_count = interact_info.get('comment_count', 0)
        collected_count = interact_info.get('collected_count', 0)
        share_count = interact_info.get('share_count', 0)

        parsed_info.append({
            '标题': title,
            '内容': desc_cleaned,
            '点赞数': liked_count,
            '评论数': comment_count,
            '收藏数': collected_count,
            '转发数': share_count,
            '话题': topics
        })

    return parsed_info


def convert_to_int(value):
    if isinstance(value, str) and '万' in value:
        value = value.replace('万', '')
        return float(value) * 10000  # 转换为整数
    return int(value) if value else 0


search_data = {
    "keyword": "抖音",  # 爬取TikTok（抖音）相关内容，模糊匹配
    "page": 1,
    "page_size": 20,  # 每页20条
    "search_id": generate_search_id(),
    "sort": "general",  # 综合排序，可改为 hot(最热) 或 latest(最新)
    "note_type": 0
}

# 用户需要填写自己的 Cookie 和 请求头
cookies = {
    "a1": "1946519b432g6nzmgvw17cyuyjsk82rvy9ba1002w00000108057",
    "web_session": "040069b378a7c25bd8588e4e93354b7bd3c6fd"
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Referer": "https://www.xiaohongshu.com",
    "Content-Type": "application/json"
}


url = 'https://edith.xiaohongshu.com/api/sns/web/v1/search/notes'
api_endpoint = '/api/sns/web/v1/search/notes'
a1_value = cookies['a1']

for page in range(1, 12):  # 爬取 11 页数据
    search_data['page'] = str(page)
    
    with open('1.js', 'r', encoding='utf-8') as f:
        js_script = f.read()
        context = execjs.compile(js_script)
        sign = context.call('getXs', api_endpoint, search_data, a1_value)

    headers['x-s'] = sign['X-s']
    headers['x-t'] = str(sign['X-t'])
    headers['X-s-common'] = sign['X-s-common']

    response = requests.post(url, headers=headers, data=json.dumps(search_data, separators=(",", ":"), ensure_ascii=False).encode('utf-8'))
    
    logger.info(f'Page {page} Response: {response.json()}')

    if response.status_code == 200:
        data = response.json()
        notes = data.get('data', {}).get('items', [])
        
        for note in notes:
            try:
                xsec_token = note.get('xsec_token')
                note_id = note.get('id')
                note_url = f'https://www.xiaohongshu.com/explore/{note_id}?xsec_token={xsec_token}&xsec_source=pc_feed'

                # 解析详情数据
                note_data = parse_data(data)
                if not note_data:
                    continue  # 跳过无效数据

                display_title = note_data[0]['标题'].replace("\n", "").strip()
                text = note_data[0]['内容'].replace("\n", "").strip()
                likes = convert_to_int(note_data[0]['点赞数'])
                comments = convert_to_int(note_data[0]['评论数'])
                collects = convert_to_int(note_data[0]['收藏数'])
                shares = convert_to_int(note_data[0]['转发数'])
                topics = ", ".join(note_data[0]['话题']).replace("\n", "").strip()

                data_row = {
                    'note_url': note_url,
                    'last_update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'note_id': note_id,
                    'xsec_token': xsec_token,
                    'type': 'N/A',  # 由于类型字段获取不稳定，暂定为 N/A
                    "title": display_title,
                    "text": text,
                    "topics": topics,
                    "likes": likes,
                    "comments": comments,
                    "collects": collects,
                    "shares": shares
                }

                df = pd.DataFrame([data_row])
                df.to_csv(output_file_path, mode="a", index=False, header=False, encoding="utf-8-sig", quoting=1)

            except Exception as e:
                logger.error(f"处理笔记 {note_id} 失败: {e}")

    else:
        print('请求过于频繁，请稍后再试')
