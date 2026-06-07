#!/usr/bin/env bash
# =========================================================================
#  Trae 试标工作流助手
#  python-timesheet × 7 prompts × 5 models = 35 evaluations
#
#  用法:  Claude 逐步骤调用以下函数
#  依赖:  xclip, docker (容器运行中), git (repo/ 已 init)
#  评分:  0=失败, 1=有瑕疵, 2=完美
#
#  模型执行顺序（实际操作顺序）:
#    1. Doubao-Seed-2.0-Code (seed 筛选, 必须 0 分)
#    2. GPT-5.4
#    3. Gemini 3.1 pro
#    4. DeepSeek-v4
#    5. 轮换: Prompt1/4/7→MinMax, Prompt2/5→GLM, Prompt3/6→Qwen
# =========================================================================
set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$BASE_DIR/repo"
LOG_FILE="$BASE_DIR/trial_log.csv"
TRAE_LOG_DIR="/home/jianglei/.config/Trae CN/logs"
TRAE_CLI_BIN="${TRAE_CLI_BIN:-trae-cn}"
TRAE_CHAT_MODE="${TRAE_CHAT_MODE:-agent}"        # ask | edit | agent
TRAE_CHAT_WINDOW_FLAG="${TRAE_CHAT_WINDOW_FLAG:---reuse-window}"
TRAE_CLI_TIMEOUT="${TRAE_CLI_TIMEOUT:-0}"        # 0 means no timeout

# ========== Prompt 定义 ==========

PROMPT1='请详细解释一下 `src/timesheet/services/entry_service.py` 中 `_calc_duration` 方法的实现逻辑，它是如何计算工时并处理跨天情况的？另外，为什么旧的 `old_duration_calc` 方法被废弃了，它存在什么精度和边界计算问题？'

PROMPT2='目前 `src/timesheet/services/entry_service.py` 中计时器功能使用了一个模块级别的内存字典 `self._timers` 模拟，导致应用重启时计时器状态会全部丢失。
请将其升级为数据库持久化存储：
1. 在 `TimeEntry` 模型中新增字段 `start_time_iso` (String) 和 `is_active_timer` (Boolean)。
2. 修改 `start_timer`，让它在启动计时器时，如果当前用户已经有运行的计时器，应抛出 `ValueError("已有正在运行的计时器")`，否则将计时器持久化到数据库。
3. 修改 `stop_timer` 逻辑，从数据库查找当前用户激活的计时器并计算时长，保存为正式工时记录，并将计时器标记为失效。
4. 相应重构数据访问层、Service 层逻辑和 `tests/test_entries.py` 中对应的单元测试。'

PROMPT3='目前在 `src/timesheet/services/entry_service.py` 中，用户创建工时时，系统只校验了单次工时是否超过上限（`settings.max_hours_per_day`）。
我们需要将其升级为"今日累计总工时上限校验"：
当用户通过 `create_entry` 创建记录时，系统应该先去数据库统计该用户在该日期已录入的全部工时之和（duration 累加），如果"已录入的累计工时"加上"当前准备创建的工时"超过了 `settings.max_hours_per_day`，则必须抛出 `ValueError("今日累计工时超过每日上限")` 异常。请完成逻辑修改并在 `tests/test_entries.py` 中补充测试。'

PROMPT4='目前 `src/timesheet/utils/export.py` 中导出的 Excel 只有原始明细。我们需要在所有数据行写入完成后，添加一个美化后的汇总行：
1. 在表格最下方留空一行，然后写入一行汇总行，首列单元格内容为"Total"。
2. 在工时时长（`duration`）对应的列（假设为 D 列），写入 Excel 计算公式 `=SUM(D2:Dn)`，其中 n 为数据结束行号。
3. 使用 `openpyxl` 的样式功能对"Total"这一行进行加粗处理，并设置单元格背景填充为淡灰色。
4. 请在 `tests/test_reports.py` 中添加测试用例，验证生成的 Excel 是否包含正确的公式和样式定义。'

PROMPT5='我们需要为工时审批流引入权限控制。请进行如下重构：
1. 在 `Project` 模型中新增字段 `manager_id` (Integer) 指代负责人。
2. 更新 Pydantic 校验 Schema `src/timesheet/schemas/project_schema.py` 允许设置该字段。
3. 修改 `src/timesheet/services/timesheet_service.py` 中的 `approve_timesheet` 和 `reject_timesheet` 方法：在操作时必须传入 `operator_id`，并校验操作人是否等于当前工时表关联项目的 `manager_id`，若无权操作则抛出 `PermissionError("无权审批该工时表")`。请同步修改相关的测试。'

PROMPT6='我们需要对项目的生命周期状态做更细致的管控：
1. 将 `Project` 模型中的布尔字段 `is_active` 改为枚举状态 `status`（包含值：`DRAFT`、`ONGOING`、`COMPLETED`、`SUSPENDED`）。
2. 修改项目创建和任务创建规则：只允许状态为 `ONGOING` 的项目创建任务或记录工时。
3. 如果项目处于 `COMPLETED` 或 `SUSPENDED` 状态，创建工时记录应抛出 `ValueError("当前项目不可录入工时")` 异常。
请重构所有受影响的 Schema、服务逻辑和数据访问层，并修正现有的测试。'

PROMPT7='我们需要在报表生成中支持弹性加班时长折算统计：
1. 修改 `src/timesheet/schemas/report_schema.py` 中的报表返回 Schema，新增 `overtime_hours` 和 `weighted_billable_hours` 两个可选的统计输出字段。
2. 修改 `src/timesheet/services/report_service.py` 中的 `generate_report` 逻辑：如果某用户在一天内记录的 `is_billable` 工时超过了 8 小时，则超过的部分计入 `overtime_hours`，且超过的部分在 `weighted_billable_hours` 中按 1.5 倍加权计算（例如某天工作了 10 小时，正常 8 小时 + 加班 2 * 1.5 = 11 小时）。
请修改计算逻辑并为其添加测试用例。'

# ========== 工具函数 ==========

# 根据 Prompt 编号获取文本
get_prompt() {
  local pn=$1
  eval "echo \"\$PROMPT$pn\""
}

# 获取第 5 个轮换模型的短名
get_rollout5_short() {
  local pn=$1  # prompt number 1-7
  local idx=$(( (pn - 1) % 3 ))
  case "$idx" in
    0) echo "minmax" ;;
    1) echo "glm" ;;
    2) echo "qwen" ;;
  esac
}

# 获取第 5 个轮换模型的全名
get_rollout5_name() {
  local pn=$1
  local idx=$(( (pn - 1) % 3 ))
  case "$idx" in
    0) echo "MinMax-M2.7" ;;
    1) echo "GLM-5.1" ;;
    2) echo "Qwen3.6-Plus" ;;
  esac
}

# 复制到剪贴板
copy_prompt() {
  local pn=$1
  local text=$(get_prompt "$pn")
  echo -n "$text" | xclip -selection clipboard
  echo "OK: 已复制 Prompt $pn 到剪贴板"
}

# 通过 Trae CLI 提交到 chat，绕过 Wayland GUI 粘贴/回车自动化
submit_prompt_cli() {
  local pn=$1
  local mode="${2:-$TRAE_CHAT_MODE}"
  local text
  text=$(get_prompt "$pn")

  if ! command -v "$TRAE_CLI_BIN" >/dev/null 2>&1; then
    echo "ERROR: 找不到 Trae CLI: $TRAE_CLI_BIN"
    return 1
  fi

  local args=(chat -m "$mode")
  if [ -n "$TRAE_CHAT_WINDOW_FLAG" ] && [ "$TRAE_CHAT_WINDOW_FLAG" != "none" ]; then
    args+=("$TRAE_CHAT_WINDOW_FLAG")
  fi
  args+=("$text")

  echo "OK: 通过 Trae CLI 提交 Prompt $pn (mode=$mode)"
  if [ "$TRAE_CLI_TIMEOUT" -gt 0 ]; then
    (cd "$REPO_DIR" && timeout "$TRAE_CLI_TIMEOUT" "$TRAE_CLI_BIN" "${args[@]}")
  else
    (cd "$REPO_DIR" && "$TRAE_CLI_BIN" "${args[@]}")
  fi
}

# 运行测试
run_tests() {
  cd "$REPO_DIR"
  python3 -m pytest tests/ -x -q 2>&1 | tail -3
}

# 保存 patch 并重置代码
save_patch_and_reset() {
  local pn=$1
  local model_short=$2
  local patch_name="prompt${pn}_${model_short}.patch"
  local patch_path="$BASE_DIR/$patch_name"

  cd "$REPO_DIR"
  git diff > "$patch_path" 2>/dev/null

  if [ -s "$patch_path" ]; then
    echo "OK: Patch 已保存 ($(wc -c < "$patch_path") bytes)"
  else
    echo "EMPTY: 无代码变更"
    echo "# Empty patch - no code changes" > "$patch_path"
  fi

  git reset --hard HEAD 2>/dev/null
  git clean -fd 2>/dev/null
  echo "OK: 代码已重置"
}

# 从 Trae 日志查找最新 Session ID
find_session_id() {
  local log_files
  log_files=$(find "$TRAE_LOG_DIR" -type f \( -name 'renderer.log' -o -name 'ai-agent*stdout.log' \) -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -30 | cut -d' ' -f2-)
  if [ -z "$log_files" ]; then
    echo "ERROR: 找不到 Trae 日志"
    return 1
  fi

  local log_file sid
  while IFS= read -r log_file; do
    sid=$(grep -hoP '(session_id[=:]"?|sessionId":"|preWarmSessionSnapshot (triggered|completed) |Session )\K[0-9a-f]{24}\b' "$log_file" 2>/dev/null | tail -1)
    if [ -n "$sid" ]; then
      echo "$sid"
      return 0
    fi
  done <<< "$log_files"

  echo "ERROR: 未找到 Session ID"
  return 1
}

# 记录结果到 CSV
log_result() {
  local pn=$1 model=$2 sid=$3 score=$4 reason=$5 patch=$6
  if [ ! -f "$LOG_FILE" ]; then
    echo "prompt,model,session_id,score,score_reason,patch_file" > "$LOG_FILE"
  fi
  echo "$pn,$model,$sid,$score,$reason,$patch" >> "$LOG_FILE"
  echo "OK: 已记录到日志"
}

# 显示进度
show_progress() {
  if [ ! -f "$LOG_FILE" ]; then
    echo "进度: 0 / 35"
    return
  fi
  local total=$(tail -n +2 "$LOG_FILE" 2>/dev/null | wc -l)
  echo "总进度: $total / 35"
  for p in 1 2 3 4 5 6 7; do
    local count=$(tail -n +2 "$LOG_FILE" 2>/dev/null | awk -F',' -v p="$p" '$1==p' | wc -l)
    echo "  Prompt $p: $count/5"
  done
}

# 检查环境
check_env() {
  # 检查 docker 容器
  if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q "python-timesheet-container"; then
    echo "WARN: 容器 python-timesheet-container 未运行"
  else
    echo "OK: 容器运行中"
  fi

  # 检查 xclip
  if ! command -v xclip &>/dev/null; then
    echo "ERROR: xclip 未安装"
    return 1
  fi
  echo "OK: xclip 可用"

  if command -v "$TRAE_CLI_BIN" &>/dev/null; then
    echo "OK: Trae CLI 可用 ($TRAE_CLI_BIN)"
  else
    echo "WARN: Trae CLI 不可用 ($TRAE_CLI_BIN)"
  fi

  # 检查 repo git
  if ! git -C "$REPO_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    echo "ERROR: repo/ 未初始化 git"
    return 1
  fi
  echo "OK: git 就绪"

  # 检查 Trae 进程
  if pgrep -f "trae-cn" >/dev/null 2>&1; then
    echo "OK: Trae 运行中"
  else
    echo "WARN: Trae 未运行"
  fi

  # 检查测试
  if cd "$REPO_DIR" && python3 -m pytest tests/ -q --tb=no 2>&1 | grep -q "passed"; then
    echo "OK: 测试可运行"
  else
    echo "WARN: 测试可能有问题"
  fi
}

# 获取日志文件路径
get_log_path() {
  ls -t "$TRAE_LOG_DIR"/2026*/Modular/ai-agent*stdout.log 2>/dev/null | head -1
}

# ========== 主流程（一键运行一次 rollout）==========
# 用于 Claude 逐步骤调用
# 参数: $1=prompt编号 $2=模型编号(1-5)
do_rollout() {
  local pn=$1 model_num=$2

  # 确定模型
  local model_name model_short
  case "$model_num" in
    1) model_name="Doubao-Seed-2.0-Code"; model_short="doubao" ;;
    2) model_name="GPT-5.4";              model_short="gpt5" ;;
    3) model_name="Gemini 3.1 pro";       model_short="gemini" ;;
    4) model_name="DeepSeek-v4";          model_short="deepseek" ;;
    5) model_name=$(get_rollout5_name "$pn"); model_short=$(get_rollout5_short "$pn") ;;
  esac

  echo "=== Prompt $pn → $model_name ==="
  return 0
}

case "${1:-}" in
  check_env)    check_env ;;
  copy_prompt)  copy_prompt "${2:-1}" ;;
  submit_prompt) submit_prompt_cli "${2:-1}" "${3:-$TRAE_CHAT_MODE}" ;;
  run_tests)    run_tests ;;
  save_reset)   save_patch_and_reset "${2:-1}" "${3:-doubao}" ;;
  find_sid)     find_session_id ;;
  log)          log_result "${2}" "${3}" "${4}" "${5}" "${6}" "${7}" ;;
  progress)     show_progress ;;
  get_prompt)   get_prompt "${2:-1}" ;;
  get_rollout5) echo "$(get_rollout5_name "${2:-1}") ($(get_rollout5_short "${2:-1}"))" ;;
  log_path)     get_log_path ;;
  *)
    echo "用法: $0 <command> [args]"
    echo ""
    echo "命令:"
    echo "  check_env                  检查运行环境"
    echo "  copy_prompt <pn>           复制 Prompt 到剪贴板"
    echo "  submit_prompt <pn> [mode]  通过 trae-cn chat 提交 Prompt"
    echo "  run_tests                  运行测试"
    echo "  save_reset <pn> <short>    保存 patch + git reset"
    echo "  find_sid                   从 Trae 日志找最新 Session ID"
    echo "  log <pn> <model> <sid> <score> <reason> <patch>  记录结果"
    echo "  progress                   显示进度"
    echo "  get_prompt <pn>            输出 Prompt 文本"
    echo "  get_rollout5 <pn>          输出第5个轮换模型名"
    echo "  log_path                   输出 Trae 日志路径"
    ;;
esac
