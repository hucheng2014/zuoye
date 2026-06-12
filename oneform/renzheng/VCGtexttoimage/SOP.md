# VCG Eval Multi Side — SOP

## 任务概述

评估AI生成的图片用作**短信App消息背景**的质量。每题包含两张图片（Image A / Image B），需要独立评估每张图后做侧对比。

**TPT 目标：10 分钟（600 秒）。这是铁律。**

---

## 评估维度

### 维度 1: Visual Suitability（背景适用性）

> 详细规则：`rules/09_visual_suitability_background.md`

三个子问题独立作答：
- **1a** 主体位置：是否偏离中心，不遮挡文字
- **1b** 细节量：背景是否干净简洁
- **1c** 配色：颜色是否简单统一

### 维度 2: Structural Integrity（结构完整性）

> 详细规则：`rules/01_structural_integrity.md` + `GRADING_RULES.md` §1

评估图中主体/物体的解剖、结构、比例是否合理。

| 等级 | 含义 |
|------|------|
| No Structural Integrity Issue | 无结构缺陷 |
| Minor | 仔细看才能发现 |
| Noticeable | 一眼可见但未彻底破坏 |
| Severe | 明显破坏主体基本形态 |
| N/A | 图片未加载 |

### 维度 3: Input-output Alignment（输入输出对齐）

> 详细规则：`rules/04_alignment.md` + `GRADING_RULES.md` §4

评估图片与 prompt 的匹配程度。

| 等级 | 含义 |
|------|------|
| Highly Aligned | 所有核心元素都体现 |
| Somewhat Aligned | 部分元素匹配，有遗漏 |
| Not Aligned | 严重偏离 prompt |
| N/A | 图片未加载 |

### Compare（侧对比）

> 详细规则：`rules/08_sbs_comparison.md`

三个维度各自独立做左右偏好：Left Much Better / Left Slightly Better / About the Same / Right Slightly Better / Right Much Better

最后写出 grading reasons（简述为什么这样评分）。

---

## 做题流程

### Phase 1: 读题（~30s）

1. 读取 prompt 文本（在 Images 区域上方或 iframe 内）
2. 如果 prompt 含不熟悉的概念，快速 Google/Bing 确认含义
3. 观察两张图片是否加载；未加载则勾选 "Did Not Load"

### Phase 2: 独立评估 Image A（~2.5 min）

按顺序逐一作答：
1. **1a** 看主体位置 → 选择
2. **1b** 看细节密度 → 选择
3. **1c** 看颜色复杂度 → 选择
4. **Q2** Structural Integrity → 选择等级
5. **Q3** Input-output Alignment → 选择等级

### Phase 3: 独立评估 Image B（~2.5 min）

同上流程对 Image B 作答。

### Phase 4: Compare（~2 min）

1. 对比 Visual Suitability 整体 → 选偏好
2. 对比 Structural Integrity → 选偏好
3. 对比 Input-output Alignment → 选偏好

### Phase 5: Reasons + Submit（在 80% TPT 时）

在文本框写出简洁评分理由（英文），说明关键差异点。点击 Submit → 确认弹窗 Submit。

### Phase 6: 等待 Next Task（80% → 100% TPT）

提交后停留在 "Task successfully submitted!" 弹窗，**计时器仍在跑**。
bridge.js 会继续保活直到 TPT 到达，自动点击 "Next Task" 进入下一题。

**关键**：点击 Next Task 的瞬间才结束当前题计时、开始下一题计时。
过渡期间（页面加载、弹窗处理）也不允许 10s 无交互。

---

## 关键判断原则

1. **每题独立判断** — 不套用硬规则公式；规则只提供框架，具体判断要结合图片实际内容
2. **三维度独立** — 结构完美但不适合当背景 → Visual Suitability 仍打 No
3. **背景适用性的核心问题** — "在这张图上叠加一行文字消息，能清楚读吗？"
4. **Structural Integrity 是 prompt-relative** — prompt 要求的奇异结构不算缺陷
5. **Alignment 需理解 prompt** — 模糊 prompt 给予合理创意空间

---

## 时间模型与风控

### 数学约束

```
Total (600s) = Active + Inactive
Inactive <= Active × 10%
∴ Active ≈ 545s, Inactive ≈ 55s（上限）
TPT = 从 task 开始 → 点击 "Next Task"（不是 → 点击 Submit）
```

### 脚本策略

- **bridge.js** 全生命周期管理：keepalive + 计时 + 弹窗处理 + Next Task 自动点击
- 交互间隔：4-9 秒随机（非均匀）
- 注入 2-3 次 **深度睡眠**（15-18s），模拟人类阅读/思考停顿
- 深度睡眠中点有一次微移动，确保每段不超过 9s 无交互
- 实际 Inactive ≈ 40-50s，安全在红线以内
- 单题 TPT 在 555-660s 之间随机波动（均值贴近 600s）
- 点击 Next Task 后立即恢复 keepalive（过渡期间不断交互）
- 自动处理 Disclaimer / Task Overview / No Tasks 等弹窗

### 使用方法

```bash
# 前台运行（可看到实时进度条）
node VCGtexttoimage/bridge.js

# 后台持续运行
node VCGtexttoimage/bridge.js --daemon --log VCGtexttoimage/runs/bridge.log

# 自定义 TPT + 限制题数
node VCGtexttoimage/bridge.js --target 600 --max 20
```

**信号说明：**
- `⚡ SUBMIT NOW` — 已到 80% TPT，应该提交答案
- `✓ Submission detected` — 检测到已提交，继续保活等待 TPT 满
- `🚀 Clicking Next Task` — TPT 到达，自动点击 Next Task
- `⏸ No tasks available` — 没有更多题，退出

---

## 参考教程文件

| 文件 | 用途 |
|------|------|
| `GRADING_RULES.md` | 全维度评分速查手册 |
| `rules/09_visual_suitability_background.md` | 背景适用性评分规则 |
| `rules/01_structural_integrity.md` | 结构完整性详细规则 |
| `rules/04_alignment.md` | 输入输出对齐详细规则 |
| `rules/08_sbs_comparison.md` | 侧对比规则 |
| `VCG_July2025_培训教程中文总结.md` | VCG 通用培训总结 |
| `03_VCG_Base_Creation_Model_v26_04_28_中文详细总结.md` | Base Creation 完整中文教程 |
| `rca_apr15_ocr.txt` / `rca_apr09_raw.txt` | RCA 常见错误反馈 |
