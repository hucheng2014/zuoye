# AI Agent 自动化工作规范 — MAIL 邮件智能回复评估

> **在开始做题前，请仔细阅读并严格遵守以下规则。这些是不可违反的硬性要求。**

---

## 项目简介

本项目评估 **AI 生成的邮件智能回复（Smart Reply）质量**，涉及多维度评分。做题流程与 PROOFREAD/TA Polls 类似（extract → 分析 → fill → 验证 → bridge → submit），但脚本和规则独立。

---

## 一、每道题必须独立判断，禁止硬编码

- **严禁**用固定规则或模板批量决定评分，每道题必须独立阅读邮件对话和回复后判断。
- 各评分维度**必须独立评估**，不得互相污染。
- 回复的 groundedness（是否有邮件上下文依据）和 relevance（是否切题）独立判断。

---

## 二、必须使用现有脚本和流程

**必须使用的脚本（`MAIL/scripts/` 目录）：**

| 脚本 | 说明 |
|------|------|
| `extract_task.js` | 提取当前题目 |
| `fill_task.js` | 填写评分 |
| `screenshot.js` | 截图确认 |
| `starshot_keepalive.js` | 保活脚本 |
| `click_confirm_submit.js` | 确认提交 |
| `click_done.js` | 完成/下一题 |
| `task_active.js` | 检查任务状态 |
| `wait_time.js` | 等待计时 |

**必须阅读的规则文档：**
1. `WT_Mail_Smart_Reply_MSR_Feedback_May22.txt` — **反馈数据（最高优先级）**
2. `WT_Mail_Smart_Reply_MSR_Feedback_May22_中文详细总结.md` — 中文总结
3. 知识库：`pipeline/knowledge/mail/compact_sop.md` + `flow.md`

**禁止**把 PROOFREAD 或 TA Polls 的脚本套用到 MAIL。

---

## 三、严格按规则操作

- 使用知识库按需查询规则，不要把完整 SOP 全部加载到上下文。
- 评分基于邮件对话上下文和 AI 回复内容的实际质量。
- 不确定的判分必须查询知识库，不要凭感觉。

```bash
node pipeline/scripts/query_knowledge.js --task mail --chunk groundedness
node pipeline/scripts/query_knowledge.js --task mail --query "具体规则问题"
```

---

## 四、遇到错误必须及时汇报

- CDP 断连/弹窗未关/iframe 未加载 → 连续失败 2 次后**停止重试**。
- 登录/验证码/权限问题 → **立即通知用户**去 noVNC（`http://127.0.0.1:6082/vnc.html`）。
- **严禁**静默失败或假装成功。

---

## 五、提交前必须复检

- [ ] 所有评分维度已填写
- [ ] 填表后已验证无 validation error
- [ ] 计时器已满足最低要求
- [ ] Submit 后确认成功（timer 消失/归 0）
- [ ] 已进入下一题

---

## 工作流程检查清单

```
[ ] 1. 我已读完 MAIL 目录下的教程和反馈文档
[ ] 2. 我了解 scripts/ 下所有脚本的用途
[ ] 3. 我的方案是每题独立判断，各维度独立评估
[ ] 4. 我知道遇到错误必须立即报告
[ ] 5. 我知道提交前必须验证所有维度
```
