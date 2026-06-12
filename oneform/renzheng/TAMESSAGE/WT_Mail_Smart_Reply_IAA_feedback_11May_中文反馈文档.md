# WT Mail Smart Reply IAA Feedback 中文反馈文档

> 来源：`WT_Mail Smart Reply_IAA feedback_11May.pdf`  
> 页数：2 页  
> 主题：基于 IAA（Inter-Analyst Agreement，分析员间一致性）反馈，校准 Mail Smart Reply 任务中最容易产生分歧的评分维度。

## 1. 文档背景

本反馈基于 IAA，也就是不同分析员评估同一任务时的一致程度。文档中的观察和反馈按问题复现频率排序：越靠前，代表一致性越低、越需要重点校准。

本次 Mail Smart Reply 反馈中，风险最高的维度主要是：

- **Personalization（个性化）**
- **Groundedness（依据性/扎根性）**
- **Instruction Adherence & Contextual Fit（指令遵循与上下文适配）**
- 对 zh-CN、zh-HK 来说，**Localization（本地化）** 也是高风险维度。

## 2. Personalization（高风险）

这是数据中最普遍、最严重的问题。评估者需要重新校准如何判断回复是否真正 Personalized。

指南明确要求，Personalized 回复必须能体现用户的写作风格模式，包括：

- 词汇选择
- 格式习惯
- 铺垫或表达长度习惯
- 句子结构
- Mail Component Patterns：称呼、开场、结尾、sign-off、签名等邮件组成习惯
- 双方关系语境

一个回复即使功能上正确，只要使用了泛泛的称呼、错误的 sign-off，或遗漏了用户一贯的格式习惯，都应评为 **Generic**，而不是 Personalized。

关键校准点：

- 用户画像描述的是倾向，不是死板规则；判断时要看是否有有意义的风格对齐，而不是只做表面检查。
- 如果用户画像显示 `strong_formatting`，而 prompt 明确要求列表或结构化内容，但草稿完全没有列表或结构，应评为 **Generic**。
- 如果草稿使用了和用户画像完全不同的 sign-off，例如画像常用 `Thank You`，草稿却写 `Thanks`，这也会把评分推向 **Generic**。
- 需要判断整体感觉：这封回复是否像这个特定用户本人会写的，还是任何人都可能写出来？

校准时应重点参考指南 Step 6 的示例，尤其是 Marija 示例中 Reply 1（Personalized）与 Reply 2（Generic）的对比。该示例清楚展示了什么叫“缺失风格元素”，也更接近任务中常见的真实场景。

## 3. Groundedness（高风险）

v1.3 更新引入了三档评分：

- **Grounded**
- **Partially Grounded**
- **Not Grounded**

新的 **Partially Grounded** 档位尤其容易被误用或忽略。评估者需要明确区分轻微虚构和严重无依据内容。

关键规则：

- 标准职业礼貌语通常应视为 **Grounded**，不要处罚。例如 `Thanks for checking in`、`Hope you are doing well`、普通寒暄和常规结尾。
- 如果草稿的核心信息正确，但加入了一个轻微虚构细节，例如 prompt 中没有的具体时间、编造的时长、并不存在的先前对话引用，应评为 **Partially Grounded**，不是 Not Grounded。
- 如果草稿引入的虚构事实改变了消息含义，或带入完全无关的话题，应评为 **Not Grounded**。
- Rule 5 特别重要：如果收件人姓名在输入的任何位置都找不到，包括 prompt、先前邮件、用户画像、附加信息等，只要核心信息正确，应评为 **Partially Grounded**，不是 Not Grounded。
- 只要姓名能在任务任一位置找到，即使它和用户指令相矛盾，也应按 **Grounded** 处理。例如 prompt 写“Email Mark...”，但画像中有 `John`，回复以 `Hi John` 开头，这属于 **Grounded**，但在 Contextual Fit 上应视为不匹配。

原则：**Not Grounded 只留给明确失败。核心信息正确但有轻微编造细节时，应使用 Partially Grounded。**

## 4. Instruction Adherence & Contextual Fit（高风险）

该维度也采用三档尺度，因此同样存在校准风险。不要把本应是 **Partially Followed and Fit** 的回复过重地评为 **Not Followed** 或 **Misfit**。

关键规则：

- 如果草稿完成了主要指令，但遗漏了次要元素，应评为 **Partially Followed and Fit**。
- 如果草稿回应了先前邮件中的大部分关键点，但没有覆盖全部关键点，应评为 **Partially Followed and Fit**。
- 如果只是轻微的正式程度不匹配，也通常属于 **Partially Followed and Fit**。
- **Not Followed** 或 **Misfit** 只用于更严重的情况，例如缺少关键要素、直接违背指令、正式程度差距明显。
- 明显正式的职业邮件线程中使用过于随意的语气，是可能达到 Misfit 的情况。

如果任务中有先前邮件，必须把指令遵循和上下文适配放在一起评估。一个回复可能表面上遵循了 prompt，但没有回应先前邮件的关键点；这种情况最高也只能是 **Partially Followed and Fit**。

## 5. Locale-Specific Issues（语言地区特定问题）

### zh-CN 与 zh-HK

对 zh-CN 和 zh-HK 来说，Localization 是高风险维度，这一点比较特殊。评估时要特别注意：

- 简繁体或脚本层面的问题
- 中文标点格式错误
- 不符合中文书面表达习惯的格式

不要套用 LE certification 的本地化规则。Writing Tools 有自己的 Localization 规则，应以 Writing Tools 指南为准。

同时，语法和拼写问题不属于 Localization，不要把 Grammar/Spelling 错误报告到 Localization 维度下。

### 其他 locale

多数其他 locale 的 Localization 风险为中等。仍需严格按照对应指南判断，不要按个人感觉放宽或加严。

### vi-VN

vi-VN 的 Naturalness 也被标为高风险，这在其他 locale 中不常见。问题可能是模型输出语法上可以接受，但读起来像翻译腔或生硬的越南语。

评估 Naturalness 时，核心问题不是“语法是否正确”，而是“这是否像一个真实的人用该语言自然写出来的”。

## 6. What's Working - Don't Overcorrect

Harmful 和 Tone 在所有 locale 中整体都是低风险维度。评估者不应因为其他维度风险高，就强行在这些维度中寻找问题。

Tone 只有在存在明确不匹配时才应评为 **Not Aligned**，例如：

- 对方表达沮丧或不满时，回复显得冷淡、机械。
- 明确正式的职业语境中，回复语气过于随意。

如果语气整体适合上下文，就应通过 Tone 维度。

## 7. 实操自检清单

评估 Mail Smart Reply 时，可按以下顺序快速自检：

1. 先判断回复是否真的像该用户本人会写，而不只是内容正确。
2. 对 Groundedness 使用三档思维：核心正确但轻微编造时，不要直接判 Not Grounded。
3. 同时看 prompt 和先前邮件：回复不能只满足指令，却忽略邮件上下文。
4. 对 zh-CN、zh-HK 特别检查文字系统、标点和中文格式习惯。
5. 不要过度处罚 Harmful 和 Tone；只有明确问题才降级。
