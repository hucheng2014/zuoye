# AI Agent 自动化工作规范 — Oneform 项目总入口

> **在开始任何做题任务前，请仔细阅读并严格遵守以下规则。**

---

## 项目结构

本目录包含多个独立的自动化做题子项目，**每个子项目有自己的 PROMPT.md、脚本和规则文档**。进入具体子项目做题前，必须先读该子项目的 PROMPT.md。

### oneform 直属项目

| 目录 | 任务 | 关键文档 |
|------|------|----------|
| `AD/` | Search Ads 搜索广告相关性评估 | `AD/PROMPT.md`、`AD_RATING_SOP.md` |
| `ADJIAN/` | ASR 音频标注 | `ADJIAN/PROMPT.md`、`MEMORY.md` |
| `AAHEG/` | AI 助手回答评估（5+1 维度） | `AAHEG/PROMPT.md`、`AI_Assistant_Human_Evaluation_Guidelines_v6.md` |
| `BMG/` | Broad Match 关键词匹配评估 | `BMG/PROMPT.md`、`AGENTS.md` |
| `RQOAE/` | 音频编辑质量评估（1-5 分） | `RQOAE/PROMPT.md`、`AGENTS.md` |
| `ROADBoundingBox/` | 道路 Bounding Box 标注评估 | `ROADBoundingBox/PROMPT.md` |
| `RTQOT/` | 过渡质量评估 | `RTQOT/PROMPT.md`（如有） |
| `pipeline/` | 自动化流水线编排 | `pipeline/CLAUDE.md` |

### renzheng/ 子项目

| 目录 | 任务 | 单题时长 |
|------|------|----------|
| `renzheng/PROOFREAD/` | 中文校对 Eval | ~15 分钟 |
| `renzheng/TA Intelligent Polls/` | 投票生成评估 | ~5 分钟 |
| `renzheng/VCGtexttoimage/` | 图片背景质量评估 | ~10 分钟 |
| `renzheng/MAIL/` | 邮件智能回复评估 | 见项目文档 |
| `renzheng/PR CERTIFICATION/` | 偏好排序认证 | 见项目文档 |

---

## 公共铁律（所有子项目通用）

### 一、禁止硬编码，每题独立判断
- 严禁用固定规则、关键词匹配或模板批量决定评分。
- 每道题/每个任务必须独立读取、独立分析、独立决策。

### 二、必须复用现有脚本和流程
- 进入子项目后，先读该项目的 `PROMPT.md` 和 `CLAUDE.md`/`AGENTS.md`。
- 优先使用项目内已有的脚本，禁止从零重写。
- 禁止跨项目混用脚本。

### 三、必须先阅读规则文档
- 做题前必须读完项目内的教程、SOP、规则文件。
- 严格按规则操作，不可自行猜测或发明规则。
- 不确定时查询知识库：`pipeline/scripts/query_knowledge.js`。

### 四、遇到错误必须及时汇报
- 同一错误重试 ≤2 次，仍失败则立即报告用户。
- 登录/验证码/权限问题 → 立即通知用户去 noVNC 手动处理。
- 严禁静默失败、吞掉错误、假装成功。

### 五、提交前必须复检
- 所有评分维度已填写且正确。
- 验证脚本已通过。
- 计时器满足最低要求。
- 提交后确认成功。

---

## 知识库按需查询

```bash
# 查看可用任务
node pipeline/scripts/query_knowledge.js --task ad --list
node pipeline/scripts/query_knowledge.js --task polls --list
node pipeline/scripts/query_knowledge.js --task proofread --list
node pipeline/scripts/query_knowledge.js --task mail --list
node pipeline/scripts/query_knowledge.js --task rqoae --list

# 按需查询具体规则
node pipeline/scripts/query_knowledge.js --task <task_id> --query "具体问题"
node pipeline/scripts/query_knowledge.js --task <task_id> --chunk <chunk_name>
```
