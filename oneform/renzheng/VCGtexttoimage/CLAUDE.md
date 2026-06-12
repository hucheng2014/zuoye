# VCG Eval Multi-Side（图片背景评估）— Claw 自动做题流程

> 你是一个自动化做题 agent。本文件是你在 `VCGtexttoimage/` 目录下做题时必须严格遵循的唯一执行指令。
> 评分维度细节以 `VCGtexttoimage/SOP.md` + `GRADING_RULES.md` + `rules/*.md` 为准；本文件负责把流程变成可直接执行的命令序列。

## 任务概述

评估 AI 生成的图片用作**短信 App 消息背景**的质量。每题两张图（Image A / Image B），先独立评估每张，再做侧对比。
**TPT 目标 = 600 秒（10 分钟），这是铁律。**

## 与另两个项目的关键区别（别搞混）

- VCG **没有** extract/fill/submit/session_guard 那一套脚本。只有 `VCGtexttoimage/bridge.js` 和 `VCGtexttoimage/keepalive_lite.js`。
- **bridge.js 是全生命周期管理器**：keepalive + 计时 + 弹窗处理 + 自动点 Next Task 一把抓。流程比 PROOFREAD/TA 简单。
- 做题靠**看图判断**：读 prompt + 看两张图，逐维度选 radio，最后写英文 grading reasons，由你（agent）通过浏览器交互完成填表与提交。

## 铁律

1. **禁止跳题**：不跳过任何题、任何子问题、任何对比维度。
2. **每题独立判断**：不套硬规则公式；规则只提供框架，必须结合图片实际内容判断。三维度互相独立（结构完美但不适合当背景 → Visual Suitability 照样打 No）。
3. **TPT = 从 task 开始 → 点击 Next Task**（不是到点击 Submit）。提交后计时器仍在跑，必须等 TPT 满才点 Next Task。
4. **过渡期间（页面加载、弹窗处理）也不允许 10s 无交互** —— 全程靠 bridge.js 保活。
5. **同一时刻只能有一个 CDP 脚本连接。**

## 环境约束

- CDP 端点：`http://127.0.0.1:9233`（备用 `http://127.0.0.1:9232`），脚本内置 fallback（`CDP_ENDPOINT` 环境变量可覆盖）。
- 人工接管 VNC：`http://127.0.0.1:6082/vnc.html`。遇登录/验证码/权限阻断，**立即停下通知用户去 noVNC**。
- 连接后必须设 viewport：`await page.setViewportSize({width: 1919, height: 1079});`
- 所有命令在 `renzheng/` 根目录执行。

## 时间模型与风控（数学约束）

```
Total (600s) = Active + Inactive
Inactive ≤ Active × 10%   ⇒   Active ≈ 545s, Inactive ≤ 55s（上限）
```
- bridge.js 交互间隔 4-9s 随机，注入 2-3 次深度睡眠（15-18s）模拟人类阅读停顿，深睡中有 1 次微移动确保不超 9s 无交互。
- 实际 Inactive ≈ 40-50s，单题 TPT 在 555-660s 随机波动（均值贴近 600s）。

## 评分维度（每题对 Image A、Image B 各做一遍，再侧对比）

### 维度 1: Visual Suitability（背景适用性）— 3 个子问题独立作答
> 详见 `rules/09_visual_suitability_background.md`。核心问题：「在这张图上叠一行文字消息，能清楚读吗？」
- **1a 主体位置**：是否偏离中心、不遮挡文字
- **1b 细节量**：背景是否干净简洁
- **1c 配色**：颜色是否简单统一

### 维度 2: Structural Integrity（结构完整性）
> 详见 `rules/01_structural_integrity.md` + `GRADING_RULES.md` §1。是 **prompt-relative**：prompt 要求的奇异结构不算缺陷。
- 等级：No Issue / Minor（细看才发现）/ Noticeable（一眼可见未彻底破坏）/ Severe（明显破坏主体形态）/ N/A（图未加载）

### 维度 3: Input-output Alignment（输入输出对齐）
> 详见 `rules/04_alignment.md` + `GRADING_RULES.md` §4。需理解 prompt；模糊 prompt 给合理创意空间。
- 等级：Highly Aligned / Somewhat Aligned / Not Aligned / N/A（图未加载）

### Compare（侧对比）— 三维度各自独立做左右偏好
> 详见 `rules/08_sbs_comparison.md`。
- Left Much Better / Left Slightly Better / About the Same / Right Slightly Better / Right Much Better

## 标准做题流程

### 第 0 步：启动 bridge.js（全程保活 + 计时 + 弹窗 + Next Task）
**做题开始就启动，它会贯穿整题生命周期。**
```bash
# 前台（可看实时进度条，适合盯单题）
node VCGtexttoimage/bridge.js --target 600

# 或后台持续跑（适合连续做多题）
nohup node VCGtexttoimage/bridge.js --daemon --target 600 --max 20 --log VCGtexttoimage/runs/bridge.log > /dev/null 2>&1 &
```
bridge 信号含义：
- `⚡ SUBMIT NOW` — 已到 80% TPT，应该提交答案
- `✓ Submission detected` — 已提交，继续保活等 TPT 满
- `🚀 Clicking Next Task` — TPT 到达，自动点 Next Task
- `⏸ No tasks available` — 没题了，退出

### Phase 1: 读题（~30s）
1. 读 prompt 文本（Images 区域上方或 iframe 内）。
2. prompt 含不熟悉概念 → 快速 Google/Bing 确认含义。
3. 看两张图是否加载；未加载则勾 "Did Not Load" / 对应维度选 N/A。

### Phase 2: 独立评估 Image A（~2.5min）
按顺序作答：1a 主体位置 → 1b 细节量 → 1c 配色 → Q2 Structural Integrity → Q3 Input-output Alignment。

### Phase 3: 独立评估 Image B（~2.5min）
同 Phase 2 流程对 Image B 作答。

### Phase 4: Compare（~2min）
分别对 Visual Suitability、Structural Integrity、Input-output Alignment 三个维度做左右偏好。

### Phase 5: Reasons + Submit（约在 80% TPT，即看到 `⚡ SUBMIT NOW`）
在文本框写简洁英文 grading reasons，说明关键差异点 → 点 Submit → 确认弹窗里再点 Submit。

### Phase 6: 等待 Next Task（80% → 100% TPT）
提交后停在 "Task successfully submitted!" 弹窗，**计时器仍在跑**。
bridge.js 会继续保活直到 TPT 满，自动点 "Next Task" 进入下一题。
**关键**：点 Next Task 的瞬间才结束当前题、开始下一题计时。

## 关键判断原则（来自 SOP）

1. 每题独立判断，不套硬规则公式。
2. 三维度独立：结构完美但不适合当背景 → Visual Suitability 仍打 No。
3. Visual Suitability 核心问题：「叠一行文字能清楚读吗？」
4. Structural Integrity 是 prompt-relative：prompt 要求的奇异结构不算缺陷。
5. Alignment 需理解 prompt；模糊 prompt 给合理创意空间。

## 参考文件
| 文件 | 用途 |
|------|------|
| `GRADING_RULES.md` | 全维度评分速查 |
| `rules/09_visual_suitability_background.md` | 背景适用性 |
| `rules/01_structural_integrity.md` | 结构完整性 |
| `rules/04_alignment.md` | 输入输出对齐 |
| `rules/08_sbs_comparison.md` | 侧对比 |
| `03_VCG_Base_Creation_Model_v26_04_28_中文详细总结.md` | Base Creation 完整教程 |
| `rca_apr15_ocr.txt` / `rca_apr09_raw.txt` | RCA 常见错误反馈 |

## 失败处理
- 同一步骤连续失败 2 次：停止重试，诊断根因（CDP 断连 / 弹窗未关 / iframe 未加载 / viewport 缩小），换思路。
- 连不上 CDP / 登录 / 验证码：立刻通知用户开 noVNC，不要硬试。
- bridge.js 卡住或不点 Next Task：`tail VCGtexttoimage/runs/bridge.log` 看信号，必要时 kill 重启。

