#!/usr/bin/env python3
import os
import requests
import paramiko
import socket
from datetime import datetime
import pytz

# PushPlus 设置
PUSHPLUS_TOKEN = "" # 在pushplus公众号-功能-个人中心-开发设置里获取Token

# 预先定义的常量  
url = '你检测的地址，参考下一行注释'  
# 测试URL 这个URL是个凉了的 url = 'https://edwgiz.serv00.net/'
ssh_info = {  
    'host': 's3.serv00.com',    # 主机地址
    'port': 22,  
    'username': '你的用户名',       # 你的用户名，别写错了
    'password': '你的SSH密码'       # 你注册的时候收到的密码或者你自己改了的密码
}

# 获取当前脚本文件的绝对路径
script_dir = os.path.dirname(os.path.abspath(__file__))

# 日志文件将保存在脚本所在的目录中
log_file_path = os.path.join(script_dir, 'Auto_connect_SSH.log')
pushplus_message_sent = False
flush_log_message = []

# 写入日志的函数
def write_log(log_message):
    global flush_log_message
    if not os.path.exists(log_file_path):
        open(log_file_path, 'a').close()
        os.chmod(log_file_path, 0o644)
    log_info = f"{log_message}"
    flush_log_message.append(log_info)

# 把所有的日志信息写入日志文件
def flush_log():
    global flush_log_message
    username = ssh_info['username']
    system_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    current_day = datetime.now(pytz.timezone('Asia/Shanghai')).weekday()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    current_weekday_name = weekdays[current_day]
    flush_log_messages = f"{system_time} - {beijing_time} - {current_weekday_name} - {url} - {username} - {' - '.join(flush_log_message)}"
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(flush_log_messages + '\n')
    flush_log_message.clear()

# 发送PushPlus消息的函数
def send_pushplus_message(title, content):
    global pushplus_message_sent
    pushplus_url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content
    }
    try:
        response = requests.post(pushplus_url, json=data)
        if response.status_code == 200:
            pushplus_status = "PushPlus提醒消息发送成功"
            print("温馨提醒：PushPlus提醒消息发送成功。")
        else:
            pushplus_status = f"PushPlus提醒消息发送失败，状态码: {response.status_code}"
            print(f"警告：PushPlus提醒消息发送失败！状态码: {response.status_code}")
    except Exception as e:
        pushplus_status = f"PushPlus提醒消息发送失败，错误: {str(e)}"
        print(f"警告：PushPlus提醒消息发送失败！错误: {str(e)}")
    
    if not pushplus_message_sent:
        write_log(pushplus_status)
        pushplus_message_sent = True

# 尝试通过SSH恢复PM2进程的函数
def restore_pm2_processes():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(**ssh_info)
        
        stdin, stdout, stderr = ssh.exec_command('pm2 resurrect')
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if error:
            write_log(f"PM2恢复失败: {error}")
            print(f"PM2恢复失败: {error}")
        else:
            write_log(f"PM2恢复成功: {output}")
            print(f"PM2恢复成功: {output}")
        
        ssh.close()
    except Exception as e:
        write_log(f"SSH连接失败: {str(e)}")
        print(f"SSH连接失败: {str(e)}")

# 尝试通过SSH连接的函数
def ssh_connect():
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(**ssh_info)
        
        stdin, stdout, stderr = ssh.exec_command('ls -l')
        output = stdout.read().decode()
        
        write_log("SSH连接成功")
        print("SSH连接成功")
        
        ssh.close()
    except Exception as e:
        write_log(f"SSH连接失败: {str(e)}")
        print(f"SSH连接失败: {str(e)}")

# 检查是否为每月的1号
def is_first_day_of_month():
    return datetime.now().day == 1

# 返回当前的天、月和一年中的第几天
def get_day_info():
    now = datetime.now()
    return now.day, now.month, now.timetuple().tm_yday, ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][now.weekday()]

# 每个月发送仅包含URL和时间的提醒消息
def send_monthly_reminder():
    current_day, current_month, current_year_day, current_weekday_name = get_day_info()
    system_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    title = "🎉每月固定SSH提醒🎉"
    content = f"""
检测地址:
{url}
-------------------------------------
　　今天是{current_month}月{current_day}日( {current_weekday_name} )，本月的第 {current_day} 天，今年的第 {current_year_day} 天，例行SSH连接已经成功执行，以防万一空了可以到后台查看记录！
-------------------------------------
系统时间: {system_time}
北京时间: {beijing_time}
"""
    return title, content

if __name__ == '__main__':
    # 每月一次检查提醒
    if is_first_day_of_month():
        title, content = send_monthly_reminder()
        send_pushplus_message(title, content)
        ssh_connect()

    # 检查URL状态和DNS
    try:
        # 尝试解析URL的域名
        host = socket.gethostbyname(url.split('/')[2])
        print(f"解析成功，IP地址为: {host}")
        write_log(f"{host}")

        # 尝试获取URL的状态码
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        if status_code != 200:
            # URL状态码不是200，发送通知并尝试恢复PM2进程
            system_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
            title = "💥 当前服务不可用 💥"
            content = f"""
地址: {url}
状态码: {status_code}
💪 正在尝试通过SSH恢复PM2进程，请稍后手动检查恢复情况！
-------------------------------------
系统时间: {system_time}
北京时间: {beijing_time}
"""
            write_log(f"主机状态码: {status_code}")
            send_pushplus_message(title, content)
            restore_pm2_processes()
        else:
            write_log(f"主机状态码: {status_code}")
            print(f"主机状态码: {status_code}")

    except socket.gaierror as e:
        # 解析失败，发送通知
        write_log(f"Error: {e}")
        system_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
        title = "💣 解析失败提醒 💣"
        content = f"""
地址: {url}
错误: {e}
😱 抓紧尝试检查解析配置或联系管事的老铁。
-------------------------------------
系统时间: {system_time}
北京时间: {beijing_time}
"""
        send_pushplus_message(title, content)
        host = "解析失败"
        status_code = "N/A"

    # 添加这些行
    system_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    beijing_time = datetime.now(pytz.timezone('Asia/Shanghai')).strftime('%Y-%m-%d %H:%M:%S')
    title = "脚本执行完毕"
    content = f"""
检测地址: {url}
解析IP: {host}
状态码: {status_code}
系统时间: {system_time}
北京时间: {beijing_time}
"""
    send_pushplus_message(title, content)

    # 所有日志信息已经收集完成，写入日志文件
    flush_log()
