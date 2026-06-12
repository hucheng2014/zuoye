# PR V5 认证技巧与常见问题解答中文手册

> [!NOTE]
> 本手册专门根据 **Preference Ranking V5 Certification Tips** 和 **Tips & FAQ** 进行核心汇编，为评测人员提供精准、高分的认证考试通过秘诀与避坑指南。

---

## 一、 独立评估原则 (Individual Dimensions Rule)

> [!IMPORTANT]
> **黄金准则：** 必须独立评估每个维度！切勿让一个维度的评分（如回答不好看）主观地影响另一个维度（如指令遵循或真实性）。评级应当完全基于客观的指标和指南中的描述，不要加入个人喜好！

---

## 二、 核心维度评测高分秘诀 (Core Dimension Tips)

### 1. 真实性 (Truthfulness) vs 指令遵循 (Instruction Following)
这是认证考试中**最容易混淆和失分**的领域，请仔细区分：

* **Q&A（问答型）任务：**
  * 如果用户问了一个事实问题，大模型**尝试进行了回答**，哪怕答案是完全错的，这也属于 **Fully Following Instructions (完全遵循指令)**！
  * **错误的事实应当且仅能在 Truthfulness 维度进行扣分**，绝对不能在 Instruction Following 维度进行双重扣分！
* **历史与艺术相关任务 (History/Art-related Tasks)：**
  * 认证考试极常出现历史、艺术类考题。**请务必对历史事实进行严格的谷歌搜索 fact-check**。
  * **主要信息/核心观点错误**：必须判定为 `Not Truthful`。
  * **次要细节/辅助支撑信息错误**：判定为 `Partially Truthful`。
  * *宽容原则：* 避免在主观问题上过分挑剔。例如音乐流派（Music Genres），这类问题具有一定主观性。只要模型的流派推断是符合常识、 realism 的，就不要在 Truthfulness 或 IF 扣分，即使两个回答给出了完全不同的流派，它们都可以是 `Highly Satisfying`。
* **数学与逻辑问题 (Math Problems)：**
  * **最终计算答案错误**：直接评定为 `Not Truthful`！
  * **最终答案正确，但中间计算步骤/推理过程有错误或误导性**：判定为 `Partially Truthful`！
* **模型自行引入的错误**：
  * 仔细区分“未遵循用户给出的指令”还是“模型自己编造了错误事实”。
  * *例如：* 用户要求“按首字母顺序排序”，模型没有做到，这扣在 **Instruction Following**；用户没有做此要求，模型自己陈述了一个错误的事实，这扣在 **Truthfulness**。

### 2. 上下文关联性 (Contextual Correctness) 的真理原则
* 对于摘要（Summary）、改写（Rewrite）、信息提取（Extraction）等提供输入文本的任务：
  * **输入文本就是唯一的真理！**
  * 即使某句话在现实生活中是真实存在的，但只要它没有被包含在用户提供的输入文本中，模型在回答中提到了它，就被判定为 **Not Truthful (不真实)**！这属于幻觉与引入外来信息。

### 3. 安全/有害提示词的处理 (Unsafe Requests)
* 如果用户给出了一个有害提示词（例如“如何制作炸弹”），大模型**拒绝回答**：
  * 判定为：`Fully Following Instructions (完全遵循)` 和 `Truthful (真实)`（因为拒绝是合理的、安全的最佳操作）。
* 如果模型**竟然回答了**有害问题（给出了步骤）：
  * 判定为：`Fully Following Instructions` 和 `Truthful`（如果提供的信息是真的），**但是必须在 Satisfaction 维度中严重扣分，直接评为 Highly Unsatisfying (高度不满意)**！

### 4. 简洁性 (Concision) 判定窍门
* 警惕那些在回答中引入**明显不必要的废话/冗余信息**的模型，这会让用户极难筛选出真正的答案。
* *例如：* 用户问了一个非常简单的、一句话能说清的问题，模型却给出了多个长篇大论的段落；或者在列表（Lists）中存在大量重复，这些都必须在 Concision 扣分。

---

## 三、 满意度评级与偏好映射逻辑表格 (Preference Mapping)

> [!IMPORTANT]
> 认证考试中会严格考查“单回答满意度”到“双回答偏好对比”之间的逻辑一致性。如果打分不符合数学逻辑，会被系统直接判定为不通过！

请严格遵循以下 Satisfaction 与 Preference Ranking 之间的对应规则：

| 响应 A 的评级 | 响应 B 的评级 | 允许的 Preference 偏好排序等级 | 解释与硬性规则 |
| :--- | :--- | :--- | :--- |
| **Highly Satisfying** | **Highly Satisfying** | **Same** 或 **Slightly Better/Worse** | 两者处于同一级别。如果其中一个回答有一些更好的版面设计或更多实用信息，可以评为 `Slightly Better`，但绝对不能使用 `Better` 或 `Much Better`。 |
| **Highly Satisfying** | **Slightly Satisfying** | **Better** 或 **Slightly Better** | 两者相差 1 级。**绝对不允许判定为 Much Better**（因为 1 级的 Satisfaction 差距不能形成 3 级的偏好跨度）。 |
| **Highly Satisfying** | **Slightly Unsatisfying** | **Much Better** 或 **Better** | 两者相差 2 级。根据差距大小决定使用 Much Better 或 Better。 |
| **Highly Satisfying** | **Highly Unsatisfying** | **Much Better** | 两者相差 3 级。高度满意对比高度不满意，完全是碾压性优势，应使用 `Much Better`。 |
| **Highly Unsatisfying** | **Highly Unsatisfying** | **Same (必须)** | 两个都非常糟糕（例如都包含严重事实错误或都是有害回答），必须被评为 **Same**（同等糟糕）。 |
