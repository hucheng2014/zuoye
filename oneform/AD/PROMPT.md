# AI Agent 自动化工作规范 — AD Search Ads Relevance

> **在开始做题前，请仔细阅读并严格遵守以下规则。这些是不可违反的硬性要求。**

---

## 项目简介

本项目在 TryRating 平台上评估**搜索广告相关性**：给定用户搜索词（Query）和展示的广告 App（Ad），判断广告与搜索意图的相关程度。每页 5 道题，每页做题时间须 **≥10 分钟**。

---

## 一、每道题必须独立判断，禁止硬编码

- **严禁**用关键词匹配表、固定规则或模板批量决定评分。
- 每道题必须独立分析 Query 意图和 Ad 功能，基于实际研究得出结论。
- 不同题目之间的 Query、App、上下文完全不同，**绝不可套用上一题的判断逻辑**。
- Game 题必须比较 play style / theme / audience 三维度，不能只看"都是游戏"。

---

## 二、必须优先使用现有脚本和流程

**必须使用的现有脚本（禁止从零重写）：**

| 步骤 | 脚本 | 说明 |
|------|------|------|
| 填写页面 | `fill_ad_page.py` | 从 JSON 记录填评分+评论到页面 |
| 提交页面 | `submit_ad_page.py` | 校验+提交，记录时间戳 |
| 离线校验 | `tools/validate_ad_batch.py` | 检查记录完整性，不连浏览器 |
| 初始化记录 | `tools/validate_ad_batch.py --init` | 创建批次记录模板 |

**必须阅读的规则文档（按优先级）：**
1. `AD_RATING_SOP.md` — **最高优先级**，做题标准流程
2. `Search Ads.md` — 官方教程全文
3. `GPT_MINI_AD_PROMPT.md` — 精简提示词参考
4. 知识库：`pipeline/knowledge/ad/compact_sop.md` + `flow.md`

**禁止**恢复已删除的 `auto_rating.py`、`smart_rating.py`、`runner.py`、`loop_rating.py` 等自动判题脚本。

---

## 三、严格按规则操作

- **评分等级**：Excellent / Good / Acceptable / Bad（四档）
- **研究顺序**：看 Query → 看 Ad App → 查 App Store 搜索 → 必要时网页搜索
- **Comments 格式**：`[Query Intent] ... [Ad Analysis] ... [Relevance] ... [Why not higher/lower] ... Rated [Rating].`
- **Bad 必须解释原因**，所有题建议写简短理由
- Comments 中 Query/App 名称必须对应当前题，**不得串题**
- 提交前检查：5 道题都有评分、Comments 非空、无 `This field is required!`

---

## 四、遇到错误必须及时汇报

- 同一错误重试 **≤2 次**，仍失败则**立即报告**用户。
- 以下情况必须立即通知用户去 noVNC（`http://localhost:6081/vnc.html`）手动处理：
  - 登录/验证码/权限问题
  - 页面异常或无法加载
- **严禁**静默失败或假装成功。

---

## 五、提交前必须复检

**逐题检查清单：**
- [ ] 5 道题都选了 Ad Relevance 评分
- [ ] 每题 Comments 不为空
- [ ] Bad 题 Comments 明确解释了原因
- [ ] Comments 中的 Query/App 没串题
- [ ] 页面无 `This field is required!` 报错
- [ ] JSON 记录文件与页面内容一致

**只有全部通过才允许提交。提交后确认新页面加载正常。**

---

## 工作流程检查清单

```
[ ] 1. 我已读完 AD_RATING_SOP.md 和 Search Ads.md
[ ] 2. 我了解 fill_ad_page.py / submit_ad_page.py / validate_ad_batch.py 的用法
[ ] 3. 我的方案是逐题独立研究判断，而非硬编码批量处理
[ ] 4. 我知道遇到错误必须立即报告
[ ] 5. 我知道提交前必须逐题复检
[ ] 6. 每页做题时间 ≥ 10 分钟
```
