# AI Agent 自动化工作规范 — Alibaba LabelX 音频字幕标注

> **在开始做题前，请仔细阅读并严格遵守以下规则。这些是不可违反的硬性要求。**

---

## 项目简介

本项目在 **LabelX 平台**上完成**音频字幕（Audio Caption）**标注任务：提取当前页面所有任务，离线生成字幕，复核后填写并提交。

---

## 一、每道题必须独立判断，禁止硬编码

- 每个视频的 caption 必须基于实际视频内容独立生成，不可套用模板。
- 每道题的 review 必须独立进行，不可批量跳过。

---

## 二、必须使用现有脚本和流程

**核心工作流（严格按此顺序执行）：**

| 步骤 | 命令 | 说明 |
|------|------|------|
| 1. 生成字幕 | `solve_current_page.py` | 提取当前页任务、下载视频、生成 caption |
| 2. 定向复核 | `review_targets.py` | 对可疑项独立复核 |
| 3. 填写+验证 | `solve_current_page.py --fill --use-results` | 填写并验证持久化 |
| 4. 提交 | `solve_current_page.py --submit --use-results` | 预检后提交 |

**关键辅助脚本：**
- `preflight_checks.py` — 提交前硬性检查（格式、时间戳、语言结构、音效规则）
- `new_rules_text_full.txt` — 最新飞书规则

**禁止**使用旧的单任务脚本。即使是单任务页面也必须用 current-page 工作流。

---

## 三、严格按规则操作

- 做题前必须阅读 `new_rules_text_full.txt` 中的规则。
- 填写前必须确认当前页面与生成结果匹配（index、原始 caption、视频时长）。
- `review_targets.py` 发现内容问题时，必须先更新 result JSON，再跑硬检，再 fill+verify。

---

## 四、遇到错误必须及时汇报

- 视频下载失败 → **立即报告**。
- 硬性检查失败 → **立即报告**，不要强行提交。
- 登录/验证码/权限问题 → **立即通知用户**去 noVNC（`http://127.0.0.1:6084/vnc.html`）。
- **严禁**静默失败或假装成功。

---

## 五、提交前必须复检

**提交纪律：**
- [ ] `solve_current_page.py --fill --use-results` 已通过（fill + reload 验证）
- [ ] `preflight_checks.py` 全部通过
- [ ] 实际填写的页面值与 JSON 一致
- [ ] reload 后持久化验证通过
- [ ] **禁止**从 `agent-browser` 提交，必须用生产脚本

---

## 工作流程检查清单

```
[ ] 1. 我已读完 README.md 和 new_rules_text_full.txt
[ ] 2. 我使用 solve_current_page.py 工作流，不用旧脚本
[ ] 3. 我的方案是每个 caption 独立生成和复核
[ ] 4. 我知道遇到错误必须立即报告
[ ] 5. 我知道提交前必须 fill+verify+preflight 全通过
```
