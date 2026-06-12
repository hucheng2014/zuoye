# Trae Docker 试标 — Agent 开场话术与执行规范

> 本文档是**测试开始前**用户与 Agent 对齐的固定话术。用户可直接复制「开场话术」发给 Agent；Agent 必须按后文流程执行，不得自行发明填表/评分/提交方式。

工作目录：`/Users/xaa/zuoye/traedocker`

---

## 开场话术（用户复制给 Agent）

把下面 `{…}` 换成本次实际情况后，整段发给 Agent：

```
请在 traedocker 工作区继续 Trae CN 试标任务。

【任务】
- 代码库：{studentsystem / 当前 repo 名称}
- 目标：完成 7 条 prompt × 5 模型 = 35 条 rollout，填表提交新任务组，最后我在群里请求质检
- 进度：{从 0/35 开始 / 从 trial_log.csv 已有条数继续，勿重复跑已完成 rollout}

【硬性边界】
1. 只创建新 Bitable 任务组，禁止修改或删除以下旧表：
   - B00001573 (recvltHcbs9Y6q)
   - B00008611 (recvlMqEuYIzqL)
   - B00010768 (recvlQJ9JaXxg3)
2. 禁止用 submit_missing_rollouts.py 往旧表补行
3. 禁止从零重写填表脚本；必须用 batch_runner.sh + submit_fresh_task_pipeline.py
4. 登录/验证码/Trae 掉线 → 停下来让我用 noVNC 处理，禁止静默假装成功
5. 没做完 35 条、没通过 review、score 质检未自查前，不要催群质检

【执行顺序】
1. preflight → fullauto（或按进度续跑）→ review → submit-fresh
2. 填表后确认 verify 通过、35/35 score_check 合理
3. 给我一段可直接粘贴到「BBS代码项目-小组3群」的验收消息

开始前先读：PROMPT.md、标注规则_完整版.md、docs/bitable-submission-checklist.md
```

---

## 项目简介

通过 `batch_runner.sh` 在 Trae CN + Docker 容器内完成 35 条 rollout，记录 `trial_log.csv` 与 patch，再用脚本向飞书 Bitable **新建**任务组并上传附件。浏览器仅用于检查；**所有可重复写表动作必须走 Python 脚本**。

---

## 一、环境与前置（开跑前 Agent 必须确认）

| 项 | 要求 |
|----|------|
| Trae PPE | `bash batch_runner.sh ppe` 通过 |
| 隐私模式 | 必须关闭；`bash batch_runner.sh privacy` 无告警 |
| 目标仓库 | Docker 容器 `studentsystem-container`，工作区 `/app` |
| Bitable 浏览器 | `work-b` / `traedocker`，CDP `127.0.0.1:9235`，Bitable 页已登录打开 |
| 进度文件 | `trial_log.csv`（35 行 = 完成）；`prompt{N}_{model}.patch` |
| 产物 | 根目录 `Dockerfile`、`repo.zip`、构建截图 |

常用检查：

```bash
bash batch_runner.sh preflight
bash batch_runner.sh progress
bash batch_runner.sh ppe
```

---

## 二、Rollout 执行（35 条）

### 模型与评分（不可改）

- **Doubao-Seed-2.0-Code**：Prompt 2–7 固定 **0 分**（前置筛选基线），不得当作满分实现
- **Prompt 1**：解释题，无法 pytest，默认 **1 分**
- **其他模型**：按 pytest 结果 0/1/2；非解释题不能 5 个模型全是 2 分
- **每条 rollout 必须单独开 session**，禁止同一窗口多 prompt 混聊

### 推荐命令

```bash
# 一次性跑完剩余 rollout（会跳过 trial_log.csv 已有记录）
TRAE_SUBMIT_MODE=bridge TRAE_CONFIRM_MODE=auto TRAE_AUTO_MODE_GUARD=off \
  bash batch_runner.sh fullauto

# 单条：prompt 3，模型槽 2（GPT-5.4）
TRAE_SUBMIT_MODE=bridge TRAE_CONFIRM_MODE=auto TRAE_AUTO_MODE_GUARD=off \
  bash batch_runner.sh run 3 2

# 某 prompt 五个模型
bash batch_runner.sh batch 3
```

模型槽：`1=Doubao, 2=GPT-5.4, 3=Gemini, 4=DeepSeek, 5=MinMax/GLM/Qwen（按 prompt 轮换）`

### score_reason（历史高频返工点）

禁止空泛模板，例如「测试全部通过(1006 passed)…」「Doubao 前置筛选规则自动记 0 分」。

每条 `score_reason` 须包含：**prompt 任务点 + patch 文件 + pytest 结论 + 分数依据**。  
`log_entry()` 已自动 enrich；填表前还会 `normalize-log`。

---

## 三、填表提交（只做新表）

```bash
# 1. 规范化 score_reason + 本地规则复检
bash batch_runner.sh review

# 2. 新任务组全流程（创建 → 附件 → Docker 元数据 → 远程校验 → 修复 score 字段）
bash batch_runner.sh submit-fresh
```

等价于 `python3 submit_fresh_task_pipeline.py --apply`，顺序为：

1. `review_rollouts.py`（含 generic score_reason 拦截）
2. `submit_new_task_group.py --apply`
3. `submit_new_task_attachments.py --apply`
4. `repair_docker_build_metadata.py --apply`
5. `verify_fresh_task_remote.py`
6. `bitable_score_reason.py repair-remote --plan latest --apply`（同时写 `score_reason` + `score_check`）

### 禁止

| 禁止项 | 原因 |
|--------|------|
| `submit_missing_rollouts.py` | 易误匹配旧表 session，覆盖历史数据 |
| 往旧 root 写 SetRecords | 脚本内有 `PROTECTED_ROOT_RECORDS` 拦截，Agent 不得绕过 |
| 用 agent-browser 点击提交业务数据 | 仅允许快照/排障；写表必须走脚本 |
| 未 review 就 submit-fresh | 群规：没自查好不要频繁催质检 |

### 完成标准

- 新组结构：**1 root + 7 prompt + 35 rollout = 43 行**
- `verify_fresh_task_remote.py` → `errors=0`
- `score评分质检不合理数据` 视图 → **0 条**（或 repair 后 35/35 合理）
- 旧表 3 组仍在且未被修改

---

## 四、核心脚本（禁止从零重写）

| 脚本 | 用途 |
|------|------|
| `batch_runner.sh` | **主入口**：rollout / review / submit-fresh / progress |
| `bitable_score_reason.py` | 生成/规范化 score_reason；远程修复 score_check |
| `submit_fresh_task_pipeline.py` | 新表提交流水线（唯一推荐） |
| `submit_new_task_group.py` | ADD RECORD 创建新任务组 |
| `submit_new_task_attachments.py` | 上传 patch / repo / Dockerfile / 截图 |
| `review_rollouts.py` | 填表前本地规则复检 |
| `verify_fresh_task_remote.py` | 填表后远程结构复检 |
| `trae_command_bridge.py` | Trae command bridge 提交 |
| `trae_model_state.py` | 切换 Trae 模型状态 |
| `archive_completed_trial.py` | 归档并停 trial 容器 |

**Legacy（新任务勿用）：** `fill_and_submit_resume_v7.py`、`submit_missing_rollouts.py`

**必读文档：**

1. `标注规则_完整版.md` — 平台规则（最高优先级）
2. `docs/bitable-submission-checklist.md` — 填表踩坑清单
3. `docs/trae-trial-runbook.md` — 英文流程摘要
4. `python_timesheet_trial_guide.md` — Trial 背景说明

---

## 五、已知坑与处理（试标实测）

| 现象 | 处理 |
|------|------|
| Trae 日志模型名大小写不一致 | `batch_runner.sh` 已 case-insensitive 校验 |
| `xclip` 占住 `.batch_runner.lock` | 已 `9>&-` 释放；仍卡住则删 lock 后重试 |
| fullauto 重复跑已完成 rollout | 读 `trial_log.csv` 自动跳过 |
| 非 Doubao 跑时 Auto 模式干扰 | bridge 提交时 `TRAE_AUTO_MODE_GUARD=off` |
| 首次 create 只写入 root、子行校验失败 | 用 `new_task_backups/new_task_group_plan_*.json` 补子行，**仅限新 root** |
| score_reason 空泛 → AI 质检「不合理」 | `bitable_score_reason.py normalize-log` + `repair-remote --apply` |
| 只改 score_reason 不改 score_check | repair-remote 必须同时写两字段 |
| Docker 构建截图缺失 | 可从 build log 生成后走 attachments 流水线 |

---

## 六、错误汇报（Agent 必须遵守）

- 脚本失败 → **立即报告**完整 stderr，同一问题最多重试 **2 次**
- 模型不可用 / 4023 / Auto 回落 / 错模型 session → **不得记分归档**，重跑或等用户
- 需登录、验证码、付款 → **停止**，请用户 noVNC 处理
- **严禁**静默失败或编造「已提交成功」

---

## 七、完成后：群聊请求质检（用户发送，Agent 可代拟）

在 **BBS代码项目-小组3群** 发送（替换任务编号）：

```
@刀砍东风
第{N}个代码库 {repo 名称} 测试任务已完成，新表 {B000xxxxx} 已提交，麻烦帮忙质检。

自检：35 条 rollout 已完成；1+7+35 结构齐全；附件与 Docker 构建已上传；
score_reason / score_check 已自查（35/35 合理）；未修改旧表 B00001573 / B00008611 / B00010768。
请验收，有问题我立即修改。
```

**发群前 Gate：** `review` 通过 + 远程 `errors=0` + 不合理 score 为 0。

---

## 八、Agent 启动检查清单

```
[ ] 已读 标注规则_完整版.md + docs/bitable-submission-checklist.md
[ ] 已确认 trial_log.csv 进度，续跑不重复已完成 rollout
[ ] 已确认 3 个旧表 root 在保护列表，本次只建 New Group
[ ] 使用 batch_runner.sh / submit_fresh_task_pipeline.py，不从零写填表逻辑
[ ] 知道 score_reason 必须结构化，禁止空泛模板
[ ] 知道出错立即汇报，登录类问题交用户处理
[ ] 35/35 + review + submit-fresh + verify 通过后才拟群验收消息
```

---

## 九、每题独立判断

- 不同代码库的 prompt 文本、测试基线、模块名不同，**禁止**把上一题的 patch/分数/理由硬编码到下一题
- `bitable_score_reason.py` 从 `get_prompt()` 动态提取任务点；换题时只需更新 `batch_runner.sh` 内 prompt 与 `repo/`
