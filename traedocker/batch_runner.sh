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
TRAE_LOG_DIR="/home/jianglei/.config/Trae CN/logs"
DEFAULT_TRAE_CLI_BIN="trae-cn"
if [ -x "/usr/share/trae-cn/bin/trae-cn" ]; then
  DEFAULT_TRAE_CLI_BIN="/usr/share/trae-cn/bin/trae-cn"
fi
TRAE_CLI_BIN="${TRAE_CLI_BIN:-$DEFAULT_TRAE_CLI_BIN}"
TRAE_REPO_TARGET="${TRAE_REPO_TARGET:-docker}" # docker | local
TRAE_DOCKER_CONTAINER="${TRAE_DOCKER_CONTAINER:-python-grade-container}"
TRAE_DOCKER_REPO_DIR="${TRAE_DOCKER_REPO_DIR:-/app}"
TRAE_REMOTE_HOST="${TRAE_REMOTE_HOST:-odc-python-grade-container-55501f}"
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
TEST_BASELINE_PASSED="${TEST_BASELINE_PASSED:-61}"

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
    1) echo -n '请详细解释 `src/services/grade_service.py` 中 `GradeService.calculate_final` 与 `src/services/gpa_service.py` 中 `GPAService.recalculate` 的成绩计算链路：它们如何读取 `Assignment.weight`、`Assignment.max_score` 和 `Score.value` 来计算课程最终分数与 GPA？另外，请指出这两处重复计算逻辑可能带来的维护风险，以及 `CourseGrade._cached_final` 这个未使用缓存字段为什么容易造成误导。' ;;
    2) echo -n '目前 `src/services/grade_service.py` 的 `submit_score` 只检查 assignment 是否存在，没有严格校验成绩范围，也没有确认提交的 `course_grade_id` 与作业所属课程成绩一致。请完善成绩提交校验：1. 当 `value < 0` 或 `value > assignment.max_score` 时抛出 `ValueError("成绩超出允许范围")`。2. 当 `ScoreCreate.course_grade_id` 为空时默认使用 `assignment.course_grade_id`；当传入值与 `assignment.course_grade_id` 不一致时抛出 `ValueError("成绩与课程记录不匹配")`。3. 成功创建或更新成绩时写入 `graded_at=datetime.utcnow()`。4. 更新 `src/routers/grade_router.py`，把这些 `ValueError` 转成 400 响应。5. 在 `tests/test_grade.py` 中补充新增、更新、越界和课程不匹配的测试。' ;;
    3) echo -n '目前作业权重只有一个全局 `weight` 字段，`WeightCalculator` 也只能把所有作业直接归一化。我们需要支持按类别归一化权重：1. 在 `Assignment` 模型和 `AssignmentCreate/AssignmentResponse` Schema 中新增 `category` 字段，默认值为 `"homework"`。2. 修改 `WeightCalculator.normalize_weights` 和 `validate_weights`，让它们按 `category` 分组返回每组的权重总和、归一化结果和是否合法。3. 修改 `GradeService.calculate_final`、`GPAService.recalculate` 和 `TranscriptService.update`，在计算最终成绩时仍能正确使用归一化后的作业权重，且兼容没有类别的旧数据。4. 为分类权重、空分类、原有单分类行为补充测试。' ;;
    4) echo -n '目前 `src/services/curve_service.py` 的评分曲线会原地覆盖 `Score.value`，没有审计记录，也无法撤销。请增加可撤销的曲线调整能力：1. 新增一个持久化模型 `CurveAdjustment`，记录 `score_id`、`course_grade_id`、`curve_type`、`original_value`、`adjusted_value` 和 `created_at`。2. `apply_bell_curve` 和 `apply_flat_curve` 在修改分数时必须写入调整记录，并且不要为未实际变化的分数写记录。3. 新增 `CurveService.undo_last_curve(course_grade_id)`，按最近一批曲线调整恢复每个分数的 `original_value` 并删除或标记该批记录。4. 在 `src/routers/academic_router.py` 暴露撤销接口。5. 为曲线应用、审计记录和撤销恢复补充测试。' ;;
    5) echo -n '目前成绩单只保存 `records_json`，缺少可验证的官方凭证。请为成绩单增加验证码与校验接口：1. 在 `Transcript` 模型中新增 `verification_code` 和 `checksum` 字段。2. 更新 `TranscriptResponse` Schema。3. 修改 `TranscriptService.update`，根据 `student_id`、排序后的课程记录和生成时间生成稳定的 `checksum`，并生成不重复的 `verification_code`。4. 新增 `TranscriptService.verify(verification_code)`，返回校验结果、学生 ID 和 checksum。5. 在 `src/routers/academic_router.py` 增加查询验证码的接口。6. 补充测试，覆盖首次生成、重复更新、篡改 records_json 后校验失败、未知验证码。' ;;
    6) echo -n '目前 `GPAService.recalculate` 把每门课学分硬编码为 `3.0`，这会导致累计 GPA 不准确。请将课程成绩记录升级为支持真实学分：1. 在 `CourseGrade` 模型中新增 `credits` 字段，默认 `3.0`。2. 更新 `CourseGradeCreate/CourseGradeResponse` Schema 和 `CourseGradeFactory`。3. 修改 `GPAService.recalculate` 使用每个 `CourseGrade.credits`，并拒绝小于等于 0 的学分，抛出 `ValueError("课程学分必须为正数")`。4. 修改相关路由，将该错误转换为 400。5. 更新 GPA、累计 GPA、课程创建和工厂相关测试，确保不同学分会影响最终 GPA。' ;;
    7) echo -n '目前 `ReportService.student_ranking` 只是按学生平均分排序并使用顺序名次，无法处理同分并列，也没有百分位信息。请增强排名报表：1. 使用 `GradeService.calculate_final` 等价的加权最终分，而不是简单平均分。2. 同分学生使用并列名次，下一名采用竞赛排名规则（例如 1, 1, 3）。3. 每条记录新增 `percentile` 字段，按班级人数和名次计算，第一名为 100.0。4. 支持只返回某个 semester 的排名。5. 更新 `src/routers/academic_router.py` 暴露排名接口，并在 `tests/test_extras.py` 或新增测试中覆盖加权计算、并列名次、percentile 和 semester 过滤。' ;;
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
  if echo -n "$text" | xclip -selection clipboard; then
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
    1) echo "  背景: 成绩最终分与 GPA 计算链路"
       echo "  需求: 解释 GradeService/GPAService 的权重计算和重复逻辑风险"
       echo "  关键: 纯解释题，通常用 ask 模式，无需代码 diff" ;;
    2) echo "  背景: 成绩提交缺少范围和课程一致性校验"
       echo "  需求: submit_score 校验 + graded_at + 路由 400 + 测试"
       echo "  关键: Service/Router/测试多点联动" ;;
    3) echo "  背景: 作业权重不支持类别"
       echo "  需求: Assignment.category + 分类归一化 + 计算链路兼容"
       echo "  关键: 模型/Schema/Service/GPA/Transcript/测试级联修改" ;;
    4) echo "  背景: 曲线调整原地覆盖且不可撤销"
       echo "  需求: CurveAdjustment 审计模型 + 撤销接口"
       echo "  关键: 持久化记录、批次恢复、路由和测试" ;;
    5) echo "  背景: 成绩单缺少官方验证码"
       echo "  需求: verification_code/checksum + verify 接口"
       echo "  关键: 稳定校验、重复更新、篡改检测" ;;
    6) echo "  背景: GPA 学分硬编码为 3.0"
       echo "  需求: CourseGrade.credits + 真实学分计算 + 非法学分校验"
       echo "  关键: 模型/Schema/工厂/GPA/路由/测试全链路" ;;
    7) echo "  背景: 学生排名只用简单平均且无并列规则"
       echo "  需求: 加权最终分 + 竞赛排名 + percentile + semester 过滤"
       echo "  关键: 计算复用、并列名次、报表接口和测试" ;;
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
            if model:
                models.append(model)

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

review_rollouts_before_submit() {
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

  local m
  for m in 1 2 3 4 5; do
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
    echo "填表后复检: $0 verify-table"
    echo "新表提交:  $0 submit-fresh"
    echo "归档完成任务并停容器: $0 archive-completed [--label name]"
    echo "查看进度:  $0 progress"
    echo "运行测试:  $0 test"
    echo "重置代码:  $0 reset"
    ;;
esac
