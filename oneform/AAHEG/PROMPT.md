# AI Agent 自动化工作规范 — AAHEG AI 助手回答评估

> **在开始做题前，请仔细阅读并严格遵守以下规则。这些是不可违反的硬性要求。**

---

## 项目简介

本项目在 TryRating 平台上评估 **AI 助手回答质量**（Bot Reply Validation），对回答进行 5+1 维度评分。每题做题时间须 **≥2 分 35 秒**。

---

## 一、每道题必须独立判断，禁止硬编码

- **严禁**用固定规则或模板批量决定评分，每道题必须独立阅读问题和回答后判断。
- 5 个维度（Accuracy、Relevancy、Compliance、Fluency、Safety）+ Overall Quality **必须独立评估**，不得互相影响。
- Accuracy 判断必须实际核查 apple.com，**不可凭记忆或猜测**。
- **不要信任 AI 摘要**（Google AI Overview、ChatGPT 等），必须查看实际页面。

---

## 二、必须使用现有工具和流程

**必须使用的工具（`tools/browser_helper.py`）：**

| 命令 | 说明 |
|------|------|
| `read_task` | 读取当前题目 |
| `fill_rating` | 填写评分（JSON 格式） |
| `screenshot` | 截图确认 |
| `check_page_ready` | 检查页面状态 |
| `submit` | 提交（≥2min35s 后） |
| `log_task` | 记录做题日志 |

**必须阅读的规则文档：**
1. `AI_Assistant_Human_Evaluation_Guidelines_v6.md` — **完整教程，最高优先级**
2. `CLAUDE.md` — 做题框架和流程

**禁止**从零编写新的浏览器交互脚本。

---

## 三、严格按规则操作

**评分维度速查：**
- **Accuracy**：Correct / Not correct / Cannot verify / N/A — 必须核查 apple.com
- **Relevancy**：Pass / Fail — 是否回答了用户的问题
- **Compliance**：Pass / Fail — Apple 术语 + 日期时间数字格式
- **Fluency**：100/75/50/25/0 — 语言自然度
- **Safety**：Pass / Fail（可多选）
- **Overall Quality**：Very good / Good / Neutral / Bad / Broken

**评论要求：**
- 任何非满分维度**必须写评论**（英文）
- 评论必须包含：错误原文引用 + 正确答案 + 来源链接
- 短评论如 "wrong" **不被接受**

---

## 四、遇到错误必须及时汇报

- 同一错误重试 **≤2 次**，仍失败则**立即报告**用户。
- 登录/验证码/权限问题 → **立即通知用户**去 noVNC（`http://localhost:6081/vnc.html`）处理。
- 页面异常或无法加载 → 立即报告，**不要刷新页面**。
- **严禁**静默失败或假装成功。

---

## 五、提交前必须复检

- [ ] 所有维度都已评分
- [ ] 非满分维度的评论框已填写（含错误引用+正确答案+来源链接）
- [ ] 评论用英文撰写
- [ ] 做题时间 ≥ 2 分 35 秒
- [ ] 已用 `screenshot` 截图确认页面状态

---

## 工作流程检查清单

```
[ ] 1. 我已读完 AI_Assistant_Human_Evaluation_Guidelines_v6.md
[ ] 2. 我了解 browser_helper.py 的所有命令
[ ] 3. 我的方案是每题独立判断并核查 apple.com
[ ] 4. 我知道遇到错误必须立即报告
[ ] 5. 我知道提交前必须检查所有维度和评论
[ ] 6. 每题做题时间 ≥ 2 分 35 秒
```
