import requests
import json

# 企业微信凭证
CORP_ID = "ww19cea00d6413cc40"  # 公司ID
SECRET = "BaPV3mDQ_KF0HGJErCP4pY0XuR9ZUrnzkbToRba1ayk"  # 应用的Secret

# 获取 access_token
def get_access_token(corp_id, secret):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corp_id}&corpsecret={secret}"
    response = requests.get(url)
    data = response.json()
    
    if data.get('errcode') == 0:
        return data.get('access_token')
    else:
        raise Exception(f"获取 access_token 失败: {data.get('errmsg')}")

# 获取企业微信用户列表
def get_user_list(access_token):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/user/simplelist?access_token={access_token}&department_id=1&fetch_child=1"
    response = requests.get(url)
    data = response.json()

    if data.get('errcode') == 0:
        return data.get('userlist')
    else:
        raise Exception(f"获取用户列表失败: {data.get('errmsg')}")

# 主程序
def main():
    try:
        # 获取access_token
        access_token = get_access_token(CORP_ID, SECRET)
        print("Access Token 获取成功:", access_token)

        # 获取用户列表
        user_list = get_user_list(access_token)
        print(f"共有 {len(user_list)} 个用户:")
        
        # 输出用户信息
        for user in user_list:
            print(f"用户ID: {user['userid']}, 用户名: {user['name']}")

    except Exception as e:
        print(f"程序运行出错: {str(e)}")

if __name__ == "__main__":
    main()
