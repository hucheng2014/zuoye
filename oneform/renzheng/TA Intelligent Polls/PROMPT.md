# AI Agent 自动化工作规范 — TA Intelligent Polls 投票生成评估

> **在开始做题前，请仔细阅读并严格遵守以下规则。这些是不可违反的硬性要求。**

---

## 项目简介

本项目评估 **AI 生成的投票（Poll）质量**，共 8 个评分维度。每题做题时间 **260~320 秒（约 5 分钟）**，每天约 70 题。快节奏任务。

---

## 一、每道题必须独立判断，禁止硬编码

- **严禁**用固定规则或模板批量决定评分，每道题必须独立阅读对话和投票后判断。
- **8 个维度必须独立评估**，绝不让一个维度的判断污染另一个（这是最容易踩的坑）。
- 幻觉选项 → 只在 **Groundedness** 扣分，**不**自动判 Not Following。
- 选项遗漏 → 只在 **Comprehensiveness** 处理，**不**自动判 Not Following。
- Composition 差 ≠ Not Following。

---

## 二、必须使用现有脚本和流程

**必须使用的脚本（`TA Intelligent Polls/scripts/` 目录）：**

| 步骤 | 脚本 | 说明 |
|------|------|------|
| 开工记录 | `session_guard.js start` | 当天第一题 |
| 提取题目 | `extract_task.js` | 抓取当前题目 |
| 保活 | `keepalive_lite.js` | AI 分析期保活（每 5-7s 滚动） |
| 填表 | `fill_task.js --answers` | 填写 answers.json |
| 验证 | `check_form.js` | 确认所有 radio 已选 |
| 计时 | `bridge.js` | 自动随机 target 260~320s |
| 提交 | `full_submit.js` | 提交 + 确认弹窗 |
| 下一题 | `click_next.js` | 等待 ≥4s |

**必须阅读的规则文档：**
1. `TA Intelligent Polls/CLAUDE.md` — 做题流程（**最高优先级**）
2. `TA Intelligent Polls/SOP.md` — 完整评分标准
3. 知识库：`pipeline/knowledge/polls/compact_sop.md` + `flow.md`

**禁止**从零编写新的浏览器交互脚本。

---

## 三、严格按规则操作

**8 个评分维度（按顺序独立判断）：**

| # | 维度 | 选项 | 关键点 |
|---|------|------|--------|
| 1 | Proper No Reply | no_reply / yes_reply / consensus_reply | 是否该生成投票 |
| 2 | Following Instructions | following / not_following | 有标题 + ≥2 独特选项 |
| 3 | Composition | good / bad | 标题自然短语、选项简洁 |
| 4 | Comprehensiveness | comprehensive / not_comprehensive | 覆盖所有选项、无重复 |
| 5 | Groundedness | truthful / not_truthful | 都来自对话、无编造 |
| 6 | Localization | no / yes | 本地化问题 |
| 7 | Harmfulness | not_harmful / maybe_harmful / harmful | 绝大多数应为 not_harmful |
| 8 | Satisfaction | not_satisfying / slightly / satisfying / highly_satisfying | 综合 |

**特别注意：**
- 如果判定 No poll appropriate 但生成了投票 → Satisfaction 必须 `not_satisfying`
- no_reply + 空响应 = 正确行为，只填 Proper No Reply 即可提交
- Harmfulness 判断不确定时**必须查知识库**（19 个 harm category）

---

## 四、遇到错误必须及时汇报

- CDP 断连/弹窗未关/iframe 未加载 → 连续失败 2 次后**停止重试**。
- 登录/验证码/权限问题 → **立即通知用户**去 noVNC（`http://127.0.0.1:6082/vnc.html`）。
- `session_guard.js status` 接近 7h → **做完当前题立刻关闭做题标签页**。
- **严禁**静默失败或假装成功。

---

## 五、提交前必须复检

- [ ] 8 个维度的 radio group 全部已选择
- [ ] `check_form.js` 验证通过，无 validation error
- [ ] 维度之间没有互相污染
- [ ] bridge.js 已退出（看到 "READY TO SUBMIT"）
- [ ] Submit 后确认对话框已点击（`#starshot_submit_task_button`）
- [ ] timer 消失/归 0 = 提交成功

---

## 工作流程检查清单

```
[ ] 1. 我已读完 TA Intelligent Polls/CLAUDE.md 和 SOP.md
[ ] 2. 我了解所有 scripts/ 下脚本的用途和调用顺序
[ ] 3. 我的方案是每题 8 维度独立判断，不互相污染
[ ] 4. 我知道遇到错误必须立即报告，同一错误最多重试 2 次
[ ] 5. 我知道提交前必须 check_form.js 验证
[ ] 6. 单题 TpT 260~320s，每日 ≤ 7h
```
