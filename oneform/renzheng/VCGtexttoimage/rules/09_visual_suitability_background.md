# Visual Suitability (Message Background) — 评分规则

## 适用场景

当任务说明包含 "these images will be used as the background when users send text messages in the message app" 时，此维度生效。

此维度评估图片作为短信/消息App聊天背景时的视觉适用性，核心关注：**图片是否会干扰叠加在其上的文字阅读**。

---

## Question 1a: 主体是否偏离中心（Subject Off-Center）

**判断标准：** 背景图的主体是否避开了中心区域，从而不遮挡文字显示位置。

| 选项 | 条件 |
|------|------|
| **Yes** | 主体偏离中心且大小适当；或图中没有明显的单一主体 |
| **No, visually disruptive** | 主体居中或过于突出，导致文字难以放置 |
| **Not Applicable** | 背景描绘的是一个场景（如城市、树林、教堂），包含多个物体或多个视角，不存在单一主体问题 |

### 判断要点：
- 有单一明显主体 → 看它是否占据中心
- 主体小且靠边 → Yes
- 主体大且居中 → No
- 没有主体（纯色、渐变、纹理）→ Yes
- 多物体场景（风景、城市天际线）→ Not Applicable

---

## Question 1b: 细节是否简洁（Simple Details）

**判断标准：** 图片作为背景时，细节是否足够少以不干扰文字可读性。

| 选项 | 条件 |
|------|------|
| **Yes** | 图片细节极少，形成干净、不抢眼的背景 |
| **No, too detailed** | 图片繁忙或复杂，背景令人分心 |

### 判断要点：
- 简单渐变、模糊光斑、大面积纯色/低细节区域 → Yes
- 密集纹理、大量细小物体、复杂图案填满画面 → No
- 关键考量：想象在图片上叠加一行白色/黑色文字，是否能轻松阅读

---

## Question 1c: 配色是否简单（Simple Color Scheme）

**判断标准：** 图片作为背景时，颜色是否协调、变化少。

| 选项 | 条件 |
|------|------|
| **Yes** | 颜色均衡简洁，形成统一的背景 |
| **No, too many colors** | 颜色对比过多，视觉上令人分心 |

### 判断要点：
- 单色调、双色调、同色系渐变 → Yes
- 彩虹色、大量高对比色块拼接、霓虹撞色 → No
- 关键考量：颜色变化是否导致无论用什么颜色的文字都难以保持可读性

---

## 与其他维度的独立性

Visual Suitability 独立于 Structural Integrity 和 Input-output Alignment：
- 一张结构完美、完全匹配prompt的图片，如果主体居中且细节繁杂，Visual Suitability 仍然应该打 No
- 一张有轻微结构问题的图片，如果背景干净简洁，Visual Suitability 仍然可以打 Yes

---

## SBS Comparison: Visual Suitability 偏好对比

Compare 阶段的 Question 1 要求综合 1a + 1b + 1c 三个子问题做左右对比：

| 评分 | 含义 |
|------|------|
| Left Much Better | 左图在背景适用性上明显优于右图 |
| Left Slightly Better | 左图略优 |
| About the Same | 两张图背景适用性相当 |
| Right Slightly Better | 右图略优 |
| Right Much Better | 右图明显优于左图 |

综合考量三个子维度的整体表现做出判断。
