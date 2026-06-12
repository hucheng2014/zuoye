# AI Agent 自动化工作规范 — PR CERTIFICATION 偏好排序认证

> **在开始做题前，请仔细阅读并严格遵守以下规则。这些是不可违反的硬性要求。**

---

## 项目简介

本项目在 TryRating 平台上进行 **Preference Ranking（偏好排序）**评估，评估 AI 生成的多个响应的质量排序。涉及多模态评分指南。

---

## 一、每道题必须独立判断，禁止硬编码

- **严禁**用固定规则或模板批量决定排序，每道题必须独立阅读所有响应后判断。
- 各评分维度**必须独立评估**，不得互相影响。
- 偏好排序必须基于实际内容质量，不能套用固定模式。

---

## 二、必须使用现有脚本和流程

**判分方式：Agent 手动判分（LLM API 已停用）**

每题 extract 后**立即**读取 `current_task.json`，独立判分，写入 `current_ratings.json`，并运行 `node validate_ratings.js` 确认通过。**不得等到 720 秒才判分。**

### TPT 与刷新（铁律）

- **唯一计时**：页面顶部 `Time worked`（TPT），不是脚本墙钟
- **刷新 = 归零**：F5 / reload / 误点 Start 后 TPT 回到 0s，720s **从头计**
- **禁止** `page.reload()` 或手动刷新做题页
- TPT 归零后：重新 `fill_from_ratings.js`，再等满 720s 提交

### 前台 Agent 值守（铁律 — 不能全丢给后台）

`task_bridge.js` 只管保活和到点触发脚本，**不能替代 Agent 判分**。后台卡住时 Agent 必须前台接手：

| 时机 | Agent 必须做 |
|------|----------------|
| 新题 extract 后 | 立刻判分 → `validate_ratings.js` → `fill_from_ratings.js` |
| TPT 600s 前 | 确认 `formFilled=true`（`node agent_status.js`） |
| TPT ≥720s 未提交 | **立即** `submit_from_ratings.js --submit-only`，不等 bridge |
| submit 报 FATAL | 用 `agent-browser` 看页面 → 成功屏点 Next / 上传中等待 / 手动补点确认 |
| bridge 不在跑 | `./start_pipeline.sh` 或前台直接 fill+submit |

```bash
node agent_status.js   # 打印当前必须执行的前台动作（exit 2 = 有事要做）
```

**必须使用的脚本：**

| 脚本 | 说明 |
|------|------|
| `bridge.js` | 保活 + 计时管理 |
| `keepalive.js` | 页面保活 |
| `task_bridge.js` | 任务桥接 |
| `pr_automation_helper.js` | 自动化辅助 |
| `validate_ratings.js` | 判分文件指纹门禁 |
| `verify_task.js` | 填表后/提交前后复检 |
| `submit_from_ratings.js` | 从评分提交 |
| `confirm_and_next.js` | 确认并进入下一题 |
| `get_radio_details.js` | 获取 radio 按钮详情 |
| `inspect_dims.js` | 检查评分维度 |

### React 表单不同步处理（已验证）

如果 `node fill_from_ratings.js` 反复失败，日志出现 `commit: pending`，并且页面上 radio 已经显示 checked 但 `RESPONSES 0/N Complete` 不更新：

1. **不要刷新页面**，TPT 会归零。
2. 先运行 `node validate_ratings.js`，确认 ratings 指纹和字段合法。
3. 重新检查评分是否被平台校验逻辑拒绝。典型情况：`concision=Bad` 同时 `satisfaction=Slightly Satisfying` 会导致 Satisfaction radio 显示 checked 但该响应仍 invalid。此时必须按实际内容重新判分，不能为了过校验硬改；如果只是轻微超字数/略啰嗦，应优先考虑 `concision=Acceptable` + `description="It could have been made shorter"`。
4. 使用 React 直填脚本：

```bash
node fill_react_oneshot.js
node verify_task.js --form-only
node agent_status.js
```

5. `verify_task.js --form-only` 必须显示 `responsesComplete=N/N`、`compareComplete=N/N`、`submitReady=true`。通过后脚本会写入 `runs/form_filled.flag` 和 `runs/submittable.flag`，然后等待 TPT ≥720s 提交。

**必须阅读的规则文档：**
1. `FLOW.md` — 做题流程（**最高优先级**）
2. `Preference_Ranking_V5_核心指南中文详细总结.md` — 核心评分指南
3. `PR_V5_认证技巧与常见问题解答中文手册.md` — 认证技巧
4. `AFM_Multi_Modal_Grading_多模态评分指南中文总结.md` — 多模态评分
5. `QA_Feedback_Master_多语言 质检反馈中文总结.md` — QA 反馈

**禁止**从零编写新的浏览器交互脚本。

---

## 三、严格按规则操作

- 偏好排序必须基于响应的实际质量差异。
- 多维度评分时，各维度独立判断。
- 提交前确认所有评分维度已填写。

### 判分字段格式（铁律）

`current_ratings.json` 必须严格遵循以下格式，否则 `validate_ratings.js` 会拒绝：

| 维度 | 合法值 |
|------|--------|
| instructionFollowing | `Not following` / `Partially following` / `Fully following` |
| localization | `Yes (issues present)` / `No (no issues)` |
| concision | `Bad` / `Acceptable` / `Good` |
| truthfulness | `Not Truthful` / `Partially Truthful` / `Truthful` |
| satisfaction | `Highly Unsatisfying` / `Slightly Unsatisfying` / `Slightly Satisfying` / `Highly Satisfying` |

**必填附加字段：**
- concision = `Acceptable` 或 `Bad` 时，**必须**加 `"description"` 字段，值只能是：
  - `"It could have been made shorter"`
  - `"It could have been made longer"`
- localization = `Yes (issues present)` 时，**必须**加 `"localizationIssues"` 数组，值从以下选取：
  - `Unlocalized information` / `Overly-localized content` / `Spelling` / `Tone` / `Non-local perspective` / `Vocabulary` / `Awkward or unnatural writing` / `Formatting & punctuation` / `Grammar` / `Phrase or idiom` / `Units of measurement` / `Wrong language` / `Other`

### 满意度到偏好映射（铁律）

comparison 标签由双方 satisfaction 等级差距决定，**不得随意选择**：

| 等级差 | comparison 标签 |
|--------|----------------|
| 0（同级） | `Same` 或 `Slightly Better/Worse` |
| 1 级 | `Slightly Better/Worse`（**不是 Better！**） |
| 2 级 | `Better` 或 `Much Better` |
| 3 级 | `Much Better`（唯一选择） |

注意：A and B 中 A=Left，B=Right。A 更好用 Left，B 更好用 Right。

### Rationale 结构要求（铁律）

rationale 必须包含：
1. **每个响应独立块**：以 `RESPONSE A:` / `RESPONSE B:` 开头
2. 每块必须讨论全部 5 个维度（Instruction Following、Localization、Concision、Truthfulness、Satisfaction）
3. 末尾必须有 `Preference Summary:` 段落（≥40字符），解释偏好理由
4. **禁止**在 Preference Summary 中使用 "Left/Right Better" 行话，应直接说 "Response A/B is better"
5. 2响应时 rationale 最短 120 字符，3响应时 200 字符

---

## 四、遇到错误必须及时汇报

- CDP 断连/弹窗未关 → 连续失败 2 次后**停止重试**。
- 登录/验证码/权限问题 → **立即通知用户**去 noVNC（`http://127.0.0.1:6082/vnc.html`）。
- **严禁**静默失败或假装成功。
- **无更多任务弹窗**：如果出现 "No more tasks" 或类似弹窗，说明任务池已空。此时**关闭做题标签页（ANNOTATION TOOL）**，然后运行 `bash shutdown_all.sh` 收尾。

---

## 五、提交前必须复检

- [ ] 所有响应已排序/评分
- [ ] 所有维度已填写
- [ ] concision=Acceptable/Bad 时有 description 字段
- [ ] localization=Yes 时有 localizationIssues 数组
- [ ] comparison 标签与满意度等级差一致
- [ ] rationale 有 RESPONSE A/B 块 + 5维度 + Preference Summary
- [ ] `validate_ratings.js` 验证通过
- [ ] `verify_task.js --form-only` 页面表单复检通过（RESPONSES/Compare 全绿，Submit 可点）
- [ ] Submit 后 `verify_task.js --after` 或 success 屏确认
- [ ] 已进入下一题

---

## 工作流程检查清单

```
[ ] 1. 我已读完 FLOW.md 和核心指南
[ ] 2. 我了解所有脚本的用途和调用顺序
[ ] 3. 我的方案是每题独立判断排序
[ ] 4. 我知道遇到错误必须立即报告
[ ] 5. 我知道提交前必须 verify_task.js 验证
```
