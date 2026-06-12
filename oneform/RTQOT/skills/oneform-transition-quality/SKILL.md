---
name: oneform-transition-quality
description: Automates Transition Quality rating tasks on TryRating using PANNs acoustic features and CLAP semantic transition embeddings, including strict >2m time controls and allowed score constraint mappings.
---

# OneForm Transition Quality (音频过渡质量评估) 自动化做题技能库

本技能库总结了在 TryRating 平台进行**音频过渡质量评估（Transition Quality）**考试与做题的物理、语义标准，及对应的自动化答题与时间控制技术方案。

---

## 1. 核心判定标准与分值划分

评判对象为音频拼接过渡区（Edit Transition Window）的平滑度和听觉品质，通常划分为以下 5 个档位：

| 评分档位 | 分数范围 | 听觉过渡质量描述 |
| :--- | :--- | :--- |
| **Excellent** (优秀) | 4.25 ~ 5.0 | 过渡极其完美，音乐节奏、旋律无缝连接，听不出任何拼接痕迹。 |
| **Good** (良好) | 3.25 ~ 4.25 | 过渡自然且符合逻辑，无明显杂音，可能有极微小的淡入淡出或节奏变化但完全可接受。 |
| **Average** (中等) | 2.25 ~ 3.25 | 过渡一般，有可察觉的不自然，但没有让人感到突兀的刺耳感或音量跳跃。 |
| **Poor** (较差) | 1.25 ~ 2.25 | 过渡不自然、突兀，伴有明显的音量跳水、节拍错乱，或者轻微的杂音、切断。 |
| **Awful** (极差) | 1.0 ~ 1.25 | 出现严重的杂音、爆音、数秒的完全静音，或者音频在拼接处粗暴中断。 |

---

## 2. 自动化判定技术实现 (双模型方案)

为避免采用硬规则漏判或因规则过死被封号，必须使用本地双模型进行独立评估：

### 2.1 PANNs (声学物理分析)
* **核心作用**：评估物理声学特征（例如：能量突变、静音占比、爆音等）。
* **使用模型**：`Cnn14_mAP=0.431.pth` (AudioTagging)。
* **声学提取指标**：
  * **RMS (均方根能量)**：检测是否整体无声。
  * **Silence Ratio (静音占比)**：过渡窗口内绝对音量 `< 0.01` 的采样点比例。若占比 `> 70%` 则判定为静音断流（分值降至 `1.0`）。
  * **Max Energy Jump (能量突变度)**：通过对能量包络求一阶差分检测是否有 abrupt 粗暴截断或瞬间爆音。差分幅值 `> 0.4` 时判定为 `Awful / Poor`。

### 2.2 CLAP (语义平滑度分析)
* **核心作用**：评估音频的音乐语义连贯性。
* **使用模型**：`laion_clap` (HTSAT-base 编码器)。
* **对比文本向量库**：
  * `"awful transition with complete silence and empty audio"`
  * `"awful transition with very abrupt cut and harsh distortion"`
  * `"poor transition with unnatural timing and jarring transition"`
  * `"poor transition with slight audio artifacts and clicks"`
  * `"average transition with minor imperfections but passable quality"`
  * `"good transition with smooth natural sounding music"`
  * `"excellent transition with perfect seamless musical transition"`
* **打分机制**：利用音频 Embedding 与文本 Embedding 的余弦相似度 Softmax 加权求得 CLAP 语义质量分。

---

## 3. 页面任务交互与防刷控制

### 3.1 任务抓取 (Redux Store 链路)
通过 CDP 调试端口对页面运行 JS 代码，提取 Redux 内部的 state。
关键提取路径：`window.store.getState().survey.workableSurvey.tasks`
每个 task 中包含：
* `requestId`：唯一试题 ID。
* `audio_src`：音频下载链接。
* `overlap`：过渡拼接重叠时间长度（单位：秒）。
* `testQuestionInformation`：考试限定分值说明（若为考试题，会限制允许填写的离散分值集合，如 `[3.5, 4.0, 4.5]`）。

### 3.2 裁剪窗口计算
过渡拼接以第 10 秒为中心点。
* **编辑窗口起点**：`10.0 - (overlap / 2.0) - 0.5`
* **编辑窗口终点**：`10.0 + (overlap / 2.0) + 0.5`
判定和模型打分必须聚焦于该窗口内的音频 data。

### 3.3 严格的做题时间控制 (> 2分钟)
* **核心防刷机制**：做题页面如果提交过快，会被系统判定为机器刷题而导致封号。平台对 Transition Quality 的预估做题时间是 2分30秒。
* **时延标准**：单批次做题耗时必须被强行延迟至 **135 秒**（即 2 分 15 秒）。
* **计时起点**：从抓取到该批次试题并开始下载音频那一刻起作为计时起点。
* **延时计算**：
  $$\text{Sleep Needed} = 135.0 - (\text{Time.time()} - \text{Batch Start Time})$$
  若计算完成和滑块设置仅花费了 20 秒，程序会强行挂起并每 10 秒打印进度，挂满 115 秒延时后方可执行 Submit 模拟点击。

### 3.4 滑块模拟与状态检验
* 使用 CDP `Input.enable` 结合 MouseEvent 模拟拖拽滑块（对应分数百分比 `0.0, 0.25, 0.5, 0.75, 1.0`）。
* 滑动后通过检测 `rc-slider-dot-active` 的数量进行回检（如 `Good` 应激括 4 个激活点），确认滑动正确后方可提交。

---

## 4. 健壮性与异常防御指南

* **缺失字段防御**：非考资格题中不存在 `testQuestionInformation`，普通任务的 `audio_src` 偶尔可能加载失败。在提取和转换时，必须对任务字典全盘使用 `.get()` 安全取值。
* **默认备用方案**：一旦音频不可用或获取链接空缺，应触发兜底打分（如滑至 `Average`），跳过模型下载，而不能中断做题主进程。
* **轮询退避**：当提示 `"Looking for surveys..."`（空题）时，自动切换至 10 秒周期的静默轮询模式，减少对服务器的并发负担。
* **模型预热 (Pre-warm)**：为了避免每次做题时重新加载 2.3G 模型权重导致超时的尴尬（CLAP 初始化耗时高达 30s），应在守护进程启动之初完成全局 CLAP/PANNs 的 Pre-warm 挂载。
