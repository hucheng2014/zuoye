# AI Agent 自动化工作规范 — ROAD Bounding Box 道路标注评估

> **在开始做题前，请仔细阅读并严格遵守以下规则。这些是不可违反的硬性要求。**

---

## 项目简介

本项目在 TryRating 平台上评估 **3D 道路渲染中的 painted features 质量**：在截图的 bounding box（紫/粉色框）内判断道路标注问题，选择严重程度并勾选对应问题类型。

---

## 一、每张图必须独立判断，禁止硬编码

- **严禁**用固定规则批量决定评分，每张图必须独立查看 bounding box 内的内容。
- 只评估 **bounding box 内**的问题，框外完全忽略。
- **不查卫星图、街景或真实世界**，只看截图渲染。
- 不要把 painted median 内部设计性的断续斜线当作问题。

---

## 二、必须使用现有流程和文档

**必须阅读的规则文档：**
1. `ROAD_BOUNDING_BOX_WORKFLOW_GPT54MINI.md` — **做题流程和操作指南（最高优先级）**
2. `tutorial_summary_bilingual.md` — 教程双语总结

**关键操作参考（CDP）：**
- 抽取图片：`document.images[0]` → fetch → base64 → 保存
- 选 radio：`document.querySelector('input[type=radio][value="major"]').click()`
- 勾选 checkbox：按 index 点击（详见文档中的 index-feature-issue 对照表）
- 提交：查找含 "Submit Rating" 的 button 并 click

**禁止**从零编写新的浏览器交互脚本，优先参照文档中的代码片段。

---

## 三、严格按规则操作

**严重程度（4 选 1）：**
- `major`：不放大也明显，普通人一眼能看到
- `minor`：需要仔细看或放大才确认
- `no_issue`：框内道路可见且无可见问题
- `not_visible`：没有 3D 道路/道路渲染

**Feature 类型 + Issue 类型：**

| Feature | 可选 Issue |
|---------|-----------|
| Painted Median | Poor Geometry / Excess Paint / Void Issue / Other Issue |
| Lane Marking | Poor Geometry / Excess Paint / Collide / Void / Other |
| Colored Lane | Poor Geometry / Collide / Excess Paint / Void / Other |
| RSM Text | Poor Geometry / Excess Paint / Collide / Void / Other |
| RSM Glyph | Poor Geometry / Excess Paint / Collide / Void / Other |
| Other Issues | Other/Unclear Void / Other Issue |

**不要标的问题：** 半透明地图箭头、道路标签、灰色铁路线、正常模糊双黄线等。

---

## 四、遇到错误必须及时汇报

- 图片加载失败 → **立即报告**。
- 页面 radio/checkbox 结构与预期不符 → **先打印列表再操作**，不确定则报告。
- 同一错误重试 **≤2 次**，仍失败则停止。
- 登录/验证码/权限问题 → **立即通知用户**。

---

## 五、提交前必须复检

- [ ] 严重程度已选择（major/minor/no_issue/not_visible）
- [ ] 若选 major/minor，已勾选所有适用的 feature+issue checkbox
- [ ] checkbox index 与预期一致（先打印确认）
- [ ] 只评估了 bounding box 内的内容
- [ ] 提交后确认已进入下一题

---

## 工作流程检查清单

```
[ ] 1. 我已读完 ROAD_BOUNDING_BOX_WORKFLOW_GPT54MINI.md
[ ] 2. 我了解 CDP 连接方式和 checkbox index 对照表
[ ] 3. 我的方案是每张图独立查看 bounding box 内容
[ ] 4. 我知道遇到错误必须立即报告
[ ] 5. 我知道提交前必须复检选择项
```
