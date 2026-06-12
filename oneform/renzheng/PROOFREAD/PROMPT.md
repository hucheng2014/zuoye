# AI Agent 自动化工作规范 — PROOFREAD 中文校对评估

> **在开始做题前，请仔细阅读并严格遵守以下规则。这些是不可违反的硬性要求。**

---

## 项目简介

本项目评估 **AI 生成的中文校对响应质量**（zh-CN/zh-TW/zh-HK），对 A/B/C 三个响应分别判分并进行 pairwise 比较。每题做题时间须 **≥12 分钟（720 秒）**，每天 25-28 题。

---

## 一、每道题必须独立判断，禁止硬编码

- **严禁**用固定规则或模板批量决定评分，每道题必须独立阅读原文和三个响应后判断。
- 各维度（correctness、severity、error categories、pairwise）**必须独立评估**，不得互相污染。
- **最小编辑原则**是核心：好的校对只改必须改的，不做不必要的修改。
- zh-CN/zh-TW/zh-HK 的本地化规则不同，必须按对应 locale 的规则判断。

---

## 二、必须使用现有脚本和流程

**必须使用的脚本（`PROOFREAD/scripts/` 目录）：**

| 步骤 | 脚本 | 说明 |
|------|------|------|
| 开工记录 | `session_guard.js start` | 当天第一题执行一次 |
| 提取题目 | `extract_task.js` | 抓取当前题目数据 |
| 保活 | `keepalive_lite.js` | 消除 AI 分析期 inactive |
| 预检 | `fill_task.js --dry-run` | 干跑检查 |
| 填表 | `fill_task.js --answers` | 正式填写 |
| 验证 | `check_tabs.js` | 确认 3/3 Complete |
| 计时 | `bridge.js` | 推进计时器到 720s |
| 提交 | `full_submit.js` | 提交 + 确认 |
| 下一题 | 手动点 Next Task | 等待 ≥4s 再抓新框架 |

**必须阅读的规则文档：**
1. `PROOFREAD/CLAUDE.md` — 做题流程（**最高优先级**）
2. `PROOFREAD/SOP.md` — 完整评分标准和判分规则
3. 知识库：`pipeline/knowledge/proofread/compact_sop.md` + `flow.md`
4. 中文教程总结文件（按需查阅）

**禁止**从零编写新的浏览器交互脚本。

---

## 三、严格按规则操作

**核心判分要点：**
- **Correctness**：校对是否正确识别了原文中的实际错误
- **Severity**：错误的严重程度（三级）
- **Error Categories**：formatting / mechanical / core_content
- **Pairwise**：A/B/C 三响应的质量比较

**特别注意：**
- `correctness = some_unnecessary` 时会动态渲染额外分类组，需手填
- pre-checked 残留：fill_task 只加不取消，填完需逐 tab 核查多余勾选
- 提交确认：点 Submit 后需再点 `#starshot_submit_task_button`
- 确认成功后手动点 "Next Task"

---

## 四、遇到错误必须及时汇报

- CDP 断连/弹窗未关/iframe 未加载 → 连续失败 2 次后**停止重试**，诊断根因。
- 登录/验证码/权限问题 → **立即通知用户**去 noVNC（`http://127.0.0.1:6082/vnc.html`）。
- `session_guard.js status` 接近 7h → **做完当前题立刻关闭做题标签页**。
- **严禁**静默失败或假装成功。

---

## 五、提交前必须复检

- [ ] Response A/B/C 全部 `3/3 Complete` 且 `0 errors`
- [ ] `check_tabs.js` 验证通过（反复检查直到全绿）
- [ ] `correctness = some_unnecessary` 时的额外分类组已手填
- [ ] 无 pre-checked 残留（多余 checkbox 已取消）
- [ ] 计时器 ≥ 720s
- [ ] Submit 后确认对话框已点击（timer 消失/归 0 = 成功）

---

## 工作流程检查清单

```
[ ] 1. 我已读完 PROOFREAD/CLAUDE.md 和 SOP.md
[ ] 2. 我了解所有 scripts/ 下脚本的用途和调用顺序
[ ] 3. 我的方案是每题独立判断，遵循最小编辑原则
[ ] 4. 我知道遇到错误必须立即报告，同一错误最多重试 2 次
[ ] 5. 我知道提交前必须 check_tabs.js 全绿
[ ] 6. 每题做题时间 ≥ 12 分钟，每日 ≤ 7.5h
```
