from flask import Flask, render_template_string, request, redirect, url_for, flash
import requests
import json
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from base64 import b64encode
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # 随机生成 24 字节的密钥

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

def login(user, school_id):
    key = (str(user['username']) + "0000000000000000")[:16]
    encrypted_text = encrypt(user['password'], key)
    login_url = 'https://gw.wozaixiaoyuan.com/basicinfo/mobile/login/username'
    params = {"schoolId": school_id, "username": user['username'], "password": encrypted_text}
    response = requests.post(login_url, params=params)
    result = response.json()

    if result['code'] == 0:
        jws = re.search(r'JWSESSION=(.*?);', response.headers['Set-Cookie']).group(1)
        return jws
    return None

def get_my_sign_logs(headers):
    print("获取签到日志")
    url = 'https://gw.wozaixiaoyuan.com/sign/mobile/receive/getMySignLogs'
    params = {'page': 1, 'size': 1}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=3)
        data = response.json().get('data', [])

        if not data:
            print("未找到签到日志")
            return None

        log = data[0]
        sign_status = log.get('signStatus', 0)
        sign_mode = log.get('signMode', 0)
        sign_time = log.get('signTime', '无记录')
        name = log.get('name', '未知用户')

        if sign_status != 1:
            print(f"{name} 的签到时间已过，不再继续处理")
            return None

        if sign_mode == 2:
            print(f"{name} 已签到，无需再次签到")
            return f"{name} - 已签到 于 {sign_time}"

        print(f"{name} 未签到，准备签到")
        return f"{name} - 未签到 于 {sign_time}"

    except requests.exceptions.Timeout:
        print("获取签到日志超时")
        return "获取签到日志超时，请稍后重试"
    except Exception as e:
        print(f"获取签到日志时出错: {e}")
        return f"获取签到日志时出错: {e}"

@app.route('/')
def index():
    config = load_config()
    return render_template_string(TEMPLATE, users=config['users'])

@app.route('/sign/<username>')
def sign_user(username):
    config = load_config()
    user = next((u for u in config['users'] if u['username'] == username), None)

    if not user:
        flash(f"未找到用户: {username}")
        return redirect(url_for('index'))

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0"
    }
    jws = user.get('JWSESSION')
    if jws:
        headers['Cookie'] = f'JWSESSION={jws}'

    log_message = get_my_sign_logs(headers)

    if log_message:
        flash(log_message)
    else:
        flash(f"未能获取 {user['name']} 的签到日志")

    return redirect(url_for('index'))

TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我在校园签到系统</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f9f9f9; margin: 0; padding: 20px; }
        h1 { text-align: center; color: #4CAF50; }
        table { width: 80%; margin: 20px auto; border-collapse: collapse; }
        th, td { padding: 12px; text-align: center; border-bottom: 1px solid #ddd; }
        th { background-color: #4CAF50; color: white; }
        tr:hover { background-color: #f1f1f1; }
        .button { padding: 8px 16px; margin: 5px; background-color: #4CAF50; color: white; border: none; cursor: pointer; border-radius: 5px; }
        .button:hover { background-color: #45a049; }
        .container { text-align: center; }
        .logs { margin-top: 20px; }
    </style>
</head>
<body>
    <h1>我在校园签到系统</h1>
    <table>
        <tr>
            <th>用户名</th>
            <th>姓名</th>
            <th>签到</th>
            <th>签到日志</th>
        </tr>
        {% for user in users %}
        <tr>
            <td>{{ user.username }}</td>
            <td>{{ user.name }}</td>
            <td><button class="button" onclick="location.href='/sign/{{ user.username }}'">签到</button></td>
            <td><button class="button" onclick="location.href='/sign/{{ user.username }}'">查看日志</button></td>
        </tr>
        {% endfor %}
    </table>

    <div class="logs">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <ul>
                    {% for message in messages %}
                        <li style="text-align: left; margin-bottom: 10px;">{{ message }}</li>
                    {% endfor %}
                </ul>
            {% endif %}
        {% endwith %}
    </div>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=False)
