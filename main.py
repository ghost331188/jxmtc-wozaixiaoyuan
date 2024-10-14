import requests
import json
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode

def encrypt(t, e):
    t = str(t)
    key = e.encode('utf-8')
    cipher = AES.new(key, AES.MODE_ECB)
    padded_text = pad(t.encode('utf-8'), AES.block_size)
    encrypted_text = cipher.encrypt(padded_text)
    return b64encode(encrypted_text).decode('utf-8')

def load_config():
    with open('config.json', 'r', encoding='utf-8') as file:
        return json.load(file)

def save_jwsession(user, jws):
    config = load_config()
    for u in config['users']:
        if u['username'] == user['username']:
            u['JWSESSION'] = jws
            break
    with open('config.json', 'w', encoding='utf-8') as file:
        json.dump(config, file, ensure_ascii=False, indent=4)

def get_school_id(school_name):
    print(f"获取学校ID: {school_name}")
    headers = {"accept": "application/json, text/plain, */*", "user-agent": "Mozilla/5.0"}
    url = "https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/getSchoolList"
    response = requests.get(url, headers=headers)
    data = response.json().get('data', [])
    for school in data:
        if school['name'] == school_name:
            print(f"找到学校ID: {school['id']}")
            return school['id']
    print("未找到学校ID")
    return None

def login(user, school_id):
    print(f"登录用户: {user['username']}")
    key = (str(user['username']) + "0000000000000000")[:16]
    encrypted_text = encrypt(user['password'], key)
    login_url = 'https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username'
    params = {"schoolId": school_id, "username": user['username'], "password": encrypted_text}
    response = requests.post(login_url, params=params)
    result = response.json()

    if result['code'] == 0:
        print(f"{user['name']} 登录成功！")
        jws = re.search(r'JWSESSION=(.*?);', response.headers['Set-Cookie']).group(1)
        return jws
    else:
        print(f"{user['name']} 登录失败，请检查账号密码！")
        return None

def get_my_sign_logs(headers):
    print("获取签到日志")
    url = 'https://gw.wozaixiaoyuan.com/sign/mobile/receive/getMySignLogs'
    params = {'page': 1, 'size': 1}
    response = requests.get(url, headers=headers, params=params)
    data = response.json().get('data', [])

    if not data:
        print("未找到签到日志")
        return None, None, None

    log = data[0]
    name = log.get('name', '未知')
    sign_status = log.get('signStatus')

    status_message = {1: "签到中", 2: "签到时间已过"}.get(sign_status, "未知状态")
    print(f"用户 {name} 的签到状态: {status_message}")

    return log['id'], log['signId'], log['schoolId']

def sign_in(headers, id_value, sign_id_value, school_id, location_info):
    print("开始签到")
    url = 'https://gw.wozaixiaoyuan.com/sign/mobile/receive/doSignByLocation'
    params = {'id': id_value, 'schoolId': school_id, 'signId': sign_id_value}
    payload = {"id": id_value, "schoolId": school_id, "signId": sign_id_value, **location_info}
    response = requests.post(url, headers=headers, params=params, json=payload)
    result = response.json()

    if response.status_code == 200 and result['code'] == 0:
        print("签到成功！")
    else:
        print(f"签到失败: {result.get('message', '未知错误')}")

def try_sign_in_with_jws(user, headers):
    id_value, sign_id_value, school_id = get_my_sign_logs(headers)
    if id_value and sign_id_value and school_id:
        sign_in(headers, id_value, sign_id_value, school_id, user['location'])
        return True
    print(f"用户 {user['name']} 无法签到，尝试重新登录")
    return False

def main():
    config = load_config()
    headers_template = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0"
    }

    for user in config['users']:
        print("-----------")
        if not user['username'] or not user['password']:
            print(f"跳过用户 {user['name']}：未填写账号或密码")
            continue

        headers = headers_template.copy()
        jws = user.get('JWSESSION')

        if jws:
            headers['Cookie'] = f'JWSESSION={jws}'
            if try_sign_in_with_jws(user, headers):
                continue  # 如果签到成功，跳过后续流程

        # 获取学校ID并登录
        school_id = get_school_id(user['school_name'])
        if not school_id:
            print(f"用户 {user['name']} 获取学校ID失败，跳过")
            continue

        jws = login(user, school_id)
        if not jws:
            print(f"用户 {user['name']} 登录失败，跳过")
            continue

        save_jwsession(user, jws)
        headers['Cookie'] = f'JWSESSION={jws}'
        try_sign_in_with_jws(user, headers)

main()
