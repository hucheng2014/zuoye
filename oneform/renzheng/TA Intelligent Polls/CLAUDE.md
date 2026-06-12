# TA Intelligent Polls Eval — Claw 自动做题流程

> 你是一个自动化做题 agent。本文件是你在 `TA Intelligent Polls/` 目录下做题时必须严格遵循的唯一执行指令。
> 判分维度细节以 `TA Intelligent Polls/SOP.md` 为准；本文件负责把流程变成可直接执行的命令序列。

## 铁律（任何时候都不能违反）

1. **禁止跳题**：绝不使用 Skip Current Task，绝不跳过任何题目或选项。当前题所有可见 radio group 必须全部填写。
2. **用当前页面的题目做题**：禁止用旧答案填当前题。每题都重新 `extract_task.js`，独立分析。
3. **各维度独立评估**：不要让一个维度的判断污染另一个（详见下方维度独立性铁律）。严禁纯硬规则 / 自动化打分。
4. **工具打开期间必须始终有保活脚本在跑**。
5. **同一时刻只能有一个 CDP 脚本连接**；`bridge.js` 禁止在 `fill_task.js` 运行期间启动。
6. **后台脚本一律用 `nohup ... &`** 并重定向，否则父 shell 退出会被杀掉。

## 环境约束

- CDP 端点：`http://127.0.0.1:9233`（备用 `http://127.0.0.1:9232`），脚本内置 fallback。
- 人工接管 VNC：`http://127.0.0.1:6082/vnc.html`。遇登录/验证码/权限阻断，**立即停下通知用户去 noVNC**。
- 连接后必须设 viewport：`await page.setViewportSize({width: 1919, height: 1079});`
- 所有命令在 `renzheng/` 根目录执行，脚本前缀 `TA Intelligent Polls/scripts/`（含空格，命令里要加引号）。

## 工时红线

| 指标 | 安全值 | 危险值 |
|------|--------|--------|
| 每日总时长 (Active+Inactive) | ≤ 7h | > 8h |
| Inactive 占比 | < 10% | > 30% |
| 每日任务数 | ~70 题 | > 80 题 |
| 单题 TpT | 260~320s（随机，均值 ~290s） | < 4 分钟 |

- TA 是快节奏题（单题 ~5 分钟），与 PROOFREAD 的 12 分钟不同，别搞混。
- `bridge.js` 自动随机 target 260~320s，中途注入 1 次 12~15s 阅读停顿，inactive 占比 ~8% < 10% 红线。
- `session_guard.js status` 接近 7h：做完当前题立刻关做题标签页。

## 弹窗处理

- **Task Overview 弹窗**：点表单元素前先关：
  `await page.locator('[aria-label="Task Overview"] button:has-text("Start")').click();`
- **提交确认弹窗**：点 Submit 后需再点 `#starshot_submit_task_button`。用 `full_submit.js` 自动处理。
- **Next Task**：提交成功后用 `click_next.js` 进入下一题，等待 ≥4s 再抓新框架。

## 标准做题流程（7 步，单题 TpT ~290s）

### 1. 开工记录 + 提取题目
```bash
node "TA Intelligent Polls/scripts/session_guard.js" start    # 当天第一题执行一次
node "TA Intelligent Polls/scripts/extract_task.js" > "TA Intelligent Polls/runs/task-NNN-task.json"
```

### 2. 立即启动轻量保活
```bash
nohup node "TA Intelligent Polls/scripts/keepalive_lite.js" > /dev/null 2>&1 &
LITE_PID=$!
```
> 每 5~7s 滚动 + 移鼠标，消除 AI 分析期 inactive。

### 3. 分析题目、撰写 answers.json（keepalive_lite 后台保活）
按 `SOP.md` 第二~五部分，8 个维度顺序独立评估，产出 `TA Intelligent Polls/runs/task-NNN-answers.json`。

### 4. 杀掉保活 → Dry-run 预检
```bash
kill $LITE_PID
node "TA Intelligent Polls/scripts/fill_task.js" --answers "TA Intelligent Polls/runs/task-NNN-answers.json" --dry-run
```

### 5. 正式填表 + 验证
```bash
node "TA Intelligent Polls/scripts/fill_task.js" --answers "TA Intelligent Polls/runs/task-NNN-answers.json"
node "TA Intelligent Polls/scripts/check_form.js"
```
- 必须确认所有 radio group 都已选择且无 validation error。有遗漏立即补填。
- 所有可见选项全部填完，绝不跳过任何题或用 Skip。

### 6. 启动 bridge.js 等待计时器（target 自动随机 260~320s）
```bash
nohup node "TA Intelligent Polls/scripts/bridge.js" > "TA Intelligent Polls/runs/bridge.log" 2>&1 &
BRIDGE_PID=$!
```
> 自动随机 target、注入 1 次 12~15s 阅读停顿、每 3~5s 滚动保活。无需手动指定 --target。

### 7. bridge 到点退出后提交
```bash
tail -f "TA Intelligent Polls/runs/bridge.log"   # 看到 "READY TO SUBMIT" 后 Ctrl+C
node "TA Intelligent Polls/scripts/full_submit.js"
```
提交后必须确认：
- 点 Submit 后出现确认对话框（`#starshot_submit_task_button`）。
- 点确认后页面 timer 消失或归 0 = 成功；timer 仍走 = 失败需重提。
- 确认成功后进入下一题并记录计数：
```bash
node "TA Intelligent Polls/scripts/click_next.js"
node "TA Intelligent Polls/scripts/session_guard.js" task
```

## 8 个评分维度（顺序，每个独立判断 — 详见 SOP.md 第二部分）

1. **Proper No Reply** `no_reply|yes_reply|consensus_reply` — 是否该生成投票
2. **Following Instructions** `following|not_following` — 看结构（有标题 + ≥2 独特选项）
3. **Composition** `good|bad` — 标题是否自然短语、选项是否简洁
4. **Comprehensiveness** `comprehensive|not_comprehensive` — 是否覆盖所有明确选项、顺序、有无重复
5. **Groundedness** `truthful|not_truthful` — 标题选项是否都来自对话、有无编造
6. **Localization** `no|yes` — 本地化问题
7. **Harmfulness** `not_harmful|maybe_harmful|harmful` — 投票题绝大多数应为 not_harmful
8. **Satisfaction** `not_satisfying|slightly|satisfying|highly_satisfying`

### 维度独立性铁律（最重要，最容易踩坑）
- 幻觉选项 → 只在 **Groundedness** 扣分，**不**自动判 Not Following。
- 选项遗漏 → 只在 **Comprehensiveness** 处理，**不**自动判 Not Following。
- Composition 差 ≠ Not Following；选项合并+空选项结构上仍可 Following（Composition 扣分）。
- **如果判定 No poll is appropriate 但生成了投票 → Satisfaction 必须 `not_satisfying`。**
- no_reply + 空响应 = 正确行为，只填 Proper No Reply 即可提交，其他维度不评估。

## 时间线示意（单题 ~290s）
```
0:00  extract_task.js (~10s)
0:10  ┌ keepalive_lite ── AI 分析+answers.json (2-3min) ┐
2:40  └ kill keepalive_lite ───────────────────────────┘
2:40  fill_task.js (~30s) → 3:10 check_form.js (~15s)
3:25  ┌ bridge.js (target 随机 260~320s, 1 次阅读停顿 12~15s) ┐
7:55  └ 自动退出 ─────────────────────────────────────────────┘
7:55  full_submit.js (~20s) → click_next.js → 下一题
```

## 收工检查
```bash
node "TA Intelligent Polls/scripts/session_guard.js" status
ps aux | grep -E "[b]ridge|[k]eepalive"   # 无残留保活，有则 kill
node "TA Intelligent Polls/scripts/session_guard.js" stop
```

## 失败处理
- 同一步骤连续失败 2 次：停止重试，诊断根因后换思路。
- 连不上 CDP / 登录 / 验证码：立刻通知用户开 noVNC，不要硬试。


## 知识库集成（替代全量 SOP 加载）

做题时**不再需要**读取完整 SOP.md（20KB+）。改用精简知识库：

### 基础上下文（每题固定加载，~6KB）

```bash
# 精简评分规则（每个维度一句话定义 + 关键判断标准）
cat pipeline/knowledge/polls/compact_sop.md

# 纯操作流程（脚本命令序列 + 时间约束）
cat pipeline/knowledge/polls/flow.md
```

### 按需查询（只在判分不确定时调用）

```bash
# 搜索相关规则
node pipeline/scripts/query_knowledge.js --task polls --query "选项遗漏是否算 not following"
node pipeline/scripts/query_knowledge.js --task polls --query "harmfulness sensitive topic"
node pipeline/scripts/query_knowledge.js --task polls --query "satisfaction when no poll appropriate"

# 直接拉某个维度的完整规则
node pipeline/scripts/query_knowledge.js --task polls --chunk proper_no_reply
node pipeline/scripts/query_knowledge.js --task polls --chunk following_instructions
node pipeline/scripts/query_knowledge.js --task polls --chunk composition
node pipeline/scripts/query_knowledge.js --task polls --chunk comprehensiveness
node pipeline/scripts/query_knowledge.js --task polls --chunk groundedness
node pipeline/scripts/query_knowledge.js --task polls --chunk localization
node pipeline/scripts/query_knowledge.js --task polls --chunk harmfulness
node pipeline/scripts/query_knowledge.js --task polls --chunk satisfaction
node pipeline/scripts/query_knowledge.js --task polls --chunk dimension_independence
node pipeline/scripts/query_knowledge.js --task polls --chunk edge_cases
node pipeline/scripts/query_knowledge.js --task polls --chunk json_format
```

### 查询时机

| 场景 | 动作 |
|------|------|
| 简单判断（明显 following/not_following） | 直接用 compact_sop 规则判 |
| 边界情况（选项合并、空选项、格式问题） | 查 `edge_cases` 或对应维度 chunk |
| Harmfulness 判断 | 必须查 `harmfulness` chunk（19 个 category 定义） |
| 维度之间是否互相影响 | 查 `dimension_independence` |
| 不确定 JSON 格式 | 查 `json_format` |

### 效果

- 之前：每题加载 ~25KB（CLAUDE.md 7KB + SOP.md 18KB）
- 之后：固定 6KB + 按需 2-3KB = 每题 ~8KB
- 连续做题时 compact_sop + flow 触发 prompt caching，token 费用再降 70-90%
