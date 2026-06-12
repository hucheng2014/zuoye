#!/usr/bin/env bash
# ============================================================
#  global_alarm.sh — 全局蜂鸣报警工具包
#
#  安装: source ~/.bashrc  (已自动加载)
#  或:   source /Users/xaa/zuoye/oneform/renzheng/MAIL/scripts/global_alarm.sh
#
#  功能:
#    1. err_beep    — 上一条命令失败时自动蜂鸣 (PROMPT_COMMAND 钩子)
#    2. run         — 通用命令包装: 失败蜂鸣 + 超时蜂鸣
#    3. watchdog_bg — 后台看门狗: 监控指定 PID，挂死超时则蜂鸣
#    4. beep        — 手动蜂鸣
#    5. say_err     — 语音播报错误 (可选)
# ============================================================

# ─── 配置 ───────────────────────────────────────────────────
ALARM_TIMEOUT_DEFAULT="${ALARM_TIMEOUT_DEFAULT:-600}"   # 默认超时 10 分钟
ALARM_BEEP_COUNT="${ALARM_BEEP_COUNT:-5}"               # 报警响铃次数
ALARM_BEEP_INTERVAL="${ALARM_BEEP_INTERVAL:-0.3}"       # 响铃间隔(秒)
ALARM_SPEAK="${ALARM_SPEAK:-1}"                          # 1=语音播报 0=仅蜂鸣
ALARM_HOOK_ON="${ALARM_HOOK_ON:-1}"                      # 1=自动钩子(每条命令失败自动响)

# ─── 蜂鸣原语 ──────────────────────────────────────────────
beep() {
    local count="${1:-$ALARM_BEEP_COUNT}"
    local msg="${2:-ALERT}"
    local i

    # 1) 终端 BEL (如果终端支持，会触发系统提示音或视觉提示)
    for ((i=0; i<count; i++)); do
        printf '\a'
        sleep "$ALARM_BEEP_INTERVAL"
    done

    # 2) paplay 系统音效 (Ubuntu 桌面)
    if command -v paplay &>/dev/null; then
        local sound="/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"
        if [[ -f "$sound" ]]; then
            paplay "$sound" &>/dev/null &
        fi
    fi

    # 3) 语音播报 (如果 spd-say 可用)
    if [[ "$ALARM_SPEAK" == "1" ]] && command -v spd-say &>/dev/null; then
        spd-say -r 20 "$msg" &>/dev/null &
    fi

    # 4) 终端高亮闪烁提示
    if [[ -t 2 ]]; then
        local red='\033[1;31m' blink='\033[5m' reset='\033[0m'
        printf "${red}${blink}*** %s ***${reset}\n" "$msg" >&2
    fi
}

# ─── 语音播报 ──────────────────────────────────────────────
say_err() {
    local msg="$*"
    if command -v spd-say &>/dev/null; then
        spd-say "$msg" &>/dev/null &
    fi
    beep 3 "$msg"
}

# ─── 通用命令包装器 ────────────────────────────────────────
# 用法:
#   run <command> [args...]           # 失败时蜂鸣
#   run -t 300 <command> [args...]    # 300秒超时 + 失败蜂鸣
#   run -t 60 -- node myscript.js     # 明确分隔
run() {
    local timeout_val="$ALARM_TIMEOUT_DEFAULT"
    local use_timeout=0

    # 解析选项
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -t|--timeout)
                timeout_val="$2"
                use_timeout=1
                shift 2
                ;;
            -q|--quiet)
                ALARM_SPEAK=0
                shift
                ;;
            --)
                shift
                break
                ;;
            *)
                break
                ;;
        esac
    done

    if [[ $# -eq 0 ]]; then
        echo "用法: run [-t 超时秒数] [-q] <command> [args...]" >&2
        return 1
    fi

    local exit_code
    local cmd_str="$*"

    if [[ $use_timeout -eq 1 ]]; then
        timeout "$timeout_val" "$@"
        exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            beep "$ALARM_BEEP_COUNT" "TIMEOUT: $cmd_str 超过 ${timeout_val}秒"
            echo "[alarm] 命令超时 ${timeout_val}s: $cmd_str" >&2
            return 124
        fi
    else
        "$@"
        exit_code=$?
    fi

    if [[ $exit_code -ne 0 ]]; then
        beep "$ALARM_BEEP_COUNT" "ERROR: exit=$exit_code"
        echo "[alarm] 命令失败 (exit=$exit_code): $cmd_str" >&2
    fi

    return $exit_code
}

# ─── 后台看门狗 ────────────────────────────────────────────
# 用法:
#   watchdog_bg <PID> [超时秒数] [描述]
#   watchdog_bg $! 300 "node脚本"
#   watchdog_all              # 监控当前 shell 所有后台进程
watchdog_bg() {
    local pid="${1:?需要PID}"
    local timeout_val="${2:-$ALARM_TIMEOUT_DEFAULT}"
    local desc="${3:-PID:$pid}"
    local elapsed=0

    (
        while kill -0 "$pid" 2>/dev/null; do
            sleep 1
            ((elapsed++))
            if (( elapsed >= timeout_val )); then
                beep 10 "HANG: $desc 超过 ${timeout_val}秒"
                echo "[watchdog] 进程挂死 ${timeout_val}s: $desc (PID=$pid)" >&2
                # 持续报警：每隔30秒再响一次，直到进程结束
                while kill -0 "$pid" 2>/dev/null; do
                    sleep 30
                    beep 5 "STILL HUNG: $desc"
                done
                exit 0
            fi
        done
        # 进程正常结束 — 检查退出码
        wait "$pid" 2>/dev/null
        local ec=$?
        if [[ $ec -ne 0 ]]; then
            beep 3 "CRASH: $desc exit=$ec"
            echo "[watchdog] 进程崩溃 (exit=$ec): $desc (PID=$pid)" >&2
        fi
    ) &
    echo "[watchdog] 监控 PID=$pid ($desc) 超时=${timeout_val}s"
}

# 监控当前 shell 所有后台 jobs
watchdog_all() {
    local timeout_val="${1:-$ALARM_TIMEOUT_DEFAULT}"
    local pids
    pids=$(jobs -p 2>/dev/null)
    if [[ -z "$pids" ]]; then
        echo "[watchdog] 没有后台进程" >&2
        return
    fi
    while IFS= read -r pid; do
        [[ -n "$pid" ]] && watchdog_bg "$pid" "$timeout_val" "job:$pid"
    done <<< "$pids"
}

# ─── PROMPT_COMMAND 自动钩子 ──────────────────────────────
# 每条命令执行完毕后检查退出码，非零则蜂鸣
_alarm_prompt_hook() {
    local last_exit=$?
    if [[ "$ALARM_HOOK_ON" == "1" && $last_exit -ne 0 ]]; then
        # 避免对 cd、export 等简单命令误报
        local cmd
        cmd=$(HISTTIMEFORMAT='' history 1 | sed 's/^[ ]*[0-9]*[ ]*//')
        case "$cmd" in
            cd\ *|export\ *|alias\ *|source\ *|clear|ls|pwd|echo\ *|true|false)
                return ;;
        esac
        beep 2 "CMD FAIL: exit=$last_exit"
        echo "[alarm] 上一条命令失败 (exit=$last_exit): $cmd" >&2
    fi
}

# ─── 注册钩子 ─────────────────────────────────────────────
# 安全追加到 PROMPT_COMMAND，不覆盖已有内容
if [[ "$ALARM_HOOK_ON" == "1" ]]; then
    case "$PROMPT_COMMAND" in
        *_alarm_prompt_hook*) ;;  # 已注册
        "")  PROMPT_COMMAND="_alarm_prompt_hook" ;;
        *)   PROMPT_COMMAND="_alarm_prompt_hook;${PROMPT_COMMAND}" ;;
    esac
fi

# ─── 快捷别名 ──────────────────────────────────────────────
alias r='run'
alias rt='run -t'

# ─── 导出 ─────────────────────────────────────────────────
export -f beep say_err run watchdog_bg watchdog_all _alarm_prompt_hook 2>/dev/null

echo "[global_alarm] 已加载: beep/run/watchdog_bg/watchdog_all (HOOK=$ALARM_HOOK_ON, TIMEOUT=${ALARM_TIMEOUT_DEFAULT}s)"

# ────────────────────────────────────────────────────────────────
# 7. ntfy.sh 手机推送通知集成
# ────────────────────────────────────────────────────────────────
NTFY_TOPIC="${NTFY_TOPIC:-jianglei-oneform-alerts}"
NTFY_URL="${NTFY_URL:-https://ntfy.sh}"
NTFY_ENABLED="${NTFY_ENABLED:-1}"  # 1=开启手机推送 0=关闭

ntfy_send() {
    local msg="${1:-Alert}"
    local priority="${2:-default}"  # min/low/default/high/max
    local title="${3:-终端报警}"
    
    if [[ "$NTFY_ENABLED" == "1" ]]; then
        curl -s \
            -H "Title: $title" \
            -H "Priority: $priority" \
            -H "Tags: warning" \
            -d "$msg" \
            "${NTFY_URL}/${NTFY_TOPIC}" &>/dev/null &
    fi
}

# 修改 beep 函数，增加 ntfy 推送
beep_with_ntfy() {
    local count="${1:-$ALARM_BEEP_COUNT}"
    local msg="${2:-ALERT}"
    
    # 本地蜂鸣
    beep "$count" "$msg"
    
    # 手机推送
    ntfy_send "$msg" "high" "🚨 终端报警"
}

# 用 beep_with_ntfy 替换 beep（可选）
# 取消注释下面这行来启用手机推送
# alias beep='beep_with_ntfy'

export -f ntfy_send beep_with_ntfy 2>/dev/null
echo "[ntfy] 已加载: 手机推送到 ${NTFY_URL}/${NTFY_TOPIC} (NTFY_ENABLED=$NTFY_ENABLED)"
