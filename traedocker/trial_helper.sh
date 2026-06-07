#!/usr/bin/env bash
# =========================================================================
#  Trae 试标助手 v2 — 剪贴板模式
#
#  工作方式：
#    1. 我通过 xclip 把 prompt 复制到剪贴板
#    2. 你切到 Trae: Ctrl+V 粘贴 → 选模型 → 点发送
#    3. AI 回复后，把 Session ID 和分数告诉我
#    4. 我自动生成 .patch、git reset、记录日志
#
#  执行顺序：
#    Rollout 1: Doubao-Seed-2.0-Code (0分验证)
#    Rollout 2: GPT-5.4
#    Rollout 3: Gemini 3.1 pro
#    Rollout 4: DeepSeek-v4
#    Rollout 5: MinMax/GLM/Qwen 轮换
# =========================================================================
set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$BASE_DIR/repo"
LOG_FILE="$BASE_DIR/trial_log.csv"

# ---------- 7 个 Prompt ----------
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

# ---------- 模型顺序 ----------
# 前 4 个固定
ROLLOUT1="Doubao-Seed-2.0-Code:doubao"
ROLLOUT2="GPT-5.4:gpt5"
ROLLOUT3="Gemini 3.1 pro:gemini"
ROLLOUT4="DeepSeek-v4:deepseek"
# 第 5 个按 Prompt 轮换（索引 = (PN-1) % 3）
ROLLOUT5_0="MinMax-M2.7:minmax"   # Prompt 1, 4, 7
ROLLOUT5_1="GLM-5.1:glm"          # Prompt 2, 5
ROLLOUT5_2="Qwen3.6-Plus:qwen"    # Prompt 3, 6

# ---------- 颜色 ----------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
err()   { echo -e "${RED}[ERR]${NC} $1"; }
hr()    { echo -e "${YELLOW}────────────────────────────────────────────────────${NC}"; }

# ---------- 复制到剪贴板 ----------
copy_to_clipboard() {
  echo -n "$1" | xclip -selection clipboard
  if [ $? -eq 0 ]; then
    ok "已复制到剪贴板！在 Trae 里 Ctrl+V 粘贴即可"
  else
    warn "复制失败，请手动选中下面文字复制"
  fi
}

# ---------- 解析模型变量 ----------
parse_model() {
  local choice="$1"
  case "$choice" in
    1) IFS=':' read -r MODEL_NAME MODEL_SHORT <<< "$ROLLOUT1" ;;
    2) IFS=':' read -r MODEL_NAME MODEL_SHORT <<< "$ROLLOUT2" ;;
    3) IFS=':' read -r MODEL_NAME MODEL_SHORT <<< "$ROLLOUT3" ;;
    4) IFS=':' read -r MODEL_NAME MODEL_SHORT <<< "$ROLLOUT4" ;;
    5)
      idx=$(( (PN - 1) % 3 ))
      var="ROLLOUT5_$idx"
      IFS=':' read -r MODEL_NAME MODEL_SHORT <<< "${!var}"
      ;;
  esac
}

# =========================================================================
# 主流程
# =========================================================================
clear
echo ""
echo -e "${GREEN}"
echo "  ╔══════════════════════════════════════╗"
echo "  ║   Trae 试标助手 v2                    ║"
echo "  ║   35 次评估 · 剪贴板模式              ║"
echo "  ╚══════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "  执行顺序:"
echo "    Rollout 1: Doubao-Seed-2.0-Code (0分验证)"
echo "    Rollout 2: GPT-5.4"
echo "    Rollout 3: Gemini 3.1 pro"
echo "    Rollout 4: DeepSeek-v4"
echo "    Rollout 5: MinMax / GLM / Qwen 轮换"
echo ""
info "流程：我复制 prompt → 你 Ctrl+V 到 Trae → AI 回复 → 告诉我 Session ID"
echo ""

# 检查 git 状态
cd "$REPO_DIR"
if ! git rev-parse --git-dir > /dev/null 2>&1; then
  err "repo/ 没有 git 仓库"
  exit 1
fi
if [ -n "$(git status --porcelain)" ]; then
  warn "repo/ 有未提交的更改，先重置..."
  git reset --hard HEAD 2>/dev/null
  git clean -fd 2>/dev/null
fi
ok "git 仓库就绪"
echo ""

# 主循环
while true; do
  # ---- 选 Prompt ----
  hr
  echo "  选择题目:"
  echo "    1) Prompt 1 - 代码解释（纯解释，不需改代码）"
  echo "    2) Prompt 2 - 计时器持久化"
  echo "    3) Prompt 3 - 累计工时上限校验"
  echo "    4) Prompt 4 - Excel 汇总行"
  echo "    5) Prompt 5 - 审批流权限"
  echo "    6) Prompt 6 - 项目生命周期"
  echo "    7) Prompt 7 - 加班权重统计"
  echo "    s) 查看进度"
  echo "    q) 退出"
  echo ""
  read -p "  选择 [1-7/s/q]: " p_choice
  [[ "$p_choice" == "q" ]] && break

  if [[ "$p_choice" == "s" ]]; then
    hr
    if [ -f "$LOG_FILE" ]; then
      TOTAL=$(tail -n +2 "$LOG_FILE" 2>/dev/null | wc -l)
      echo "  总进度: $TOTAL / 35"
      for p in 1 2 3 4 5 6 7; do
        COUNT=$(tail -n +2 "$LOG_FILE" 2>/dev/null | awk -F',' -v p="$p" '$1==p' | wc -l)
        echo "    Prompt $p: $COUNT/5"
      done
    else
      echo "  尚未开始"
    fi
    echo ""
    continue
  fi

  case "$p_choice" in
    1) PN=1; PT="$PROMPT1" ;;
    2) PN=2; PT="$PROMPT2" ;;
    3) PN=3; PT="$PROMPT3" ;;
    4) PN=4; PT="$PROMPT4" ;;
    5) PN=5; PT="$PROMPT5" ;;
    6) PN=6; PT="$PROMPT6" ;;
    7) PN=7; PT="$PROMPT7" ;;
    *) warn "无效选择"; continue ;;
  esac

  # ---- 内循环：同一个 Prompt 跑多个模型 ----
  while true; do
    # 确定轮换模型
    idx=$(( (PN - 1) % 3 ))
    var="ROLLOUT5_$idx"
    IFS=':' read -r r5_name r5_short <<< "${!var}"

    hr
    echo "  Prompt $PN — 选择要跑的模型:"
    echo "    1) Doubao-Seed-2.0-Code    (rollout 1, 自动0分)"
    echo "    2) GPT-5.4                 (rollout 2)"
    echo "    3) Gemini 3.1 pro          (rollout 3)"
    echo "    4) DeepSeek-v4             (rollout 4)"
    echo "    5) $r5_name          (rollout 5)"
    echo "    b) 返回选题目"
    echo "    q) 退出"
    echo ""
    read -p "  选择 [1-5/b/q]: " m_choice

    if [[ "$m_choice" == "q" ]]; then echo ""; exit 0; fi
    if [[ "$m_choice" == "b" ]]; then break; fi
    if [[ "$m_choice" -lt 1 || "$m_choice" -gt 5 ]]; then
      warn "无效选择"; continue
    fi

    # 解析模型
    parse_model "$m_choice"

    hr
    echo ""
    echo "  📋 Prompt $PN  →  $MODEL_NAME"
    echo ""

    # ---- 复制 Prompt 到剪贴板 ----
    copy_to_clipboard "$PT"
    echo ""

    # ---- 提示 ----
    echo "  操作提示："
    if [ "$PN" == "1" ]; then
      echo "  • 这是解释题，在 Trae 聊天框选「Ask」模式发送"
    else
      echo "  • 在 Trae 聊天框选「Edit」或「Agent」模式发送"
    fi
    echo "  • 发送前确认模型切换为「$MODEL_NAME」"
    echo "  • AI 回复后，点聊天窗口右上角「复制 Session ID」"
    echo ""

    # ---- 等用户操作 Trae ----
    read -p "  ⏳ 输入 Session ID: " SESSION_ID
    while [ -z "$SESSION_ID" ]; do
      warn "Session ID 不能为空！"
      read -p "  请输入 Session ID: " SESSION_ID
    done

    # ---- 打分 ----
    if [[ "$MODEL_NAME" == Doubao* ]]; then
      SCORE=0
      SCORE_REASON="Doubao 前置筛选规则自动记 0 分"
      info "Doubao 自动记 0 分"
    else
      echo ""
      read -p "  打分 [4/5] (默认 4): " si
      SCORE="${si:-4}"
      read -p "  评分理由 (回车默认): " sr
      SCORE_REASON="${sr:-代码实现完整，通过测试}"
    fi
    echo ""

    # ---- 生成 Patch ----
    PATCH_NAME="prompt${PN}_${MODEL_SHORT}.patch"
    echo "  [1/3] 生成 $PATCH_NAME ..."
    cd "$REPO_DIR"
    git diff > "$BASE_DIR/$PATCH_NAME" 2>/dev/null
    if [ -s "$BASE_DIR/$PATCH_NAME" ]; then
      ok "  Patch 已保存 ($(wc -c < "$BASE_DIR/$PATCH_NAME") bytes)"
    else
      echo "# Empty - no code changes for $MODEL_NAME on Prompt $PN" > "$BASE_DIR/$PATCH_NAME"
      warn "  Patch 为空（AI 可能没改代码，也可能是解释题无变更）"
    fi

    # ---- git reset ----
    echo "  [2/3] 重置代码到初始状态..."
    git reset --hard HEAD 2>/dev/null
    git clean -fd 2>/dev/null
    ok "  代码已重置"

    # ---- 记录日志 ----
    echo "  [3/3] 记录日志..."
    if [ ! -f "$LOG_FILE" ]; then
      echo "prompt,model,session_id,score,score_reason,patch_file" > "$LOG_FILE"
    fi
    echo "$PN,$MODEL_NAME,$SESSION_ID,$SCORE,$SCORE_REASON,$PATCH_NAME" >> "$LOG_FILE"

    # ---- 结果 ----
    hr
    echo "  ✅ Prompt $PN × $MODEL_NAME 完成！"
    echo "  Session: $SESSION_ID  |  分数: $SCORE"
    TOTAL=$(tail -n +2 "$LOG_FILE" 2>/dev/null | wc -l)
    echo "  总进度: $TOTAL / 35"
    hr

    # ---- 继续？ ----
    echo ""
    read -p "  继续 Prompt $PN 的下一个模型？(Y/n): " next_m
    if [[ "$next_m" == "n" || "$next_m" == "N" ]]; then
      break
    fi
    echo ""
  done
done

echo ""
echo "═══════════════════════════════════════"
echo "  全部完成！共 $(tail -n +2 "$LOG_FILE" 2>/dev/null | wc -l) 条记录"
echo "  日志: $LOG_FILE"
echo "  Patch 文件: $BASE_DIR/prompt*.patch"
echo "═══════════════════════════════════════"
