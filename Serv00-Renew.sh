#!/bin/bash

# 函数：获取用户输入并验证不为空
get_input() {
    local prompt="\$1"
    local input=""
    while [ -z "$input" ]; do
        read -p "$prompt" input
        if [ -z "$input" ]; then
            echo "输入不能为空，请重新输入。"
        fi
    done
    echo "$input"
}

# 函数：下载 Python 文件
download_python_file() {
    local url="\$1"
    local filename="\$2"
    if command -v curl &> /dev/null; then
        curl -L "$url" -o "$filename"
    elif command -v wget &> /dev/null; then
        wget -O "$filename" "$url"
    else
        echo "错误：未找到 curl 或 wget。请安装其中之一以继续。"
        exit 1
    fi
    
    if [ $? -eq 0 ]; then
        echo "成功下载 $filename"
    else
        echo "下载 $filename 失败"
        exit 1
    fi
}

# 函数：安装 Python 文件所需的模块
install_required_modules() {
    local filename="\$1"
    echo "正在分析 $filename 所需的模块..."
    
    modules=$(grep -E "^import |^from " "$filename" | sed -E 's/^import //; s/^from ([^ ]+).*/\1/' | sort -u)
    
    for module in $modules; do
        if ! python3 -c "import $module" 2>/dev/null; then
            echo "正在安装模块: $module"
            pip3 install "$module"
        fi
    done
}

# 获取主机名
HOSTNAME=$(hostname)
echo "当前主机名是: $HOSTNAME"

# 获取SSH密码
SSH_PASSWORD=$(get_input "请输入SSH密码: ")

# 初始化变量
use_wecom=false
use_tg=false
use_pushplus=false

# 添加明确的提示
echo "==================================="
echo "       请选择推送方式"
echo "==================================="
echo "本脚本将帮助您设置自动推送通知。"
echo "您可以选择以下一种或多种推送方式："
echo ""
echo "1. 企业微信（需要企业微信机器人 KEY）"
echo "2. Telegram（需要BOT TOKEN和CHAT ID）"
echo "3. PushPlus（需要PushPlus Token）"
echo ""
echo "请仔细阅读以上说明并做出选择。"
echo "==================================="

# 询问用户选择推送方式
read -p "请输入选项编号（可多选，用空格分隔）: " choices

# 解析用户选择并下载相应的 Python 文件
for choice in $choices; do
    case $choice in
        1)
            use_wecom=true
            download_python_file "https://raw.githubusercontent.com/curry-he/Serv00_auto_script/master/Auto_connect_SSH-WeCom.py" "Auto_connect_SSH-WeCom.py"
            install_required_modules "Auto_connect_SSH-WeCom.py"
            ;;
        2)
            use_tg=true
            download_python_file "https://raw.githubusercontent.com/curry-he/Serv00_auto_script/master/Auto_connect_SSH-TG.py" "Auto_connect_SSH-TG.py"
            install_required_modules "Auto_connect_SSH-TG.py"
            ;;
        3)
            use_pushplus=true
            download_python_file "https://raw.githubusercontent.com/curry-he/Serv00_auto_script/master/Auto_connect_SSH-PushPlus.py" "Auto_connect_SSH-PushPlus.py"
            install_required_modules "Auto_connect_SSH-PushPlus.py"
            ;;
        *) echo "无效选项: $choice" ;;
    esac
done

# 根据选择获取配置信息
if $use_wecom; then
    WECHAT_ROBOT_KEY=$(get_input "请输入企业微信机器人 KEY: ")
    export WECHAT_ROBOT_KEY
fi

if $use_tg; then
    BOT_TOKEN=$(get_input "请输入 Telegram BOT TOKEN: ")
    CHAT_ID=$(get_input "请输入 Telegram CHAT ID: ")
    export BOT_TOKEN CHAT_ID
fi

if $use_pushplus; then
    PUSHPLUS_TOKEN=$(get_input "请输入 PushPlus Token: ")
    export PUSHPLUS_TOKEN
fi

# 执行对应的 Python 脚本
if $use_wecom; then
    python3 Auto_connect_SSH-WeCom.py "$HOSTNAME" "$SSH_PASSWORD"
fi

if $use_tg; then
    python3 Auto_connect_SSH-TG.py "$HOSTNAME" "$SSH_PASSWORD"
fi

if $use_pushplus; then
    python3 Auto_connect_SSH-PushPlus.py "$HOSTNAME" "$SSH_PASSWORD"
fi

echo "所有选定的推送任务已完成。"
