# AI Agent 自动化工作规范 — VCG 图片背景质量评估

> **在开始做题前，请仔细阅读并严格遵守以下规则。这些是不可违反的硬性要求。**

---

## 项目简介

本项目评估 **AI 生成图片用作短信 App 消息背景的质量**。每题两张图（Image A / Image B），先独立评估每张图，再做侧对比。**TPT = 600 秒（10 分钟）**，这是铁律。

---

## 一、每道题必须独立判断，禁止硬编码

- **严禁**用固定规则或公式批量决定评分，每道题必须独立查看两张图片后判断。
- **三维度互相独立**：结构完美但不适合当背景 → Visual Suitability 照样打 No。
- 必须结合 prompt 内容评估，prompt 要求的奇异结构不算结构缺陷。
- **禁止**不看图片直接评分。

---

## 二、必须使用现有脚本和流程

**本项目脚本布局与其他项目不同：**

| 脚本 | 说明 |
|------|------|
| `bridge.js` | **全生命周期管理器**：keepalive + 计时 + 弹窗 + Next Task |
| `keepalive_lite.js` | 轻量保活 |

**注意**：VCG **没有** extract/fill/submit/session_guard 那套脚本。做题靠 Agent 通过浏览器交互完成填表与提交。

**必须阅读的规则文档：**
1. `VCGtexttoimage/CLAUDE.md` — 做题流程（**最高优先级**）
2. `VCGtexttoimage/SOP.md` — 评分标准
3. `VCGtexttoimage/GRADING_RULES.md` — 评分细则
4. `VCGtexttoimage/rules/*.md` — 各维度详细规则

**禁止**把 PROOFREAD 或 TA Polls 的脚本套用到 VCG。

---

## 三、严格按规则操作

**评分维度（Image A、Image B 各做一遍，再侧对比）：**

| 维度 | 说明 | 关键问题 |
|------|------|----------|
| **Visual Suitability** | 背景适用性（3 个子问题） | 叠一行文字消息能清楚读吗？ |
| **Structural Integrity** | 结构完整性（prompt-relative） | prompt 要求的奇异结构不算缺陷 |
| **Overall Quality** | 综合质量 | 综合所有维度 |

**Visual Suitability 子问题：**
- 1a 主体位置：是否偏离中心、不遮挡文字
- 1b 细节量：背景是否干净简洁
- 1c 配色：颜色是否简单统一

**时间模型：**
- Total 600s = Active + Inactive
- Inactive ≤ Active × 10%（上限约 55s）
- bridge.js 交互间隔 4-9s，注入 2-3 次深度睡眠（15-18s）

---

## 四、遇到错误必须及时汇报

- 图片加载失败 → **立即报告**，不要凭描述猜图。
- CDP 断连 → 连续失败 2 次后**停止重试**。
- 登录/验证码/权限问题 → **立即通知用户**去 noVNC（`http://127.0.0.1:6082/vnc.html`）。
- 过渡期间 10s 无交互 → 全程靠 bridge.js 保活。
- **严禁**静默失败或假装成功。

---

## 五、提交前必须复检

- [ ] Image A 和 Image B 都已独立评估
- [ ] 侧对比已完成
- [ ] 所有维度的 radio 已选择
- [ ] Grading reasons 已用英文填写（非满分维度）
- [ ] TPT ≥ 600 秒（提交后计时器仍在跑，等 TPT 满才点 Next Task）
- [ ] bridge.js 保活运行中

---

## 工作流程检查清单

```
[ ] 1. 我已读完 VCGtexttoimage/CLAUDE.md 和 SOP.md + GRADING_RULES.md
[ ] 2. 我了解 bridge.js 是全生命周期管理器，不是 PROOFREAD 那套脚本
[ ] 3. 我的方案是每题独立看图判断，三维度互相独立
[ ] 4. 我知道遇到错误必须立即报告
[ ] 5. 我知道提交前必须复检，TPT = 600s 是铁律
```
