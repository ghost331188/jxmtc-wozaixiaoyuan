from flask import Flask, Response, stream_with_context
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
from datetime import datetime, timedelta

app = Flask(__name__)

def execute_task():
    """自动执行 wozai.py 并打印日志"""
    print(f"自动任务在 {datetime.utcnow() + timedelta(hours=8)} 执行")
    subprocess.run(['python3', 'wozai.py'])

@app.route('/')
def index():
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>我在校园签到系统</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f9f9f9; margin: 0; padding: 20px; }
            h1 { text-align: center; color: #4CAF50; }
            .button { padding: 12px 24px; margin: 10px; background-color: #4CAF50; color: white; border: none; cursor: pointer; border-radius: 8px; font-size: 16px; }
            .button:hover { background-color: #45a049; }
            .container { text-align: center; margin-top: 50px; }
            pre { background-color: #e8e8e8; padding: 10px; border-radius: 5px; text-align: left; max-height: 300px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>当前北京时间: <span id="time"></span></h1>
            <button class="button" onclick="startExecution()">手动执行签到</button>
            <pre id="output">等待执行...</pre>
        </div>

        <script>
            function updateTime() {
                const now = new Date();
                const year = now.getFullYear();
                const month = String(now.getMonth() + 1).padStart(2, '0');
                const day = String(now.getDate()).padStart(2, '0');
                const hours = String(now.getHours()).padStart(2, '0');
                const minutes = String(now.getMinutes()).padStart(2, '0');
                const seconds = String(now.getSeconds()).padStart(2, '0');
                const formattedTime = `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
                document.getElementById('time').textContent = formattedTime;
            }

            setInterval(updateTime, 1000);  // 每秒更新一次时间

            function startExecution() {
                const output = document.getElementById('output');
                output.textContent = '执行中...\\n';

                const eventSource = new EventSource('/execute');
                eventSource.onmessage = function(event) {
                    output.textContent += event.data + '\\n';
                    output.scrollTop = output.scrollHeight;  // 滚动到底部
                };
                eventSource.onerror = function() {
                    output.textContent += '执行完成。\\n';
                    eventSource.close();
                };
            }

            // 初始化页面时立即更新一次时间
            updateTime();
        </script>
    </body>
    </html>
    """
    return html_content

@app.route('/execute')
def execute():
    """手动执行 wozai.py 并实时捕获输出"""
    def generate():
        process = subprocess.Popen(
            ['python3', '-u', 'wozai.py'],  # -u 禁用缓冲输出
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for line in iter(process.stdout.readline, ''):
            yield f"data: {line.strip()}\n\n"  # SSE 格式发送输出
        process.stdout.close()
        process.wait()

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

if __name__ == '__main__':
    scheduler = BackgroundScheduler()
    scheduler.add_job(execute_task, 'cron', hour=18, minute=32)  # 每天 18:32 自动执行任务
    scheduler.start()

    app.run(host='0.0.0.0', port=8080)
