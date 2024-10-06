import requests
import json
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
import os


# AES加密函数
def encrypt(t, e):
    t = str(t)
    key = e.encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    padded_text = pad(t.encode('utf-8'), AES.block_size)
    encrypted_text = cipher.encrypt(padded_text)
    return b64encode(encrypted_text).decode('utf-8')


# 从 'wozai.json' 文件中加载配置
def load_config():
    with open('wozai.json', 'r', encoding='utf-8') as file:
        config = json.load(file)
    return config


# 将 JWSESSION 存储到 'wozai.json' 文件中
def save_jwsession(jws):
    config = load_config()
    config['JWSESSION'] = jws  # 将 JWSESSION 存入配置文件
    with open('config.json', 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)  # 保存配置文件


# 获取学校ID
def get_school_id(school_name):
    print(f"获取学校ID: {school_name}")
    headers = {
        "accept": "application/json, text/plain, */*",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1 Edg/119.0.0.0"
    }
    url = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/getSchoolList"
    response = requests.get(url, headers=headers)
    data = json.loads(response.text)['data']
    for school in data:
        if school['name'] == school_name:
            print(f"找到学校ID: {school['id']}")
            return school['id']
    print("未找到学校ID")
    return None


# 登录函数，返回JWSESSION
def login(headers, username, password, school_id):
    print(f"登录用户: {username}")
    key = (str(username) + "0000000000000000")[:16]  # 生成16位密钥
    encrypted_text = encrypt(password, key)
    login_url = 'https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username'
    params = {
        "schoolId": school_id,
        "username": username,
        "password": encrypted_text
    }
    login_req = requests.post(login_url, params=params, headers=headers)
    text = json.loads(login_req.text)
    if text['code'] == 0:
        print(f"{username}账号登录成功！")
        set_cookie = login_req.headers['Set-Cookie']
        jws = re.search(r'JWSESSION=(.*?);', str(set_cookie)).group(1)
        return jws
    else:
        print(f"{username}登录失败，请检查账号密码！")
        return False


# 获取打卡日志
def get_my_sign_logs(headers):
    print("获取签到日志")
    url = 'https://gw.wozaixiaoyuan.com/sign/mobile/receive/getMySignLogs'
    params = {
        'page': 1,
        'size': 1
    }
    response = requests.get(url, headers=headers, params=params)
    print(f"签到日志响应: {response.text}")

    data = json.loads(response.text).get('data', [])
    if len(data) == 0:
        print("未找到签到日志")
        return None, None, None, False

    sign_data = data[0]
    if int(sign_data['signStatus']) != 1:
        print("用户已打过卡！")
        return None, None, None, False

    if 'id' in sign_data and 'signId' in sign_data and 'schoolId' in sign_data:
        id_value = sign_data['id']
        sign_id_value = sign_data['signId']
        school_id = sign_data['schoolId']
        print(f"签到记录 id: {id_value}, signId: {sign_id_value}, schoolId: {school_id}")
        return id_value, sign_id_value, school_id, True

    print("签到记录中没有 'id' 或 'signId' 字段。")
    return None, None, None, False


# 签到函数
def sign_in(headers, id_value, sign_id_value, school_id, location_info):
    print("开始签到")
    url = 'https://gw.wozaixiaoyuan.com/sign/mobile/receive/doSignByLocation'
    params = {
        'id': id_value,
        'schoolId': school_id,
        'signId': sign_id_value
    }

    payload = {
        "id": id_value,
        "schoolId": school_id,
        "signId": sign_id_value,
        "latitude": location_info['latitude'],  # 从配置中读取经纬度
        "longitude": location_info['longitude'],
        "country": location_info['country'],
        "province": location_info['province'],
        "city": location_info['city'],
        "district": location_info['district'],
        "street": location_info['street']
    }

    response = requests.post(url, headers=headers, params=params, json=payload)
    print(f"签到响应: {response.text}")

    if response.status_code == 200:
        result = json.loads(response.text)
        if result['code'] == 0:
            print("签到成功！")
        else:
            print(f"签到失败，错误信息: {result.get('message', '未知错误')}")
    else:
        print(f"请求失败，HTTP状态码: {response.status_code}")


# 主函数：登录并进行签到
def main():
    # 从配置文件读取信息
    config = load_config()
    school_name = config['school_name']
    username = config['username']
    password = config['password']
    location_info = config['location']

    # 初始化 headers
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
        "sec-ch-ua": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"'
    }

    # 检查是否已经存储JWSESSION
    jws = config.get('JWSESSION', None)
    if jws:
        print("使用存储的JWSESSION进行签到")
    else:
        # 获取学校ID
        school_id = get_school_id(school_name)
        if not school_id:
            print("无法获取学校ID，结束程序")
            return

        # 登录并获取 JWSESSION
        jws = login(headers, username, password, school_id)
        if not jws:
            print("登录失败，结束程序")
            return

        # 保存JWSESSION到配置文件中
        save_jwsession(jws)

    # 设置登录后的Cookie
    headers['Cookie'] = f'JWSESSION={jws}'

    # 获取签到日志
    id_value, sign_id_value, school_id, can_sign_in = get_my_sign_logs(headers)

    # 如果可以签到，执行签到
    if can_sign_in:
        sign_in(headers, id_value, sign_id_value, school_id, location_info)
    else:
        print("无法进行签到，已打卡或无相关信息。")


# 调用主函数
main()
