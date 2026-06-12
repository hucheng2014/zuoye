# renzheng — Claw 自动做题总入口

> 你是一个自动化做题 agent。这个仓库下有三个独立的做题项目，各自有自己的 `CLAUDE.md` 做题流程。
> **进入哪个项目目录做题，就严格遵循那个目录下的 `CLAUDE.md`。** 本文件只做分流和公共约定。

## 三个项目

| 目录 | 任务 | 单题时长 | 脚本位置 | 流程文件 |
|------|------|----------|----------|----------|
| `PROOFREAD/` | 中文校对 Eval（zh-CN/TW/HK，A/B/C 三响应判分+pairwise） | ~15 分钟（≥720s） | `PROOFREAD/scripts/` | `PROOFREAD/CLAUDE.md` |
| `TA Intelligent Polls/` | 投票生成评估（8 维度） | ~5 分钟（260~320s） | `TA Intelligent Polls/scripts/` | `TA Intelligent Polls/CLAUDE.md` |
| `VCGtexttoimage/` | 图片背景质量评估（A/B 两图侧对比） | 10 分钟（600s） | 项目顶层 `*.js` | `VCGtexttoimage/CLAUDE.md` |

> 注意三者节奏和脚本布局都不同：PROOFREAD/TA 是 extract→分析→fill→验证→bridge→submit 的多脚本流程；VCG 是 bridge.js 全生命周期管理 + agent 看图填表的简流程。**别把一个项目的命令套到另一个上。**

## 公共铁律（三项目通用）

1. **禁止跳题**：绝不用 Skip Current Task，绝不跳过任何题/子题/选项。
2. **用当前页面的题做题**，禁止用旧答案填当前题。
3. **每题独立判断**，严禁纯硬规则/自动化打分；多维度互相独立，不要互相污染。
4. **工具打开期间必须始终有保活脚本在跑**，否则累计 Inactive。
5. **同一时刻只能有一个 CDP 脚本连接**（多进程连同一端点会串行卡死）。
6. **后台脚本一律 `nohup ... &` 并重定向日志。**

## 公共环境

- CDP 端点：`http://127.0.0.1:9233`（备用 `9232`），脚本内置 fallback。
- 人工接管 VNC：`http://127.0.0.1:6082/vnc.html`。**遇登录/验证码/权限阻断 → 立即停下通知用户去 noVNC 手动处理，不要硬刚。**
- CDP 连接后必须设 viewport：`await page.setViewportSize({width: 1919, height: 1079});`
- 禁止用 `cat` 读文件，用 Read 工具或 node/python 脚本。
- 命令默认在 `renzheng/` 根目录执行；带空格的路径（`TA Intelligent Polls`）记得加引号。

## 失败处理通则

- 同一步骤连续失败 2 次：停止重试，诊断根因后换思路，不要反复打补丁。
- 拿不准判分 → 回去查对应项目的 `SOP.md` / `rules/` / `GRADING_RULES.md`，不要凭感觉。

## 知识库按需查询（替代全量 SOP 加载）

做题时**不要**把完整 SOP.md 全部读入上下文。改用知识库系统：

### 做题 prompt 构成

```
[compact_sop.md ~3KB]   ← 精简评分规则，每个维度一句话
[flow.md ~3KB]           ← 纯操作步骤，脚本命令序列
[题目 JSON]              ← extract_task.js 输出
```

### 遇到不确定的判分时

```bash
# 搜索相关规则
node pipeline/scripts/query_knowledge.js --task polls --query "选项遗漏是否算 not following"

# 直接拉某个维度的完整规则
node pipeline/scripts/query_knowledge.js --task polls --chunk dimension_independence
node pipeline/scripts/query_knowledge.js --task mail --chunk groundedness
node pipeline/scripts/query_knowledge.js --task proofread --chunk error_categories
```

### 各项目对应的 task_id

| 目录 | task_id | compact_sop 位置 |
|------|---------|------------------|
| `TA Intelligent Polls/` | `polls` | `pipeline/knowledge/polls/compact_sop.md` |
| `MAIL/` | `mail` | `pipeline/knowledge/mail/compact_sop.md` |
| `PROOFREAD/` | `proofread` | `pipeline/knowledge/proofread/compact_sop.md` |

### 何时查询 vs 何时不查询

**必须查询**：
- 边界情况（compact_sop 没覆盖的细节）
- Harmfulness 判断（需要看 19 个 harm category 定义）
- 维度独立性不确定时
- CJK/locale 特殊规则
- Pairwise comparison 逻辑

**不需要查询**：
- compact_sop 已经明确覆盖的简单判断
- 同一 session 内已经查过的相同问题
- 明显的 yes/no 判断
