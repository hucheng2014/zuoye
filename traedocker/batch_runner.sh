#!/usr/bin/env bash
# =========================================================================
#  Trae 试标 - 批量自动处理器
#  支持 manual / cli / auto 三层：
#    manual: 复制 prompt 后人工在 Trae 发送，并人工确认完成
#    cli:    用 trae-cn chat 投递到 Trae GUI，人工确认新对话/模型/完成
#    auto:   仅在显式允许时等待 repo 稳定；默认禁用，避免误收空会话
# =========================================================================
set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNNER_PID="$BASHPID"
REPO_DIR="$BASE_DIR/repo"
LOG_FILE="$BASE_DIR/trial_log.csv"
RUNNER_LOCK_FILE="${TRAE_RUNNER_LOCK_FILE:-$BASE_DIR/.batch_runner.lock}"
TRAE_LOG_DIR="/Users/xaa/.config/Trae CN/logs"
DEFAULT_TRAE_CLI_BIN="trae-cn"
if [ -x "/usr/share/trae-cn/bin/trae-cn" ]; then
  DEFAULT_TRAE_CLI_BIN="/usr/share/trae-cn/bin/trae-cn"
fi
TRAE_CLI_BIN="${TRAE_CLI_BIN:-$DEFAULT_TRAE_CLI_BIN}"
TRAE_REPO_TARGET="${TRAE_REPO_TARGET:-docker}" # docker | local
TRAE_DOCKER_CONTAINER="${TRAE_DOCKER_CONTAINER:-studentsystem-container}"
TRAE_DOCKER_REPO_DIR="${TRAE_DOCKER_REPO_DIR:-/app}"
TRAE_REMOTE_HOST="${TRAE_REMOTE_HOST:-odc-studentsystem-container}"
TRAE_REMOTE_WORKSPACE_URI="${TRAE_REMOTE_WORKSPACE_URI:-vscode-remote://ssh-remote%2B${TRAE_REMOTE_HOST}${TRAE_DOCKER_REPO_DIR}}"
TRAE_SUBMIT_MODE="${TRAE_SUBMIT_MODE:-manual}"   # manual | cli | bridge
TRAE_CONFIRM_MODE="${TRAE_CONFIRM_MODE:-manual}" # manual | auto
TRAE_CHAT_MODE="${TRAE_CHAT_MODE:-agent}"        # ask | edit | agent
TRAE_CHAT_WINDOW_FLAG="${TRAE_CHAT_WINDOW_FLAG:---new-window}"
TRAE_CONTINUE_WINDOW_FLAG="${TRAE_CONTINUE_WINDOW_FLAG:---reuse-window}"
TRAE_ALLOW_REUSE_WINDOW="${TRAE_ALLOW_REUSE_WINDOW:-off}"
TRAE_CHAT_PROFILE="${TRAE_CHAT_PROFILE:-}"
TRAE_CHAT_PROFILE_PREFIX="${TRAE_CHAT_PROFILE_PREFIX:-}"
TRAE_AUTO_CONFIRM_ALLOWED="${TRAE_AUTO_CONFIRM_ALLOWED:-off}"
TRAE_CLI_TIMEOUT="${TRAE_CLI_TIMEOUT:-0}"        # 0 means no timeout
TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT="${TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT:-auto}" # auto | on | off
TRAE_WORKSPACE_FOCUS_SECONDS="${TRAE_WORKSPACE_FOCUS_SECONDS:-3}"
TRAE_AUTO_WAIT_TIMEOUT="${TRAE_AUTO_WAIT_TIMEOUT:-900}"
TRAE_AUTO_STABLE_SECONDS="${TRAE_AUTO_STABLE_SECONDS:-20}"
TRAE_AUTO_POLL_SECONDS="${TRAE_AUTO_POLL_SECONDS:-5}"
TRAE_AUTO_START_GRACE_SECONDS="${TRAE_AUTO_START_GRACE_SECONDS:-45}"
TRAE_MODEL_SWITCH="${TRAE_MODEL_SWITCH:-auto}"   # auto | off
if [ "$TRAE_REPO_TARGET" = "docker" ]; then
  DEFAULT_TRAE_MODEL_WORKSPACE="$TRAE_REMOTE_WORKSPACE_URI"
else
  DEFAULT_TRAE_MODEL_WORKSPACE="$REPO_DIR"
fi
TRAE_MODEL_WORKSPACE="${TRAE_MODEL_WORKSPACE:-$DEFAULT_TRAE_MODEL_WORKSPACE}"
TRAE_MODEL_STATE_BIN="${TRAE_MODEL_STATE_BIN:-$BASE_DIR/trae_model_state.py}"
TRAE_COMMAND_BRIDGE_BIN="${TRAE_COMMAND_BRIDGE_BIN:-$BASE_DIR/trae_command_bridge.py}"
TRAE_BRIDGE_TIMEOUT="${TRAE_BRIDGE_TIMEOUT:-30}"
TRAE_SETTINGS_JSON="${TRAE_SETTINGS_JSON:-$HOME/.config/Trae CN/User/settings.json}"
TRAE_PPE_CHECK="${TRAE_PPE_CHECK:-auto}"          # auto | off
TRAE_CONTINUE_TEXT="${TRAE_CONTINUE_TEXT:-继续}"
TRAE_CONTINUE_TIMES="${TRAE_CONTINUE_TIMES:-1}"
TRAE_CONTINUE_INTERVAL="${TRAE_CONTINUE_INTERVAL:-8}"
TRAE_AUTO_CONTINUE_ON_TIMEOUT="${TRAE_AUTO_CONTINUE_ON_TIMEOUT:-off}" # off | on
TRAE_AUTO_CONTINUE_MAX="${TRAE_AUTO_CONTINUE_MAX:-3}"
TRAE_REQUIRE_LOG_MODEL_MATCH="${TRAE_REQUIRE_LOG_MODEL_MATCH:-off}" # off | on
TRAE_NEW_TASK_MODE="${TRAE_NEW_TASK_MODE:-manual}" # manual | state | command | off
TRAE_REQUIRE_EXPECTED_SESSION="${TRAE_REQUIRE_EXPECTED_SESSION:-off}" # off | on
TRAE_AUTO_MODE_GUARD="${TRAE_AUTO_MODE_GUARD:-on}" # off | on
TEST_BASELINE_PASSED="${TEST_BASELINE_PASSED:-29}"

# ====== 评分与模型配置 ======
# 评分: 0=失败, 1=有瑕疵, 2=完美
# Doubao 在非解释题自动 0 分
# 其他模型根据测试结果决定

# 轮换规则: Prompt1/4/7→MinMax, Prompt2/5→GLM, Prompt3/6→Qwen
get_rollout5() {
  local pn=$1
  local idx=$(( (pn - 1) % 3 ))
  case "$idx" in
    0) echo "MinMax-M2.7:minmax" ;;
    1) echo "GLM-5.1:glm" ;;
    2) echo "Qwen3.6-Plus:qwen" ;;
  esac
}

rollout_model_spec() {
  local pn="$1" model_num="$2"
  case "$model_num" in
    1) echo "Doubao-Seed-2.0-Code:doubao" ;;
    2) echo "GPT-5.4:gpt5" ;;
    3) echo "Gemini 3.1 pro:gemini" ;;
    4) echo "DeepSeek-v4:deepseek" ;;
    5) get_rollout5 "$pn" ;;
    *) echo "ERROR: model_num must be 1..5" >&2; return 1 ;;
  esac
}

# ====== 工具函数 ======
get_prompt() {
  local pn=$1
  case "$pn" in
    1) echo -n '请详细解释 `studentsystem.py` 中学生信息的录入、保存、查询、删除、修改与排序流程：`insert/save` 如何把字典写入 `students.txt`，`search/delete/modify/sort` 又如何读取并回写文件。另外，请指出使用 `eval` 解析文件行、`save` 追加写入、以及 `search` 中用 `is not ""` 判断字符串等实现会带来哪些数据一致性和安全风险。' ;;
    2) echo -n '目前 `insert()` 允许重复 ID 追加写入，且空 ID/姓名时只是跳出循环，没有明确提示。请完善录入校验：1. `id` 和 `name` 不能为空，否则抛出 `ValueError("学生ID和姓名不能为空")`。2. 新录入前检查 `students.txt` 中是否已存在相同 `id`，重复时抛出 `ValueError("学生ID已存在")`。3. 将校验逻辑抽到 `validate_student_record(record, existing_ids)` 供 `insert` 复用。4. 在 `tests/` 中补充测试覆盖成功录入、空字段、重复 ID，以及重复录入不会追加第二条同 ID 记录。' ;;
    3) echo -n '目前 `search()` 用 `eval` 解析每行记录，并用 `id is not ""` / `name is not ""` 判断查询条件，存在安全和逻辑隐患。请改为安全读取：1. 新增 `load_students()`，用 `ast.literal_eval` 逐行解析 `students.txt`，文件不存在时返回空列表，格式错误时抛出 `ValueError("学生数据格式无效")`。2. `search()` 改为基于 `load_students()` 过滤，并使用 `==` 比较 ID/姓名。3. 保留原有交互菜单，但查无结果时打印 `未找到匹配学生`。4. 补充测试覆盖按 ID/姓名查询、无结果提示、损坏数据行报错。' ;;
    4) echo -n '目前 `modify()` 在找不到目标 ID 时仍会原样写回所有行，且 `delete()` 删除后会再次调用 `show()` 造成重复输出。请修复修改/删除流程：1. `modify()` 找不到 ID 时抛出 `ValueError("学生不存在")`，且不得丢失其他记录。2. `delete()` 删除成功后只打印一次结果，不再自动调用 `show()`。3. 抽取 `rewrite_students(records)` 统一覆盖写回 `students.txt`。4. 补充测试覆盖修改成功、修改不存在 ID、删除后文件只剩目标记录、以及删除不存在 ID 的提示。' ;;
    5) echo -n '目前成绩录入只校验能转成整数，不限制合理区间，可能出现负分或超过 100 分。请增加成绩边界校验：1. 新增 `validate_scores(english, python, c)`，三门课成绩都必须是 0-100 的整数，否则抛出 `ValueError("成绩必须是0到100之间的整数")`。2. `insert()` 和 `modify()` 录入成绩时统一调用该校验。3. 非法输入时保留现有重试交互，不要崩溃退出。4. 补充测试覆盖合法分数、负数、超 100、非整数输入。' ;;
    6) echo -n '目前 `show_student()` 只显示总分，无法快速看到平均分。请增强展示：1. 在表头和每行数据中新增 `平均分` 列，计算 `(english + python + c) / 3` 并保留 1 位小数。2. `total()` 除人数外，再输出全体平均总分 `(sum(total)/count)`，保留 1 位小数；没有学生时仍保持现有提示。3. 保持原有列对齐风格，不要破坏菜单其它功能。4. 补充测试覆盖单行平均分、多行展示、total 平均分和空文件提示。' ;;
    7) echo -n '目前 `save()` 采用追加写入，重复导入或修复后容易产生重复记录，也缺少统一读取入口。请重构存储层：1. 用 `load_students()` 读取全部学生到列表；没有文件时返回空列表。2. 将 `save(student)` 改为 `save_students(records)`，按 ID 覆盖更新后整文件重写，不再追加。3. `insert()` 录入完成后应基于内存列表去重保存，避免同一 ID 多条记录。4. 保持 `show/search/delete/modify/sort` 行为兼容。5. 补充测试覆盖重复 ID 覆盖写入、整文件重写、以及加载空文件。' ;;
    *) echo "Invalid prompt"; return 1 ;;
  esac
}

copy_prompt() {
  local pn=$1
  local text
  text=$(get_prompt "$pn")
  if ! command -v xclip >/dev/null 2>&1; then
    if [ "$TRAE_SUBMIT_MODE" = "manual" ]; then
      echo "ERROR: 找不到 xclip，无法复制 Prompt $pn 到剪贴板" >&2
      return 1
    fi
    echo "WARN: 找不到 xclip，跳过剪贴板复制；当前提交模式为 $TRAE_SUBMIT_MODE"
    return 0
  fi
  if echo -n "$text" | xclip -selection clipboard 9>&-; then
    echo "✅ Prompt $pn 已复制到剪贴板"
    return 0
  fi
  if [ "$TRAE_SUBMIT_MODE" = "manual" ]; then
    echo "ERROR: 复制 Prompt $pn 到剪贴板失败" >&2
    return 1
  fi
  echo "WARN: 复制 Prompt $pn 到剪贴板失败；当前提交模式为 $TRAE_SUBMIT_MODE，继续通过自动通道提交"
}

activate_trae_workspace() {
  if [ "$TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT" = "off" ]; then
    return 0
  fi
  if [ "$TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT" = "auto" ] && [ "$TRAE_REPO_TARGET" != "docker" ]; then
    return 0
  fi
  if [ "$TRAE_REPO_TARGET" != "docker" ]; then
    echo "WARN: TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT 仅支持 Docker/remote workspace 目标"
    return 0
  fi
  if ! command -v "$TRAE_CLI_BIN" >/dev/null 2>&1; then
    echo "ERROR: 找不到 Trae CLI: $TRAE_CLI_BIN"
    return 1
  fi

  echo "  → 聚焦 Trae 远程工作区: $TRAE_REMOTE_WORKSPACE_URI" >&2
  "$TRAE_CLI_BIN" --reuse-window --folder-uri "$TRAE_REMOTE_WORKSPACE_URI" >/dev/null 2>&1 || {
    echo "ERROR: 无法聚焦远程工作区: $TRAE_REMOTE_WORKSPACE_URI"
    return 1
  }
  sleep "$TRAE_WORKSPACE_FOCUS_SECONDS"
}

target_repo_label() {
  if [ "$TRAE_REPO_TARGET" = "docker" ]; then
    echo "docker:${TRAE_DOCKER_CONTAINER}:${TRAE_DOCKER_REPO_DIR}"
  else
    echo "local:${REPO_DIR}"
  fi
}

repo_cmd() {
  if [ "$TRAE_REPO_TARGET" = "docker" ]; then
    docker exec -e TRAE_TARGET_REPO_DIR="$TRAE_DOCKER_REPO_DIR" "$TRAE_DOCKER_CONTAINER" \
      sh -lc 'cd "$TRAE_TARGET_REPO_DIR" && "$@"' sh "$@"
  elif [ "$TRAE_REPO_TARGET" = "local" ]; then
    (cd "$REPO_DIR" && "$@")
  else
    echo "ERROR: TRAE_REPO_TARGET 只能是 docker 或 local，当前为: $TRAE_REPO_TARGET" >&2
    return 1
  fi
}

clean_repo_caches() {
  repo_cmd find . -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
}

check_target_repo() {
  if [ "$TRAE_REPO_TARGET" = "docker" ]; then
    if ! docker ps --format '{{.Names}}' | grep -Fxq "$TRAE_DOCKER_CONTAINER"; then
      echo "ERROR: Docker 容器未运行: $TRAE_DOCKER_CONTAINER"
      return 1
    fi
  fi
  if ! repo_cmd test -d .git; then
    echo "ERROR: 目标仓库没有 .git: $(target_repo_label)"
    return 1
  fi

  clean_repo_caches
  local status
  status=$(repo_cmd git status --short)
  if [ -n "$status" ]; then
    echo "ERROR: 目标仓库不是干净基线: $(target_repo_label)"
    echo "$status"
    return 1
  fi
  echo "  → 目标仓库: $(target_repo_label)"
}

submit_prompt_cli() {
  local pn="$1"
  local mode="${2:-$TRAE_CHAT_MODE}"
  local model_short="${3:-}"
  local text
  text=$(get_prompt "$pn")

  if ! command -v "$TRAE_CLI_BIN" >/dev/null 2>&1; then
    echo "ERROR: 找不到 Trae CLI: $TRAE_CLI_BIN"
    return 1
  fi

  activate_trae_workspace

  local args=(chat -m "$mode")
  if [ -n "$TRAE_CHAT_WINDOW_FLAG" ] && [ "$TRAE_CHAT_WINDOW_FLAG" != "none" ]; then
    args+=("$TRAE_CHAT_WINDOW_FLAG")
  fi
  local profile="$TRAE_CHAT_PROFILE"
  if [ -z "$profile" ] && [ -n "$TRAE_CHAT_PROFILE_PREFIX" ] && [ -n "$model_short" ]; then
    profile="${TRAE_CHAT_PROFILE_PREFIX}-${model_short}"
  fi
  if [ -n "$profile" ]; then
    args+=(--profile "$profile")
  fi
  args+=("$text")

  echo "  → CLI 提交: $TRAE_CLI_BIN ${args[*]:0:4} ..."
  if [ "$TRAE_CLI_TIMEOUT" -gt 0 ]; then
    (cd "$REPO_DIR" && timeout "$TRAE_CLI_TIMEOUT" "$TRAE_CLI_BIN" "${args[@]}")
  else
    (cd "$REPO_DIR" && "$TRAE_CLI_BIN" "${args[@]}")
  fi
}

submit_prompt_bridge() {
  local pn="$1" model_short="$2"
  local text
  text=$(get_prompt "$pn")

  if [ ! -f "$TRAE_COMMAND_BRIDGE_BIN" ]; then
    echo "ERROR: 找不到 Trae command bridge: $TRAE_COMMAND_BRIDGE_BIN" >&2
    return 1
  fi

  activate_trae_workspace
  echo "  → Bridge 提交: newSession=true model=$model_short" >&2
  printf '%s' "$text" | python3 "$TRAE_COMMAND_BRIDGE_BIN" send \
    --model "$model_short" \
    --new-session \
    --workspace "$TRAE_MODEL_WORKSPACE" \
    --timeout "$TRAE_BRIDGE_TIMEOUT"
}

check_cli_window_mode() {
  if [ "$TRAE_SUBMIT_MODE" != "cli" ] && [ "$TRAE_SUBMIT_MODE" != "bridge" ]; then
    return 0
  fi
  if [ "$TRAE_SUBMIT_MODE" = "bridge" ]; then
    if [ ! -f "$TRAE_COMMAND_BRIDGE_BIN" ]; then
      echo "ERROR: 找不到 Trae command bridge: $TRAE_COMMAND_BRIDGE_BIN"
      return 1
    fi
    if [ "$TRAE_REPO_TARGET" = "docker" ] && [ "$TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT" = "off" ]; then
      echo "ERROR: Docker bridge 自动提交必须先聚焦远程工作区，请保持 TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT=on/auto。"
      return 1
    fi
    return 0
  fi
  if [ "$TRAE_REPO_TARGET" = "docker" ] && [ "${TRAE_CLI_DOCKER_ALLOWED:-off}" != "on" ]; then
    echo "ERROR: Docker 目标下默认禁止 CLI 直接提交。"
    echo "       trae-cn chat 会投递到 Trae GUI，但不能可靠证明命中远程 Docker /app 的新会话。"
    echo "       请使用 TRAE_SUBMIT_MODE=manual，或确认风险后显式设置 TRAE_CLI_DOCKER_ALLOWED=on。"
    return 1
  fi
  if [ "$TRAE_REPO_TARGET" = "docker" ] && [ "${TRAE_CLI_DOCKER_ALLOWED:-off}" = "on" ]; then
    if [ "$TRAE_CHAT_WINDOW_FLAG" != "--reuse-window" ] && [ "${TRAE_CLI_DOCKER_UNSAFE_NEW_WINDOW:-off}" != "on" ]; then
      echo "ERROR: Docker 自动提交必须使用 TRAE_CHAT_WINDOW_FLAG=--reuse-window。"
      echo "       runner 会先聚焦 $TRAE_REMOTE_WORKSPACE_URI，再把 chat 投递到该窗口。"
      return 1
    fi
    if [ "$TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT" = "off" ] && [ "${TRAE_CLI_DOCKER_UNSAFE_NEW_WINDOW:-off}" != "on" ]; then
      echo "ERROR: Docker 自动提交必须先聚焦远程工作区，请保持 TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT=on/auto。"
      return 1
    fi
  fi
  if [ "$TRAE_CHAT_WINDOW_FLAG" = "--reuse-window" ] && [ "$TRAE_ALLOW_REUSE_WINDOW" != "on" ]; then
    echo "ERROR: CLI 当前配置会复用已有 GUI 窗口/会话。"
    echo "       请使用默认 --new-window，或显式设置 TRAE_ALLOW_REUSE_WINDOW=on。"
    return 1
  fi
}

check_confirm_mode() {
  if [ "$TRAE_CONFIRM_MODE" = "auto" ] && [ "$TRAE_AUTO_CONFIRM_ALLOWED" != "on" ]; then
    echo "ERROR: 自动确认默认禁用。当前 Trae CLI 会打开/投递到 GUI，不能可靠证明新对话、模型和发送完成。"
    echo "       请使用 TRAE_CONFIRM_MODE=manual，或在完成额外验证后显式设置 TRAE_AUTO_CONFIRM_ALLOWED=on。"
    return 1
  fi
}

acquire_runner_lock() {
  if [ "${TRAE_RUNNER_LOCK_DISABLED:-off}" = "on" ]; then
    return 0
  fi
  exec 9>"$RUNNER_LOCK_FILE"
  if ! flock -n 9; then
    echo "ERROR: 已有 batch_runner 正在运行；为避免复用会话或重置未记录代码，拒绝启动。"
    echo "       lock: $RUNNER_LOCK_FILE"
    return 1
  fi
}

privacy_status() {
  local log_files status log_file
  log_files=$(find "$TRAE_LOG_DIR" -type f -name '*.log' -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -80 | cut -d' ' -f2-)
  if [ -z "$log_files" ]; then
    echo "unknown"
    return 1
  fi

  while IFS= read -r log_file; do
    status=$(grep -hoP '(new_mode is |privacy_mode":"|is_privacy_mode":)\K(Off|On|off|on|0|1)' "$log_file" 2>/dev/null | tail -1)
    if [ -n "$status" ]; then
      break
    fi
  done <<< "$log_files"

  case "$status" in
    Off|off|0) echo "off" ;;
    On|on|1) echo "on" ;;
    *) echo "unknown"; return 1 ;;
  esac
}

check_privacy_mode() {
  local status
  status=$(privacy_status || true)
  case "$status" in
    off)
      echo "  → Trae 隐私模式: off"
      ;;
    on)
      echo "ERROR: Trae 隐私模式为 on，请先关闭后再跑自动化"
      return 1
      ;;
    *)
      echo "WARN: 无法从日志确认 Trae 隐私模式；当前继续执行"
      ;;
  esac
}

check_manual_model_after_auto_switch() {
  local model_name="$1"
  if [ "$TRAE_AUTO_MODE_GUARD" = "off" ]; then
    return 0
  fi
  if [ "$TRAE_SUBMIT_MODE" != "bridge" ] && [ "$TRAE_CONFIRM_MODE" != "auto" ]; then
    return 0
  fi

  python3 - "$TRAE_LOG_DIR" "$model_name" <<'PY'
import json
import re
import sys
from pathlib import Path

log_dir = Path(sys.argv[1])
target = sys.argv[2]

files = []
if log_dir.exists():
    files = sorted(
        [p for p in log_dir.rglob("renderer.log")],
        key=lambda p: (p.stat().st_mtime, str(p)),
    )

last_auto = None
last_target_manual_evidence = None
order = 0
payload_re = re.compile(r"params:\s+(\{.*\})")

for path in files:
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        continue
    for lineno, line in enumerate(lines, 1):
        order += 1
        if "switch auto mode when model offline" in line:
            last_auto = (order, str(path), lineno, line[:240])
            continue
        if (
            "model_select_click" not in line
            and "code_comp_trigger" not in line
            and "code_comp_shown" not in line
            and "code_comp_complete_shown" not in line
        ):
            continue
        match = payload_re.search(line)
        if not match:
            continue
        try:
            payload = json.loads(match.group(1))
        except Exception:
            continue
        chat_model = str(payload.get("chat_model") or "")
        if chat_model.lower() != target.lower():
            continue
        if payload.get("chat_model_mode") == "manual":
            last_target_manual_evidence = (order, str(path), lineno, line[:240])
            continue
        if payload.get("is_auto_mode") == 0:
            last_target_manual_evidence = (order, str(path), lineno, line[:240])

if not last_auto:
    raise SystemExit(0)
if last_target_manual_evidence and last_target_manual_evidence[0] > last_auto[0]:
    raise SystemExit(0)

print("ERROR: Trae 最近一次模型离线后已切换到 Auto，且之后没有看到目标模型的手动选择日志。")
print(f"       target_model: {target}")
if last_auto:
    print(f"       last_auto: {last_auto[1]}:{last_auto[2]}")
if last_target_manual_evidence:
    print(f"       last_manual_target: {last_target_manual_evidence[1]}:{last_target_manual_evidence[2]}")
else:
    print("       last_manual_target: NOT_FOUND")
print("       请在 Trae 输入框模型选择器中手动选择目标模型后再重试。")
raise SystemExit(1)
PY
}

check_ppe_config() {
  if [ "$TRAE_PPE_CHECK" = "off" ]; then
    echo "  → Trae PPE 配置检查: off"
    return 0
  fi

  python3 - "$TRAE_SETTINGS_JSON" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1]).expanduser()
required = {
    "ai_assistant.request.env": "ppe",
    "ai_assistant.request.ppe": "ppe_data_label_trae",
}
recommended = {
    "git.openRepositoryInParentFolders": "always",
    "AI.toolcall.v2.command.allowList": "[\"sort\",\"tail\",\"cp\"]",
    "AI.toolcall.reviewMode.ide": "skip",
    "AI.toolcall.reviewMode.solo": "skip",
    "AI.toolcall.v2.ide.mcp.autoRun": "alwaysRun",
    "AI.toolcall.v2.ide.command.mode": "alwaysRun",
    "AI.toolcall.v2.solo.command.mode": "alwaysRun",
    "AI.rules.importClaudeMd": True,
    "AI.toolcall.v2.fileOp.allowPaths": "[\"kill\"]",
}

if not settings_path.exists():
    print(f"ERROR: Trae settings.json 不存在: {settings_path}")
    sys.exit(1)

try:
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
except Exception as exc:
    print(f"ERROR: 无法读取 Trae settings.json: {exc}")
    sys.exit(1)

bad = []
for key, expected in required.items():
    actual = settings.get(key)
    if actual != expected:
        bad.append(f"{key}: {actual!r} != {expected!r}")

if bad:
    print("ERROR: Trae PPE 配置不正确:")
    for item in bad:
        print(f"  - {item}")
    sys.exit(1)

print("  → Trae PPE: ppe / ppe_data_label_trae")
missing = []
for key, expected in recommended.items():
    actual = settings.get(key)
    if actual != expected:
        missing.append(f"{key}: {actual!r} != {expected!r}")
if missing:
    print("WARN: Trae 自动化推荐配置不完整:")
    for item in missing:
        print(f"  - {item}")
PY
}

send_continue_cli() {
  local times="${1:-$TRAE_CONTINUE_TIMES}"
  local text="${2:-$TRAE_CONTINUE_TEXT}"

  if ! command -v "$TRAE_CLI_BIN" >/dev/null 2>&1; then
    echo "ERROR: 找不到 Trae CLI: $TRAE_CLI_BIN"
    return 1
  fi

  local i
  for ((i = 1; i <= times; i++)); do
    local args=(chat -m "$TRAE_CHAT_MODE")
    if [ -n "$TRAE_CONTINUE_WINDOW_FLAG" ] && [ "$TRAE_CONTINUE_WINDOW_FLAG" != "none" ]; then
      args+=("$TRAE_CONTINUE_WINDOW_FLAG")
    fi
    args+=("$text")

    echo "  → 发送继续 [$i/$times]: $text"
    (cd "$REPO_DIR" && "$TRAE_CLI_BIN" "${args[@]}")
    if [ "$i" -lt "$times" ]; then
      sleep "$TRAE_CONTINUE_INTERVAL"
    fi
  done
}

capture_log_offsets() {
  python3 - "$TRAE_LOG_DIR" <<'PY'
from pathlib import Path
import sys

log_dir = Path(sys.argv[1])
files = []
if log_dir.exists():
    files = sorted(
        [p for p in log_dir.rglob("*.log") if p.name == "renderer.log" or p.name.startswith("ai-agent")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:100]
for path in files:
    try:
        print(f"{path}\t{path.stat().st_size}")
    except OSError:
        pass
PY
}

switch_model_state() {
  local model_short="$1" model_name="$2"

  if [ "$TRAE_MODEL_SWITCH" = "off" ]; then
    echo "  → Trae 模型状态切换: off"
    return 0
  fi
  if [ ! -f "$TRAE_MODEL_STATE_BIN" ]; then
    echo "WARN: 找不到模型状态脚本: $TRAE_MODEL_STATE_BIN"
    return 1
  fi

  echo "  → 写入 Trae 模型状态: $model_name"
  python3 "$TRAE_MODEL_STATE_BIN" set "$model_short" --workspace "$TRAE_MODEL_WORKSPACE"
}

current_trae_session() {
  if [ ! -f "$TRAE_MODEL_STATE_BIN" ]; then
    echo "NOT_FOUND"
    return 1
  fi
  python3 "$TRAE_MODEL_STATE_BIN" current-session --workspace "$TRAE_MODEL_WORKSPACE"
}

create_new_trae_task() {
  local model_short="$1"

  if [ "$TRAE_NEW_TASK_MODE" = "off" ] || [ "$TRAE_NEW_TASK_MODE" = "manual" ]; then
    return 0
  fi
  if [ "$TRAE_NEW_TASK_MODE" = "command" ]; then
    echo "  → Trae 新建任务: command bridge 将在提交时创建真实会话" >&2
    return 0
  fi
  if [ "$TRAE_NEW_TASK_MODE" != "state" ]; then
    echo "ERROR: TRAE_NEW_TASK_MODE 只能是 manual、state、command 或 off，当前为: $TRAE_NEW_TASK_MODE" >&2
    return 1
  fi
  if [ ! -f "$TRAE_MODEL_STATE_BIN" ]; then
    echo "ERROR: 找不到模型状态脚本: $TRAE_MODEL_STATE_BIN" >&2
    return 1
  fi

  local before sid after expected actual
  before=$(current_trae_session || true)
  echo "  → 当前 Trae session: ${before:-NOT_FOUND}" >&2
  sid=$(python3 "$TRAE_MODEL_STATE_BIN" new-session "$model_short" --workspace "$TRAE_MODEL_WORKSPACE")
  after=$(current_trae_session || true)
  if [[ ! "$sid" =~ ^[0-9a-f]{24}$ ]]; then
    echo "ERROR: 新建 Trae session 失败: $sid" >&2
    return 1
  fi
  if [ "$after" != "$sid" ]; then
    echo "ERROR: 新建 Trae session 后 currentSessionId 不一致。" >&2
    echo "       expected: $sid" >&2
    echo "       actual:   $after" >&2
    return 1
  fi
  if [ "$before" = "$sid" ]; then
    echo "ERROR: 新建 Trae session 没有改变当前会话: $sid" >&2
    return 1
  fi

  expected=$(expected_model_id "$model_short")
  actual=$(session_model_id "$sid" || true)
  if [ "$actual" != "$expected" ]; then
    echo "ERROR: 新建 Trae session 的模型绑定不正确。" >&2
    echo "       session_id: $sid" >&2
    echo "       expected:   $expected" >&2
    echo "       actual:     $actual" >&2
    return 1
  fi
  echo "  → 新建 Trae session: $sid" >&2
  echo "$sid"
}

list_model_state() {
  if [ ! -f "$TRAE_MODEL_STATE_BIN" ]; then
    echo "WARN: 找不到模型状态脚本: $TRAE_MODEL_STATE_BIN"
    return 1
  fi
  python3 "$TRAE_MODEL_STATE_BIN" list
}

read_new_logs() {
  local offsets_file="$1"
  python3 - "$TRAE_LOG_DIR" "$offsets_file" <<'PY'
from pathlib import Path
import sys

log_dir = Path(sys.argv[1])
offsets_path = Path(sys.argv[2])
offsets = {}
for line in offsets_path.read_text(errors="ignore").splitlines():
    if "\t" not in line:
        continue
    path, size = line.rsplit("\t", 1)
    try:
        offsets[Path(path)] = int(size)
    except ValueError:
        pass

files = []
if log_dir.exists():
    files = sorted(
        [p for p in log_dir.rglob("*.log") if p.name == "renderer.log" or p.name.startswith("ai-agent")],
        key=lambda p: p.stat().st_mtime,
    )

for path in files:
    try:
        start = offsets.get(path, 0)
        with path.open("rb") as fh:
            fh.seek(start)
            text = fh.read().decode("utf-8", errors="ignore")
    except OSError:
        continue
    if text:
        sys.stdout.write(text)
PY
}

session_log_status() {
  local sid="$1" offsets_file="$2"
  python3 - "$TRAE_LOG_DIR" "$offsets_file" "$sid" <<'PY'
from pathlib import Path
import sys

log_dir = Path(sys.argv[1])
offsets_path = Path(sys.argv[2])
sid = sys.argv[3]

offsets = {}
try:
    raw_offsets = offsets_path.read_text(errors="ignore").splitlines()
except OSError:
    raw_offsets = []

for line in raw_offsets:
    if "\t" not in line:
        continue
    path, size = line.rsplit("\t", 1)
    try:
        offsets[Path(path)] = int(size)
    except ValueError:
        pass

files = []
if log_dir.exists():
    files = sorted(
        [p for p in log_dir.rglob("*.log") if p.name == "renderer.log" or p.name.startswith("ai-agent")],
        key=lambda p: p.stat().st_mtime,
    )

lines = []
for path in files:
    try:
        start = offsets.get(path, 0)
        with path.open("rb") as fh:
            fh.seek(start)
            text = fh.read().decode("utf-8", errors="ignore")
    except OSError:
        continue
    lines.extend(line for line in text.splitlines() if sid in line)

if not lines:
    print("absent")
    raise SystemExit(1)

started_needles = (
    "chat_model",
    "code_comp_trigger",
    "tool_call_show",
    "file_tool_show",
    "run_script_show",
    "process_task",
    "do_chat",
)
completed_needles = (
    "code_comp_complete_shown",
    "reason=completed",
    "status=Completed",
)
error_needles = (
    "reason=error",
    "reason=user_stopped",
    "status=Failed",
    "status=Cancelled",
)

started = any(any(needle in line for needle in started_needles) for line in lines)
completed = any(any(needle in line for needle in completed_needles) for line in lines)
errored = any(any(needle in line for needle in error_needles) for line in lines)

if completed:
    print("completed")
elif errored:
    print("error")
elif started:
    print("started")
else:
    print("seen")
PY
}

session_log_model_guard() {
  local sid="$1" offsets_file="$2" model_short="$3"
  if [ "$TRAE_REQUIRE_LOG_MODEL_MATCH" != "on" ] || [ -z "$model_short" ]; then
    return 0
  fi

  local expected actual
  expected=$(expected_model_id "$model_short")
  actual=$(session_model_id_from_logs "$sid" "$offsets_file" || true)
  if [ "$actual" = "NOT_FOUND" ] || [ -z "$actual" ]; then
    return 0
  fi
  if [ "$actual" != "$expected" ]; then
    echo "ERROR: 本轮新增日志显示模型不是目标模型，立即停止等待。"
    echo "       session_id: $sid"
    echo "       expected:   $expected"
    echo "       actual:     $actual"
    return 1
  fi
}

repo_fingerprint() {
  {
    repo_cmd git status --porcelain=v1
    repo_cmd git diff --no-ext-diff --binary
    repo_cmd git diff --cached --no-ext-diff --binary
  } | sha256sum | awk '{print $1}'
}

wait_for_repo_stable() {
  local timeout="${TRAE_AUTO_WAIT_TIMEOUT}"
  local stable_seconds="${TRAE_AUTO_STABLE_SECONDS}"
  local poll_seconds="${TRAE_AUTO_POLL_SECONDS}"
  local grace_seconds="${TRAE_AUTO_START_GRACE_SECONDS}"
  local start now last_change last_fp fp

  start=$(date +%s)
  last_change="$start"
  last_fp=$(repo_fingerprint)

  echo "  → 自动等待: 最长 ${timeout}s，repo 连续稳定 ${stable_seconds}s 后继续"
  echo "  → 启动宽限: ${grace_seconds}s，避免 Trae 还没开始改代码就提前测试"

  while true; do
    sleep "$poll_seconds"
    now=$(date +%s)
    fp=$(repo_fingerprint)

    if [ "$fp" != "$last_fp" ]; then
      last_fp="$fp"
      last_change="$now"
      echo "  → 检测到 repo 变更，继续等待稳定..."
    fi

    if [ $((now - start)) -ge "$timeout" ]; then
      echo "WARN: 自动等待超时"
      return 2
    fi

    if [ $((now - start)) -ge "$grace_seconds" ] && [ $((now - last_change)) -ge "$stable_seconds" ]; then
      echo "  → repo 已稳定，继续"
      return 0
    fi
  done
}

wait_for_completion() {
  if [ "$TRAE_CONFIRM_MODE" = "auto" ]; then
    if [ -n "${TRAE_EXPECTED_SESSION_ID:-}" ]; then
      local wait_status start_timeout completion_timeout start_time now status
      start_timeout="${TRAE_SESSION_START_TIMEOUT:-120}"
      completion_timeout="${TRAE_AUTO_WAIT_TIMEOUT}"
      start_time=$(date +%s)
      echo "  → 自动确认: 等待 Trae 新 session 启动: $TRAE_EXPECTED_SESSION_ID"
      while true; do
        status=$(session_log_status "$TRAE_EXPECTED_SESSION_ID" "$TRAE_LOG_OFFSETS_FILE" || true)
        session_log_model_guard "$TRAE_EXPECTED_SESSION_ID" "$TRAE_LOG_OFFSETS_FILE" "${TRAE_EXPECTED_MODEL_SHORT:-}" || return 1
        if [ "$status" = "started" ] || [ "$status" = "completed" ]; then
          echo "  → 新 session 已进入日志: $status"
          break
        fi
        if [ "$status" = "error" ]; then
          echo "ERROR: 新 session 在日志中出现错误状态: $TRAE_EXPECTED_SESSION_ID"
          return 1
        fi
        now=$(date +%s)
        if [ $((now - start_time)) -ge "$start_timeout" ]; then
          echo "ERROR: 超时未看到新 session 的 Trae 执行日志。"
          echo "       session_id: $TRAE_EXPECTED_SESSION_ID"
          echo "       这表示 Trae 可能仍在复用旧内存会话；本轮不继续记录。"
          return 1
        fi
        sleep "$TRAE_AUTO_POLL_SECONDS"
      done

      start_time=$(date +%s)
      echo "  → 自动确认: 等待新 session 完成"
      while true; do
        status=$(session_log_status "$TRAE_EXPECTED_SESSION_ID" "$TRAE_LOG_OFFSETS_FILE" || true)
        session_log_model_guard "$TRAE_EXPECTED_SESSION_ID" "$TRAE_LOG_OFFSETS_FILE" "${TRAE_EXPECTED_MODEL_SHORT:-}" || return 1
        if [ "$status" = "completed" ]; then
          echo "  → 新 session 已完成"
          if ! wait_for_repo_stable; then
            echo "WARN: 新 session 完成后 repo 稳定等待超时，继续进入测试阶段"
          fi
          return 0
        fi
        if [ "$status" = "error" ]; then
          echo "ERROR: 新 session 在 Trae 日志中结束为错误/停止状态。"
          echo "       session_id: $TRAE_EXPECTED_SESSION_ID"
          return 1
        fi
        now=$(date +%s)
        if [ $((now - start_time)) -ge "$completion_timeout" ]; then
          wait_status="timeout"
          break
        fi
        sleep "$TRAE_AUTO_POLL_SECONDS"
      done

      if [ "$wait_status" = "timeout" ]; then
        echo "WARN: 等待新 session 完成超时"
        if [ "$TRAE_AUTO_CONTINUE_ON_TIMEOUT" != "on" ]; then
          echo "WARN: 未启用自动继续，继续进入测试阶段"
          return 0
        fi
      fi
    fi

    local continue_count=0
    while true; do
      if wait_for_repo_stable; then
        return 0
      fi

      if [ "$TRAE_AUTO_CONTINUE_ON_TIMEOUT" != "on" ]; then
        echo "WARN: 未启用自动继续，继续进入测试阶段"
        return 0
      fi
      if [ "$continue_count" -ge "$TRAE_AUTO_CONTINUE_MAX" ]; then
        echo "WARN: 自动继续已达上限 ${TRAE_AUTO_CONTINUE_MAX} 次，继续进入测试阶段"
        return 0
      fi

      continue_count=$((continue_count + 1))
      echo "  → 自动等待超时，尝试发送继续恢复 (${continue_count}/${TRAE_AUTO_CONTINUE_MAX})"
      send_continue_cli 1 "$TRAE_CONTINUE_TEXT" || return 1
      echo "  → 已发送继续，重新等待 repo 稳定"
    done
  fi

  local input
  read -p "  ⏳ 等 AI 回复完毕后，输入 '好了' 继续: " input
  while [[ "$input" != "好了" && "$input" != "ok" && "$input" != "done" ]]; do
    read -p "  输入 '好了' 继续: " input
  done
}

show_prompt() {
  local pn=$1
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "  📋 Prompt $pn"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  case "$pn" in
    1) echo "  背景: 学生信息录入、保存、查询与排序流程"
       echo "  需求: 解释 insert/save/search/delete/modify/sort 与 students.txt 的关系"
       echo "  关键: 纯解释题，通常用 ask 模式，无需代码 diff" ;;
    2) echo "  背景: 录入允许重复 ID 且空字段处理不明确"
       echo "  需求: validate_student_record + 重复 ID 拦截 + 测试"
       echo "  关键: 录入校验、重复检测、文件不追加重复记录" ;;
    3) echo "  背景: search 使用 eval 和不安全的字符串比较"
       echo "  需求: load_students + ast.literal_eval + 查无结果提示"
       echo "  关键: 安全解析、按 ID/姓名过滤、损坏数据报错" ;;
    4) echo "  背景: modify/delete 写回和输出行为有缺陷"
       echo "  需求: rewrite_students + 不存在 ID 报错 + 删除后不再 show"
       echo "  关键: 覆盖写回、不丢记录、删除提示准确" ;;
    5) echo "  背景: 成绩只校验整数，不限制 0-100"
       echo "  需求: validate_scores + insert/modify 复用 + 测试"
       echo "  关键: 边界分数、非法输入重试、不崩溃退出" ;;
    6) echo "  背景: 展示只有总分，没有平均分"
       echo "  需求: show_student 增加平均分列 + total 输出全体平均"
       echo "  关键: 保留列对齐、空文件提示不变" ;;
    7) echo "  背景: save 追加写入易产生重复记录"
       echo "  需求: load_students + save_students 整文件重写"
       echo "  关键: 按 ID 覆盖、insert 去重保存、兼容现有功能" ;;
  esac
  echo ""
}

extract_sid() {
  local offsets_file="${1:-}"
  if [ -n "$offsets_file" ] && [ -f "$offsets_file" ]; then
    python3 - "$TRAE_LOG_DIR" "$offsets_file" <<'PY'
from pathlib import Path
import re
import sys

log_dir = Path(sys.argv[1])
offsets_path = Path(sys.argv[2])
offsets = {}
for line in offsets_path.read_text(errors="ignore").splitlines():
    if "\t" not in line:
        continue
    path, size = line.rsplit("\t", 1)
    try:
        offsets[Path(path)] = int(size)
    except ValueError:
        pass

pattern = re.compile(r'(?:session_id[=:]"?|sessionId":"|preWarmSessionSnapshot (?:triggered|completed) |Session )([0-9a-f]{24})\b')
files = []
if log_dir.exists():
    files = sorted(
        [p for p in log_dir.rglob("*.log") if p.name == "renderer.log" or p.name.startswith("ai-agent")],
        key=lambda p: p.stat().st_mtime,
    )

matches = []
for path in files:
    try:
        start = offsets.get(path, 0)
        with path.open("rb") as fh:
            fh.seek(start)
            text = fh.read().decode("utf-8", errors="ignore")
    except OSError:
        continue
    matches.extend(pattern.findall(text))

if matches:
    print(matches[-1])
    raise SystemExit(0)
print("NOT_FOUND")
raise SystemExit(1)
PY
    return
  fi

  local log_files
  log_files=$(find "$TRAE_LOG_DIR" -type f \( -name 'renderer.log' -o -name 'ai-agent*stdout.log' \) -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -30 | cut -d' ' -f2-)
  if [ -z "$log_files" ]; then
    echo "ERROR"
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

  echo "NOT_FOUND"
  return 1
}

make_patch() {
  local pn=$1 model_short=$2
  local patch_name="prompt${pn}_${model_short}.patch"
  {
    repo_cmd git diff --no-ext-diff --binary
    repo_cmd git diff --cached --no-ext-diff --binary
    local untracked
    untracked=$(repo_cmd git ls-files --others --exclude-standard | grep -vE '(^|/)(__pycache__|\.pytest_cache)(/|$)|\.pyc$' || true)
    if [ -n "$untracked" ]; then
      repo_cmd git add --intent-to-add -- $untracked >/dev/null 2>&1
      repo_cmd git diff --no-ext-diff --binary -- $untracked
      repo_cmd git reset -- $untracked >/dev/null 2>&1
    fi
  } > "$BASE_DIR/$patch_name" 2>/dev/null
  if [ -s "$BASE_DIR/$patch_name" ]; then
    echo "$patch_name"
  else
    echo "# Empty" > "$BASE_DIR/$patch_name"
    echo "$patch_name"
  fi
}

patch_has_diff() {
  local patch_file="$1"
  grep -q '^diff --git ' "$BASE_DIR/$patch_file" 2>/dev/null
}

sid_already_logged() {
  local sid="$1"
  [ -f "$LOG_FILE" ] && awk -F',' -v sid="$sid" 'NR > 1 && $3 == sid { found = 1 } END { exit found ? 0 : 1 }' "$LOG_FILE"
}

session_model_id() {
  local sid="$1"
  python3 - "$TRAE_MODEL_STATE_BIN" "$TRAE_MODEL_WORKSPACE" "$sid" <<'PY'
import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

state_script = Path(sys.argv[1]).resolve()
workspace = sys.argv[2]
sid = sys.argv[3]

spec = importlib.util.spec_from_file_location("trae_model_state", state_script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

user_data_dir = mod.default_user_data_dir()
targets = mod.select_workspace_dbs(user_data_dir, workspace, False)
db_path = targets[0][0]
user_id = mod.find_user_id([db_path, mod.global_db(user_data_dir)], None)
key = f"{user_id}_ai-chat:sessionRelation:modelMap"
global_key = f"{user_id}_ai-chat:sessionRelation:globalModelMap"
memento_key = "memento/icube-ai-agent-storage"

try:
    con = sqlite3.connect(str(db_path), timeout=10)
    row = con.execute("select value from ItemTable where key = ?", (key,)).fetchone()
    global_row = con.execute("select value from ItemTable where key = ?", (global_key,)).fetchone()
    memento_row = con.execute("select value from ItemTable where key = ?", (memento_key,)).fetchone()
finally:
    try:
        con.close()
    except Exception:
        pass

model = None
if row:
    try:
        data = json.loads(row[0])
        model = data.get(sid, {}).get("dev_builder")
    except Exception:
        model = None

if model:
    print(model)
    raise SystemExit(0)

current_sid = None
if memento_row:
    try:
        memento = json.loads(memento_row[0])
        current_sid = memento.get("currentSessionId")
        if not current_sid:
            for item in memento.get("list", []):
                if item.get("isCurrent"):
                    current_sid = item.get("sessionId")
                    break
    except Exception:
        current_sid = None

if current_sid == sid and global_row:
    try:
        global_model = json.loads(global_row[0]).get("dev_builder")
    except Exception:
        global_model = None
    if global_model:
        print(global_model)
        raise SystemExit(0)

print("NOT_FOUND")
raise SystemExit(1)
PY
}

session_model_id_from_logs() {
  local sid="$1" offsets_file="${2:-}"
  python3 - "$TRAE_LOG_DIR" "$sid" "$offsets_file" <<'PY'
import json
from pathlib import Path
import re
import sys

log_dir = Path(sys.argv[1])
sid = sys.argv[2]
offsets_arg = sys.argv[3] if len(sys.argv) > 3 else ""

MODEL_IDS = {
    "Doubao-Seed-2.0-Code": "1_-_Doubao-Seed-2.0-Code",
    "doubao-seed-2.0-code": "1_-_Doubao-Seed-2.0-Code",
    "gpt-5.4": "1_-_gpt-5.4",
    "Gemini 3.1 pro": "1_-_gemini-3.1-p",
    "gemini-3.1-p": "1_-_gemini-3.1-p",
    "DeepSeek-v4": "1_-_DeepSeek-V4-Pro",
    "DeepSeek-V4-Pro": "1_-_DeepSeek-V4-Pro",
    "MiniMax-M2.7": "1_-_minimax-m2.7",
    "minimax-m2.7": "1_-_minimax-m2.7",
    "GLM-5.1": "1_-_glm-5.1",
    "glm-5.1": "1_-_glm-5.1",
    "Qwen3.6-Plus": "1_-_qwen-3.6-plus",
    "qwen-3.6-plus": "1_-_qwen-3.6-plus",
}

offsets = {}
if offsets_arg and offsets_arg != "-" and Path(offsets_arg).exists():
    for line in Path(offsets_arg).read_text(errors="ignore").splitlines():
        if "\t" not in line:
            continue
        path, size = line.rsplit("\t", 1)
        try:
            offsets[Path(path)] = int(size)
        except ValueError:
            pass

files = []
if log_dir.exists():
    files = sorted(
        [p for p in log_dir.rglob("*.log") if p.name == "renderer.log" or p.name.startswith("ai-agent")],
        key=lambda p: p.stat().st_mtime,
    )

models = []
auto_seen = False
for path in files:
    try:
        start = offsets.get(path, 0)
        with path.open("rb") as fh:
            fh.seek(start)
            text = fh.read().decode("utf-8", errors="ignore")
    except OSError:
        continue

    for line in text.splitlines():
        if sid not in line or "chat_model" not in line:
            continue
        for match in re.finditer(r'params:\s+(\{.*\})', line):
            try:
                payload = json.loads(match.group(1))
            except Exception:
                continue
            model = payload.get("chat_model")
            is_auto_mode = payload.get("is_auto_mode")
            if model == "auto" or str(is_auto_mode) == "1" or payload.get("chat_model_mode") == "auto":
                auto_seen = True
            if model:
                models.append(model)

if auto_seen:
    print("AUTO_MODE")
    raise SystemExit(0)

if not models:
    print("NOT_FOUND")
    raise SystemExit(1)

model_name = models[-1]
model_id = MODEL_IDS.get(model_name)
if not model_id:
    key = model_name.strip().lower().replace(" ", "-").replace("_", "-")
    model_id = MODEL_IDS.get(key)

if model_id:
    print(model_id)
    raise SystemExit(0)

print(model_name)
raise SystemExit(0)
PY
}

expected_model_id() {
  local model_short="$1"
  python3 - "$TRAE_MODEL_STATE_BIN" "$model_short" <<'PY'
import importlib.util
import sys
from pathlib import Path

state_script = Path(sys.argv[1]).resolve()
model = sys.argv[2]
spec = importlib.util.spec_from_file_location("trae_model_state", state_script)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print(mod.normalize_model(model))
PY
}

validate_rollout_outputs() {
  local pn="$1" sid="$2" patch_file="$3" model_short="$4" offsets_file="${5:-}" expected_sid="${6:-}"
  if [[ "$sid" == "ERROR" || "$sid" == "NOT_FOUND" || ! "$sid" =~ ^[0-9a-f]{24}$ ]]; then
    echo "ERROR: 未能从本轮 Trae 日志中提取新的 Session ID。"
    echo "       不写入 trial_log.csv；repo 保持当前状态供检查。"
    return 1
  fi
  if [ -n "$expected_sid" ] && [ "$sid" != "$expected_sid" ]; then
    echo "ERROR: 本轮日志提取的 Session ID 与新建任务不一致。"
    echo "       expected: $expected_sid"
    echo "       actual:   $sid"
    echo "       这通常表示 Trae 仍然复用了旧会话。"
    return 1
  fi
  if [ "$TRAE_REQUIRE_EXPECTED_SESSION" = "on" ] && [ -z "$expected_sid" ]; then
    echo "ERROR: 当前配置要求新建任务 Session ID，但本轮未创建/传入 expected_sid。"
    return 1
  fi
  if sid_already_logged "$sid"; then
    echo "ERROR: Session ID 已在 trial_log.csv 中出现: $sid"
    echo "       这通常表示 CLI 复用了旧会话或 session 提取仍然命中了旧日志。"
    return 1
  fi
  local expected actual
  expected=$(expected_model_id "$model_short")
  actual=$(session_model_id_from_logs "$sid" "$offsets_file" || true)
  if [ "$actual" = "NOT_FOUND" ] || [ -z "$actual" ]; then
    actual=$(session_model_id "$sid" || true)
  fi
  if [ "$actual" != "$expected" ]; then
    echo "ERROR: Session 模型绑定不匹配或未写入。"
    echo "       session_id: $sid"
    echo "       expected:   $expected"
    echo "       actual:     $actual"
    echo "       请确认 Trae 中为本轮新对话且模型为目标模型，再重试记录。"
    return 1
  fi
  if [ "$TRAE_REQUIRE_LOG_MODEL_MATCH" = "on" ]; then
    local log_actual
    log_actual=$(session_model_id_from_logs "$sid" "$offsets_file" || true)
    if [ "$log_actual" != "$expected" ]; then
      echo "ERROR: 本轮新增日志中没有目标模型证据。"
      echo "       session_id: $sid"
      echo "       expected:   $expected"
      echo "       log_actual: $log_actual"
      return 1
    fi
  fi
  if [ "$pn" -ge 2 ] && ! patch_has_diff "$patch_file"; then
    echo "ERROR: 代码修改题生成了空 patch: $patch_file"
    echo "       这通常表示 Trae 没有进入新编辑会话，或模型没有实际修改 repo。"
    echo "       不写入 trial_log.csv。"
    return 1
  fi
}

reset_repo() {
  repo_cmd git reset --hard HEAD >/dev/null 2>&1
  repo_cmd git clean -fd >/dev/null 2>&1
  clean_repo_caches
  echo "✅ 代码已重置"
}

run_tests_compact() {
  local output
  output=$(
    repo_cmd sh -lc '
      python3 -m pytest tests/ -x -q --tb=line 2>&1
      rc=$?
      find . -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
      exit "$rc"
    ' | tail -2
  )
  printf '%s\n' "$output"
}

decide_score() {
  local model="$1" pn="$2"
  if [ -n "${TRAE_SCORE_OVERRIDE:-}" ]; then
    echo "${TRAE_SCORE_OVERRIDE}:${TRAE_SCORE_REASON_OVERRIDE:-人工覆盖评分}"
    return
  fi

  if [ "$pn" -eq 1 ]; then
    echo "1:解释题无法通过 pytest 自动评测；默认记 1 分，复核后可用 TRAE_SCORE_OVERRIDE 和 TRAE_SCORE_REASON_OVERRIDE 覆盖"
    return
  fi

  # Doubao 在非解释题(Prompt 2-7)自动 0 分
  if [[ "$model" == *Doubao* ]] && [ "$pn" -ge 2 ]; then
    echo "0:Doubao 前置筛选规则自动记 0 分"
    return
  fi

  # 其他模型根据测试结果决定
  local test_output=$(run_tests_compact)
  local passed failed errors
  passed=$(echo "$test_output" | grep -oP '\d+(?= passed)' | head -1 || true)
  failed=$(echo "$test_output" | grep -oP '\d+(?= failed)' | head -1 || true)
  errors=$(echo "$test_output" | grep -oP '\d+(?= errors?)' | head -1 || true)
  passed="${passed:-0}"
  failed="${failed:-0}"
  errors="${errors:-0}"

  if [ "$failed" -gt 0 ] || [ "$errors" -gt 0 ]; then
    echo "0:测试失败或代码不完整(${test_output:0:80})"
    return
  fi

  if [ "$passed" -gt "$TEST_BASELINE_PASSED" ]; then
    # 检查是否有额外测试覆盖
    local extra=$(echo "$test_output" | grep -oP '\d+(?= passed)' | head -1)
    if [ "$extra" -gt "$TEST_BASELINE_PASSED" ]; then
      echo "2:测试全部通过(${passed} passed)，代码完整且有额外测试覆盖"
    else
      echo "1:测试通过(${passed} passed)，但改动较基础无额外覆盖"
    fi
  elif [ "$passed" -eq "$TEST_BASELINE_PASSED" ]; then
    echo "1:测试通过(${passed} passed)，但没有新增通过测试覆盖"
  else
    echo "0:测试失败或代码不完整(${test_output:0:50})"
  fi
}

log_entry() {
  local pn="$1" model="$2" sid="$3" score="$4" reason="$5" patch="$6"
  reason="${reason//,/，}"
  if [ -f "$BASE_DIR/bitable_score_reason.py" ]; then
    reason=$(python3 "$BASE_DIR/bitable_score_reason.py" enrich \
      --prompt "$pn" --model "$model" --score "$score" --reason "$reason" --patch "$patch")
  fi
  if [ ! -f "$LOG_FILE" ]; then
    echo "prompt,model,session_id,score,score_reason,patch_file" > "$LOG_FILE"
  fi
  echo "$pn,$model,$sid,$score,$reason,$patch" >> "$LOG_FILE"
}

rollout_logged() {
  local pn="$1" model_num="$2" model_name model_short
  IFS=':' read -r model_name model_short <<< "$(rollout_model_spec "$pn" "$model_num")"
  [ -f "$LOG_FILE" ] && awk -F',' -v pn="$pn" -v model="$model_name" '
    NR > 1 && $1 == pn && $2 == model && $3 ~ /^[0-9a-f]{24}$/ { found = 1 }
    END { exit found ? 0 : 1 }
  ' "$LOG_FILE"
}

logged_rollout_total() {
  if [ ! -f "$LOG_FILE" ]; then
    echo 0
    return
  fi
  awk -F',' 'NR > 1 && $3 ~ /^[0-9a-f]{24}$/ { count++ } END { print count + 0 }' "$LOG_FILE"
}

print_missing_rollouts() {
  local pn model_num model_name model_short
  for pn in 1 2 3 4 5 6 7; do
    for model_num in 1 2 3 4 5; do
      if ! rollout_logged "$pn" "$model_num"; then
        IFS=':' read -r model_name model_short <<< "$(rollout_model_spec "$pn" "$model_num")"
        echo "  P${pn}/M${model_num}: $model_name"
      fi
    done
  done
}

submit_rollouts_to_bitable() {
  if [ "${TRAE_FULLAUTO_SUBMIT:-on}" != "on" ]; then
    echo "  → Bitable 提交: off"
    return 0
  fi
  if [ ! -f "$BASE_DIR/submit_fresh_task_pipeline.py" ]; then
    echo "ERROR: 找不到新任务表格提交脚本: $BASE_DIR/submit_fresh_task_pipeline.py" >&2
    return 1
  fi

  echo ""
  echo "🚚 创建新任务组、填表、上传附件并校验服务器状态"
  python3 "$BASE_DIR/submit_fresh_task_pipeline.py" --apply
}

normalize_score_reasons() {
  if [ ! -f "$BASE_DIR/bitable_score_reason.py" ]; then
    echo "ERROR: 找不到 score_reason 规范化脚本: $BASE_DIR/bitable_score_reason.py" >&2
    return 1
  fi
  echo ""
  echo "📝 规范化 trial_log.csv 的 score_reason（写入 prompt 任务点 + patch 证据）"
  python3 "$BASE_DIR/bitable_score_reason.py" normalize-log
}

review_rollouts_before_submit() {
  normalize_score_reasons || return 1
  if [ ! -f "$BASE_DIR/review_rollouts.py" ]; then
    echo "ERROR: 找不到填表前复检脚本: $BASE_DIR/review_rollouts.py" >&2
    return 1
  fi

  echo ""
  echo "🔎 填表前规则复检：对照本地 CSV、patch、Trae 日志检查 35 条 rollout"
  python3 "$BASE_DIR/review_rollouts.py"
}

verify_bitable_after_submit() {
  if [ "${TRAE_FULLAUTO_SUBMIT:-on}" != "on" ]; then
    echo "  → Bitable 提交后复检: off"
    return 0
  fi
  if [ ! -f "$BASE_DIR/verify_fresh_task_remote.py" ]; then
    echo "ERROR: 找不到新任务表格复检脚本: $BASE_DIR/verify_fresh_task_remote.py" >&2
    return 1
  fi

  echo ""
  echo "🔎 填表后完整复检：重新读取服务器记录，检查新任务组结构和附件"
  python3 "$BASE_DIR/verify_fresh_task_remote.py"
}

submit_fresh_task() {
  python3 "$BASE_DIR/submit_fresh_task_pipeline.py" --apply
}

archive_completed_trial() {
  python3 "$BASE_DIR/archive_completed_trial.py" --apply "$@"
}

# ====== 完整运行一轮 ======
run_one() {
  local pn="$1" model_num="$2"
  if [ "${TRAE_SKIP_RUNNER_LOCK_CHECK:-off}" != "on" ]; then
    acquire_runner_lock
  fi

  # 确定模型
  local model_name model_short
  IFS=':' read -r model_name model_short <<< "$(rollout_model_spec "$pn" "$model_num")"

  echo ""
  echo "╔══════════════════════════════════════════════╗"
  echo "║  Prompt $pn  →  $model_name"
  echo "╚══════════════════════════════════════════════╝"
  echo ""

  check_ppe_config
  check_target_repo
  check_cli_window_mode
  check_confirm_mode
  if ! switch_model_state "$model_short" "$model_name"; then
    echo "WARN: 自动写入 Trae 模型状态失败；请在 Trae 里手动确认模型为 $model_name"
  fi
  check_manual_model_after_auto_switch "$model_name"
  local expected_sid=""
  expected_sid=$(create_new_trae_task "$model_short")
  if [ -n "$expected_sid" ]; then
    echo "  → 本轮预期 Session ID: $expected_sid"
  fi
  echo ""
  local log_offsets_file
  log_offsets_file=$(mktemp)
  capture_log_offsets > "$log_offsets_file"
  local TRAE_EXPECTED_SESSION_ID="$expected_sid"
  local TRAE_LOG_OFFSETS_FILE="$log_offsets_file"
  local TRAE_EXPECTED_MODEL_SHORT="$model_short"

  # Step 1: 复制 prompt
  copy_prompt "$pn"
  echo ""

  # Step 2: 提交或提示用户操作
  show_prompt "$pn"
  echo "  🤖 模型: $model_name"
  echo "  📌 模式: $TRAE_CHAT_MODE"
  echo "  📁 工作区: $TRAE_MODEL_WORKSPACE"
  echo ""
  if [ "$TRAE_SUBMIT_MODE" = "bridge" ]; then
    check_privacy_mode
    local bridge_sid
    bridge_sid=$(submit_prompt_bridge "$pn" "$model_short")
    if [[ ! "$bridge_sid" =~ ^[0-9a-f]{24}$ ]]; then
      echo "ERROR: Bridge 提交未返回有效 Session ID: $bridge_sid"
      return 1
    fi
    if [ -n "$expected_sid" ] && [ "$expected_sid" != "$bridge_sid" ]; then
      echo "ERROR: Bridge 返回 Session ID 与预期不一致。"
      echo "       expected: $expected_sid"
      echo "       bridge:   $bridge_sid"
      return 1
    fi
    expected_sid="$bridge_sid"
    TRAE_EXPECTED_SESSION_ID="$expected_sid"
    echo "  → 已通过 Trae command bridge 提交 prompt"
    echo "  → 本轮预期 Session ID: $expected_sid"
    echo ""
    if [ "$TRAE_CONFIRM_MODE" = "auto" ]; then
      echo "  🤖 自动确认: 等待 bridge 返回的新 session 完成"
    else
      echo "  👆 请确认:"
      echo "     1. Trae 已进入 bridge 新建的本轮对话"
      echo "     2. 当前模型为 $model_name"
      echo "     3. AI 回复/改码完毕"
      echo "     4. 回来输入 '好了'"
    fi
  elif [ "$TRAE_SUBMIT_MODE" = "cli" ]; then
    check_privacy_mode
    if submit_prompt_cli "$pn" "$TRAE_CHAT_MODE" "$model_short"; then
      echo "  → 已通过 Trae CLI 提交 prompt"
    else
      echo "  → CLI 提交失败；prompt 已在剪贴板，请手动发送"
    fi
    echo ""
    if [ "$TRAE_CONFIRM_MODE" = "auto" ]; then
      echo "  🤖 自动确认: 等待 repo 状态稳定后继续"
      echo "  ⚠️  当前 Trae CLI 仍会打开 GUI；只有显式允许自动确认时才会进入这里"
    else
      echo "  👆 请确认:"
      echo "     1. Trae 已经新建本轮对话"
      echo "     2. 当前模型为 $model_name"
      echo "     3. AI 回复/改码完毕"
      echo "     4. 回来输入 '好了'"
    fi
  else
    echo "  👆 请操作:"
    echo "     1. Trae 打开 Docker 远程工作区 /app → 新对话 → 选 $model_name"
    echo "     2. Ctrl+V 粘贴 → 回车发送"
    echo "     3. AI 回复完毕后确认本轮 session 可见"
    echo "     4. 回来输入 '好了'"
  fi
  echo ""

  # Step 3: 等待完成。manual 等用户确认，auto 等 repo 状态稳定。
  wait_for_completion

  echo ""
  echo "  [处理中] 运行测试..."

  # Step 4: 决定分数
  local score_info=$(decide_score "$model_name" "$pn")
  local score="${score_info%%:*}"
  local reason="${score_info#*:}"
  echo "  → 分数: $score 分"
  echo "  → 理由: $reason"

  # Step 5: 生成 patch
  local patch_file=$(make_patch "$pn" "$model_short")
  echo "  → Patch: $patch_file"

  # Step 6: 提取 Session ID
  local sid
  if [ -n "$expected_sid" ]; then
    sid="$expected_sid"
  else
    sid=$(extract_sid "$log_offsets_file" || true)
  fi
  echo "  → Session ID: $sid"

  validate_rollout_outputs "$pn" "$sid" "$patch_file" "$model_short" "$log_offsets_file" "$expected_sid"
  rm -f "$log_offsets_file"

  # Step 7: 记录日志
  log_entry "$pn" "$model_name" "$sid" "$score" "$reason" "$patch_file"
  echo "  → 已记录到 CSV"

  # Step 8: 重置代码
  reset_repo

  # Step 9: 显示进度
  local total=$(tail -n +2 "$LOG_FILE" 2>/dev/null | wc -l)
  echo ""
  echo "  📊 总进度: $total / 35"
}

finalize_existing_session() {
  local pn="$1" model_num="$2" expected_sid="$3"
  if [ "${TRAE_SKIP_RUNNER_LOCK_CHECK:-off}" != "on" ]; then
    acquire_runner_lock
  fi
  if [[ ! "$expected_sid" =~ ^[0-9a-f]{24}$ ]]; then
    echo "ERROR: finalize 需要 24 位 hex Session ID"
    return 1
  fi

  local model_name model_short
  IFS=':' read -r model_name model_short <<< "$(rollout_model_spec "$pn" "$model_num")"

  echo ""
  echo "╔══════════════════════════════════════════════╗"
  echo "║  Finalize Prompt $pn  →  $model_name"
  echo "╚══════════════════════════════════════════════╝"
  echo "  → Session ID: $expected_sid"
  echo ""

  check_ppe_config
  local log_offsets_file
  log_offsets_file=$(mktemp)
  # For finalize we need historical evidence from the already-started session.
  : > "$log_offsets_file"
  local TRAE_EXPECTED_SESSION_ID="$expected_sid"
  local TRAE_LOG_OFFSETS_FILE="$log_offsets_file"

  wait_for_completion

  echo ""
  echo "  [处理中] 运行测试..."
  local score_info
  score_info=$(decide_score "$model_name" "$pn")
  local score="${score_info%%:*}"
  local reason="${score_info#*:}"
  echo "  → 分数: $score 分"
  echo "  → 理由: $reason"

  local patch_file
  patch_file=$(make_patch "$pn" "$model_short")
  echo "  → Patch: $patch_file"

  validate_rollout_outputs "$pn" "$expected_sid" "$patch_file" "$model_short" "$log_offsets_file" "$expected_sid"
  rm -f "$log_offsets_file"

  log_entry "$pn" "$model_name" "$expected_sid" "$score" "$reason" "$patch_file"
  echo "  → 已记录到 CSV"

  reset_repo

  local total
  total=$(tail -n +2 "$LOG_FILE" 2>/dev/null | wc -l)
  echo ""
  echo "  📊 总进度: $total / 35"
}

# ====== 批量模式 ======
# 用法: bash batch_runner.sh <prompt_number>
# 自动跑完该 Prompt 的 5 个模型

batch_run() {
  local pn="$1"
  acquire_runner_lock
  TRAE_SKIP_RUNNER_LOCK_CHECK=on
  export TRAE_SKIP_RUNNER_LOCK_CHECK
  echo ""
  echo "🚀 批量跑 Prompt $pn (5个模型)"
  echo "================================================"

  for m in 1 2 3 4 5; do
    run_one "$pn" "$m"
    echo ""
    echo "--- 下一个 ---"
  done

  echo "✅ Prompt $pn 全部完成！"
}

autorun_one() {
  if [ "${TRAE_SKIP_RUNNER_LOCK_CHECK:-off}" != "on" ]; then
    acquire_runner_lock
  fi
  TRAE_SKIP_RUNNER_LOCK_CHECK=on
  TRAE_SUBMIT_MODE=bridge
  TRAE_CONFIRM_MODE=auto
  TRAE_CLI_DOCKER_ALLOWED=on
  TRAE_AUTO_CONFIRM_ALLOWED=on
  TRAE_CHAT_WINDOW_FLAG=--reuse-window
  TRAE_ALLOW_REUSE_WINDOW=on
  TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT=on
  TRAE_REQUIRE_LOG_MODEL_MATCH=on
  TRAE_NEW_TASK_MODE=command
  TRAE_REQUIRE_EXPECTED_SESSION=on
  export TRAE_SKIP_RUNNER_LOCK_CHECK TRAE_SUBMIT_MODE TRAE_CONFIRM_MODE TRAE_CLI_DOCKER_ALLOWED TRAE_AUTO_CONFIRM_ALLOWED
  export TRAE_CHAT_WINDOW_FLAG TRAE_ALLOW_REUSE_WINDOW TRAE_ACTIVATE_WORKSPACE_BEFORE_CHAT TRAE_REQUIRE_LOG_MODEL_MATCH
  export TRAE_NEW_TASK_MODE TRAE_REQUIRE_EXPECTED_SESSION
  run_one "$1" "$2"
}

autobatch_run() {
  local pn="$1"
  acquire_runner_lock
  TRAE_SKIP_RUNNER_LOCK_CHECK=on
  export TRAE_SKIP_RUNNER_LOCK_CHECK
  echo ""
  echo "🚀 自动批量跑 Prompt $pn (5个模型)"
  echo "================================================"

  local m model_name model_short
  for m in 1 2 3 4 5; do
    if rollout_logged "$pn" "$m"; then
      IFS=':' read -r model_name model_short <<< "$(rollout_model_spec "$pn" "$m")"
      echo "  → 跳过已完成: P${pn}/M${m} $model_name"
      continue
    fi
    autorun_one "$pn" "$m"
    echo ""
    echo "--- 下一个 ---"
  done

  echo "✅ Prompt $pn 自动批量完成！"
}

fullauto_run() {
  acquire_runner_lock
  TRAE_SKIP_RUNNER_LOCK_CHECK=on
  export TRAE_SKIP_RUNNER_LOCK_CHECK

  echo ""
  echo "🚀 全自动模式：补齐所有 Prompt/模型 rollout，完成后提交 Bitable"
  echo "================================================"
  echo "当前进度: $(logged_rollout_total) / 35"
  echo "待处理:"
  print_missing_rollouts
  echo ""

  local pn model_num model_name model_short
  for pn in 1 2 3 4 5 6 7; do
    for model_num in 1 2 3 4 5; do
      if rollout_logged "$pn" "$model_num"; then
        IFS=':' read -r model_name model_short <<< "$(rollout_model_spec "$pn" "$model_num")"
        echo "  → 跳过已完成: P${pn}/M${model_num} $model_name"
        continue
      fi

      IFS=':' read -r model_name model_short <<< "$(rollout_model_spec "$pn" "$model_num")"
      echo ""
      echo "▶ 全自动执行: P${pn}/M${model_num} $model_name"
      autorun_one "$pn" "$model_num"
    done
  done

  local total
  total=$(logged_rollout_total)
  echo ""
  echo "📊 rollout 生成完成: $total / 35"
  if [ "$total" -ne 35 ]; then
    echo "ERROR: trial_log.csv 未达到 35 条有效 rollout，拒绝提交 Bitable。"
    echo "剩余:"
    print_missing_rollouts
    return 1
  fi

  review_rollouts_before_submit
  submit_rollouts_to_bitable
  verify_bitable_after_submit
  echo "✅ 全自动流程完成：35 个 rollout 已生成，填表前复检和填表后服务器复检均已通过。"
}

preflight_status() {
  echo "== PPE =="
  check_ppe_config
  echo ""
  echo "== 目标仓库 =="
  check_target_repo || true
  echo ""
  echo "== Trae 模型状态 =="
  list_model_state || true
  echo ""
  echo "== 正在运行的 batch_runner =="
  ps -eo pid=,stat=,etime=,args= | awk '/batch_runner\.sh (run|batch|autorun|autobatch|fullauto)/ { print }' || true
  echo ""
  echo "== 进度 =="
  total=$(tail -n +2 "$LOG_FILE" 2>/dev/null | wc -l)
  echo "总进度: $total / 35"
  local p count
  for p in 1 2 3 4 5 6 7; do
    count=$(tail -n +2 "$LOG_FILE" 2>/dev/null | awk -F',' -v p="$p" '$1==p' | wc -l)
    echo "  Prompt $p: $count/5"
  done
}

# ====== 主入口 ======
case "${1:-}" in
  run)    run_one "${2:-3}" "${3:-1}" ;;
  finalize) finalize_existing_session "${2:?prompt_num required}" "${3:?model_num required}" "${4:?session_id required}" ;;
  batch)  batch_run "${2:-3}" ;;
  autorun) autorun_one "${2:-3}" "${3:-1}" ;;
  autobatch) autobatch_run "${2:-3}" ;;
  fullauto) fullauto_run ;;
  copy)   copy_prompt "${2:-3}" ;;
  submit) submit_prompt_cli "${2:-3}" "${3:-$TRAE_CHAT_MODE}" ;;
  model-state) list_model_state ;;
  switch-model) switch_model_state "${2:-doubao}" "${3:-${2:-doubao}}" ;;
  target) check_target_repo ;;
  ppe) check_ppe_config ;;
  cont|continue) send_continue_cli "${2:-$TRAE_CONTINUE_TIMES}" "${3:-$TRAE_CONTINUE_TEXT}" ;;
  privacy) privacy_status ;;
  score)  decide_score "${2:-Doubao-Seed-2.0-Code}" "${3:-3}" ;;
  session-model) session_model_id "${2:?session_id required}" ;;
  session-model-log) session_model_id_from_logs "${2:?session_id required}" "${3:-}" ;;
  sid)    extract_sid ;;
  preflight) preflight_status ;;
  review) review_rollouts_before_submit ;;
  normalize-scores) normalize_score_reasons ;;
  verify-table) verify_bitable_after_submit ;;
  submit-fresh) submit_fresh_task ;;
  archive-completed) archive_completed_trial "${@:2}" ;;
  progress)
    total=$(tail -n +2 "$LOG_FILE" 2>/dev/null | wc -l)
    echo "总进度: $total / 35"
    for p in 1 2 3 4 5 6 7; do
      count=$(tail -n +2 "$LOG_FILE" 2>/dev/null | awk -F',' -v p="$p" '$1==p' | wc -l)
      echo "  Prompt $p: $count/5"
    done
    ;;
  reset)  reset_repo ;;
  test)   run_tests_compact ;;
  *)
    echo "用法: $0 <command> [args]"
    echo ""
    echo "单次运行:  $0 run <prompt_num> <model_num>"
    echo "批量运行:  $0 batch <prompt_num>"
    echo "自动单次:  $0 autorun <prompt_num> <model_num>"
    echo "自动批量:  $0 autobatch <prompt_num>"
    echo "全自动:    $0 fullauto"
    echo "复制文本:  $0 copy <prompt_num>"
    echo "CLI提交:   TRAE_SUBMIT_MODE=cli $0 run <prompt_num> <model_num>"
    echo "补记会话:  $0 finalize <prompt_num> <model_num> <session_id>"
    echo "超时续写:  TRAE_AUTO_CONTINUE_ON_TIMEOUT=on TRAE_AUTO_CONTINUE_MAX=3 TRAE_SUBMIT_MODE=cli TRAE_CONFIRM_MODE=auto $0 run <prompt_num> <model_num>"
    echo "单独提交:  $0 submit <prompt_num> [ask|edit|agent]"
    echo "模型状态:  $0 model-state"
    echo "切换模型:  $0 switch-model <doubao|gpt5|gemini|deepseek|minmax|glm|qwen>"
    echo "目标仓库:  $0 target"
    echo "PPE检查:   $0 ppe"
    echo "继续恢复:  $0 continue [times] [text]"
    echo "隐私模式:  $0 privacy"
    echo "自动评分:  $0 score <model> <prompt_num>"
    echo "会话模型:  $0 session-model <session_id>"
    echo "日志会话模型: $0 session-model-log <session_id> [offsets_file]"
    echo "提取SID:   $0 sid"
    echo "预检状态:  $0 preflight"
    echo "填表前复检: $0 review"
    echo "规范化评分理由: $0 normalize-scores"
    echo "填表后复检: $0 verify-table"
    echo "新表提交:  $0 submit-fresh"
    echo "归档完成任务并停容器: $0 archive-completed [--label name]"
    echo "查看进度:  $0 progress"
    echo "运行测试:  $0 test"
    echo "重置代码:  $0 reset"
    ;;
esac
