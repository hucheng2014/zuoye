# Bitable 填表沉淀清单

这份文档记录 python-payment / Trae Docker 任务填表时的**硬性流程**和**历史踩坑**，避免重复犯错。

## 标准提交流程

```bash
# 1. 跑完 35 条 rollout
bash batch_runner.sh fullauto

# 2. 填表前：规范化 score_reason + 本地规则复检
bash batch_runner.sh review

# 3. 创建新任务组、上传附件、Docker 构建、远程校验、修复评分字段
bash batch_runner.sh submit-fresh
# 等价于：
python3 submit_fresh_task_pipeline.py --apply
```

**禁止**用 `submit_missing_rollouts.py` 往旧表补行；**禁止**覆盖已有任务组。

## 必须使用的脚本

| 脚本 | 用途 |
|------|------|
| `bitable_score_reason.py` | 生成/规范化 `score_reason`，远程修复 `score_reason` + `score_check` |
| `submit_fresh_task_pipeline.py` | 唯一推荐的新表提交流水线 |
| `submit_new_task_group.py` | 创建新任务组（ADD RECORD） |
| `submit_new_task_attachments.py` | 上传 patch / repo / Dockerfile / 截图 |
| `review_rollouts.py` | 填表前本地规则复检 |
| `verify_fresh_task_remote.py` | 填表后远程结构复检 |

## 历史错误与固定方案

### 1. score_reason 写空泛模板

**错误示例：**

- `测试全部通过(1006 passed)，代码完整且有额外测试覆盖`
- `Doubao 前置筛选规则自动记 0 分`
- `解释题无法通过 pytest 自动评测；默认记 1 分…`

**后果：** 飞书 AI 质检把 `score_check` 标成「不合理」，群聊会被要求返工。

**固定方案：**

- 每条 rollout 的 `score_reason` 必须包含：
  1. prompt 核心任务点（从 `get_prompt()` 提取）
  2. patch 改动文件
  3. pytest 结论
  4. 0/1/2 分依据
- 写入时机：
  - rollout 结束时：`batch_runner.sh` → `log_entry()` 自动调用 `bitable_score_reason.py enrich`
  - 填表前：`bash batch_runner.sh review` 会先跑 `normalize-log`
  - 填表后：`submit_fresh_task_pipeline.py` 自动跑 `repair-remote --apply`

手动修复：

```bash
python3 bitable_score_reason.py normalize-log
python3 bitable_score_reason.py repair-remote --plan latest --apply
```

### 2. 只改 score_reason，不改 score_check

**错误：** 远程 `score_check` 仍引用旧理由，继续显示「不合理」。

**固定方案：** `repair-remote` 同时写入：

- `score_reason`：结构化评分理由
- `score_check`：由 `score_quality_text()` 生成，与理由一致

### 3. 覆盖旧任务组

**错误：** 往 B00001573 / B00008611 / B00010768 等旧组写数据。

**固定方案：**

- 只走 `submit_fresh_task_pipeline.py` 创建**新 root**
- 所有写脚本内置 `PROTECTED_ROOT_RECORDS` 拦截
- 远程修复只允许 plan 文件里的 rollout record id

### 4. 首次 create 后子行 lazy-load 失败

**现象：** 只 persisted root，prompt/rollout 后验失败。

**固定方案：**

- 看 `new_task_backups/new_task_group_plan_*.json`
- 必要时用 plan 里的 id 补写子行，再继续 attachments / docker pipeline

### 5. 其他 batch_runner 已修问题

- Trae 日志模型名大小写不一致 → 脚本内 case-insensitive guard
- `xclip` 持有 `.batch_runner.lock` → 已 `9>&-` 释放
- autobatch 重复跑已完成 rollout → 读 `trial_log.csv` 跳过
- 非 Doubao 跑法 → `TRAE_AUTO_MODE_GUARD=off`

## 填表前自检（review 会检查）

- `trial_log.csv` 恰好 35 行，7 prompt × 5 model
- session_id 为 24 位 hex，且不重复
- P2–P7 的 Doubao 必须为 0 分
- 非解释题不能 5 个模型全是 2 分
- 代码题 patch 非空
- `score_reason` 不是 auto template

## 填表后自检

- 新组结构 = 1 root + 7 prompt + 35 rollout = 43 行
- root 有 Dockerfile / repo.zip / build screenshot
- 每条 rollout 有 `git_diff` 附件
- `verify_fresh_task_remote.py` errors=0
- `repair-remote` 后 35/35 `score_check` 为「合理」

## 受保护旧表（勿动）

| 任务 ID | Root Record ID |
|---------|----------------|
| B00001573 | `recvltHcbs9Y6q` |
| B00008611 | `recvlMqEuYIzqL` |
| B00010768 | `recvlQJ9JaXxg3` |

## 浏览器要求

填表/修复脚本通过 CDP 连接 `work-b` / `traedocker` 浏览器（`127.0.0.1:9235`），Bitable 页面需已登录打开。

```bash
/Users/xaa/zuoye/tools/agent-browser.sh traedocker get url
```
