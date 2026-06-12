#!/bin/bash
# 宿主机运行：检测容器内是否发现新题，有则发桌面通知+蜂鸣
# 用法: 加入 crontab 每小时运行一次
# 0 * * * * /Users/xaa/zuoye/oneform/notify_tasks.sh

CONTAINER="oneform-agent"

# 让容器点击 Check Now 并检测
docker exec $CONTAINER python3 /app/check_new_tasks.py > /tmp/oneform_check.log 2>&1

# 检查是否有新题标记
HAS_TASKS=$(docker exec $CONTAINER cat /app/task_alert.flag 2>/dev/null)

if [ -n "$HAS_TASKS" ]; then
    # 桌面通知（需要 DISPLAY 和 DBUS）
    export DISPLAY=:0
    export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
    notify-send -u critical "🎯 TryRating 有新题!" "$HAS_TASKS" 2>/dev/null

    # 蜂鸣声
    for i in 1 2 3; do
        echo -ne '\a' > /dev/tty 2>/dev/null || true
        aplay -q /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || \
        paplay /usr/share/sounds/freedesktop/stereo/complete.oga 2>/dev/null || \
        echo -ne '\007' || true
        sleep 0.3
    done

    # Telegram 通知
    curl -s -X POST "https://api.telegram.org/bot8524947711:AAEsLcc4dbUnV_mSd3igKK8UQXRMVqhdlhA/sendMessage" \
        -H "Content-Type: application/json" \
        -d "{\"chat_id\":\"194652099\",\"text\":\"🎯 TryRating 有新题! $HAS_TASKS\"}" > /dev/null 2>&1 || true

    echo "[$(date)] ALERT: $HAS_TASKS"
else
    echo "[$(date)] No tasks."
fi
