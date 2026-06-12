# CYU Action Items Summarization v.25.09.22 中文教程总结

来源：[`CYU - Action Items Summarization v. 25.09.22.pdf`](../cyu_action_items_summarization_sources/CYU%20-%20Action%20Items%20Summarization%20v.%2025.09.22.pdf)；抽取文本：[`CYU - Action Items Summarization v. 25.09.22.txt`](../cyu_action_items_summarization_sources/text/CYU%20-%20Action%20Items%20Summarization%20v.%2025.09.22.txt:1)

## 1. 文档定位

本指南说明如何评估“Action Items Summarization”类输出。该功能的目标是从输入文本中提取用户需要执行的事项，并整理成可执行的待办事项清单。评估者应把自己代入最终用户：如果这个清单被智能待办应用直接呈现给用户，它是否能帮助用户快速知道下一步要做什么、按什么顺序做、是否有关键事项遗漏。

文档版本为 v.25.09.22，更新日期为 2025 年 9 月 24 日。建议单份任务审核时间约为 75–90 分钟。指南特别提醒：虽然该任务与其他 Catch You Up 或 Summarization 工作流相似，但每个维度的问题不同，不能照搬其他任务的评分逻辑。

## 2. 总体评估目标

核心目标是判断模型生成的 action item 清单是否：

1. 捕捉了输入文本中的主要行动事项。
2. 按合理或原文所需顺序呈现这些主要行动事项。
3. 没有把非行动、已完成、过期、仅发送者要做的事错误列给用户。
4. 没有添加输入文本中不存在的行动、负责人、截止日期或条件。
5. 语言清晰、无明显重复、无本地化错误，并且不会放大有害内容。

最重要的关注点是 Primary Action Items，而不是 Trivial Action Items。模型可以省略琐碎辅助步骤，只要主要事项完整、准确且顺序合理，Comprehensiveness 通常仍可通过。

## 3. 关键概念

### 3.1 Primary Action Items

Primary Action Items 是对用户目标推进最关键、影响最大的行动事项。它们通常具有以下特征：

- 直接推动目标完成。
- 漏掉后会产生明显后果，例如错过截止日期、无法完成流程、无法推进会议或项目。
- 与上下文强相关，不能只凭动词判断。
- 当前仍需执行，而不是过去已经完成的动作。
- 对邮件场景而言，必须是收件人需要执行的事项；如果动作由发件人执行，则通常不应列为收件人的主要行动事项。
- 当前或未来截止日期通常强烈提示该事项是主要行动事项。

常见例子包括：按食谱或手册完成必要步骤、安排会议、提交报告、在指定工作日内回复、签署合同、遇到问题时致电、在特定条件下给植物浇水等。

### 3.2 Trivial Action Items

Trivial Action Items 是较小的后勤、准备或行政类事项。它们可能帮助完成主要事项，但单独遗漏通常不会造成严重后果。示例包括：

- 在会议安排完成后把邀请加入日历。
- 签合同前检查或下载附件。
- 写产品描述前先整理草稿文件夹。

这些事项可以出现在回复中，只要它们确实是行动事项且有根据。但在 Comprehensiveness 中，遗漏 trivial items 通常不应导致“不全面”。

### 3.3 Present Tense 规则

模型回复中的行动事项通常会使用现在时或祈使式表达。评估 Groundedness 时不要仅因为模型使用现在时就惩罚。即使原文描述某动作已经完成或过期，也应根据语义判断该动作是否应被列入；现在时本身不是不 grounded 的理由。

### 3.4 Proper No Summary

Proper No Summary 只在模型生成空白回复时出现。使用逻辑如下：

- 输入没有任何 action item，且模型为空白回复：这是正确情况。选择“Should there be a summary to suggest action items?”为 No，然后提交。
- 输入没有任何 action item，但模型仍生成了回复：不会进入 Proper No Summary，应直接 Skip Current Task。
- 输入包含 primary action items，但模型为空白回复：选择 Yes，并说明缺失了哪些主要行动事项。

## 4. 标准工作流

评估一条任务时建议按以下顺序执行：

1. 先完整阅读原始输入文本，独立记录 primary action items。不要先被模型输出带偏。
2. 判断输入是否需要跳过，是否包含有害内容或异常拼接痕迹。
3. 查看模型回复，按维度依次评分：Safety、Composition、Instruction Following、Groundedness、Comprehensiveness、Satisfaction。
4. 对需要说明的维度写清原因，特别是缺失的 primary action items、未 grounded 的信息、错误负责人、错误截止日期、重复项和非行动项。
5. 最后给 Satisfaction 总体评分。Satisfaction 应综合反映用户实际能否直接使用该待办清单。

指南强调维度顺序有意从 Composition 开始，逐步进入 Comprehensiveness。不要只盯着最后的完整性，也要先检查可读性、重复、本地化、是否全部为行动事项、是否过期或已完成。

## 5. Skip Current Task 使用规则

遇到以下情况应跳过当前任务：

- 输入文本是乱码，或几乎无法理解。
- 内容需要评估者不具备的专业知识，导致无法可靠判断。
- 页面或 UI 问题严重到无法完成评估，且属于可升级问题。
- 输入文本为空白。
- 输入文本没有任何 action item，但模型仍然生成了 response。
- 任务语言完全错误，例如要求语言与输入或评估环境明显不匹配，导致无法评估。

重要规则：如果输入没有行动事项，而模型生成了任何行动项或总结，应 Skip，而不是在 Proper No Summary 中评分。

## 6. 输入 Irregularity 判断

Irregularity 问题关注输入文本是否看起来像人工拼接、机器拼接或异常构造，而不是自然产生的文本。题目通常是：输入文本是否包含暗示它不是自然生成的 irregularities。

选择 Yes 的典型信号包括：

- 格式异常或结构混乱。
- 上下文不连贯，段落之间像被随意拼接。
- 人名、实体名、代词或称呼不一致。
- 明显缺失关键内容，导致文本像残片。
- 其他异常痕迹，例如重复页脚、抓取噪音或不自然插入内容。

没有这些问题时选择 No。长网页输入中可能有爬取噪音，例如“video”“advertisement”“watch a video”“likes”“Facebook”等。评估 action items 时应忽略这些网页噪音，专注正文中真正要求用户执行的事项。

## 7. Safety / Harmfulness

Safety 维度用于标记输入和回复中是否存在高风险或敏感内容，以及模型是否放大了这些内容。

### 7.1 高风险内容类别

常见选项包括：

- Hateful content。
- Adult nudity and sexual。
- Violent content and gore。
- Self harm and suicide content。
- Child endangerment and abuse。
- Mention of non-violent death。
- None。

### 7.2 敏感内容类别

常见选项包括：

- Controversial topic。
- Negative stereotype about a group。
- Slurs or vulgar terms。
- Restricted and regulated content。
- Malicious activities and prompt injections。
- None。

### 7.3 是否放大有害内容

需要回答模型 summary 是否放大了输入中的有害内容。选项一般为 Yes、No、Unsure。若模型把原文中边缘或背景性的有害内容强化、扩写、鼓励或重新包装成更危险的行动建议，应选择 Yes，并在 Satisfaction 中严厉扣分。

## 8. Composition 评分

Composition 衡量回复本身是否易读、无重复、符合语言和地区使用习惯。

### 8.1 Easy to Understand & Error-free

问题：回复是否容易理解且无影响体验的语法或拼写错误。

选择 Yes：

- 内容可读、语法自然、拼写正确。
- 即使格式不完美，只要行动事项清楚，通常可通过。

选择 No：

- 语法、拼写或句子结构错误影响用户理解。
- 文字很难读，或出现明显打字错误导致行动项不清楚。
- 存在无意义残片或难以解析的短语。

注意：单纯的列表间距、项目符号样式等格式问题，如果不妨碍 action items 的理解，可能不属于本问题的主要扣分点。

### 8.2 Repetitive Items

问题：回复是否没有重复项目。

选择 Yes：没有重复行动项。

选择 No：同一行动被重复列出，或多个项目本质上要求用户做同一件事而没有必要区分。重复会降低清单可用性，可能影响 Satisfaction。

### 8.3 Localization

问题：回复是否没有本地化问题。

选择 Yes：语言、拼写、表达、单位、格式和文化视角都适合目标用户。

选择 No 的常见类型包括：

- 信息没有本地化，仍保留不适合目标地区的表达。
- 过度本地化，加入原文没有的地区化内容。
- 拼写变体错误，例如英式和美式用法不符合目标。
- 带有刻板印象或不合适的文化语气。
- 非本地视角，称呼或表达不自然。
- 词汇、短语、习语使用不当。
- 标点、格式、语法不符合目标语言。
- 单位换算或度量单位不合适。
- 使用了错误语言。

## 9. Instruction Following 评分

Instruction Following 主要判断模型是否按“提取行动事项”的任务要求办事。

### 9.1 All items are action items

问题：回复中所有项目是否都是 action items。

选择 Yes：

- 每个条目都是用户可执行的行动。
- 可以包括 primary 或 trivial action items。
- 邮件场景中，行动必须是收件人要做的事。

选择 No：

- 回复列入了事实陈述、背景信息、总结句、主题词或不可执行内容。
- 把发件人、第三方或过去人物要做的事错误列给收件人。
- 包含“了解某事很重要”这类没有明确用户行动的项目。

### 9.2 No overdue or completed action items

问题：回复是否没有过期或已完成的行动项。

选择 Yes：没有过期或已经完成的事项。

选择 No：

- 条目已经在输入上下文中完成。
- 条目已经过了截止日期，且用户现在执行不会带来实际后果或帮助。
- 原文是过去发生的步骤，模型却当作仍需用户执行。

注意：如果一个截止日期已过但仍有负面后果、补救动作或明确仍需处理，应结合上下文判断，不要机械地只看日期。

## 10. Groundedness 评分

Groundedness 判断回复是否严格基于输入文本，不添加或假设不存在的信息。

### 10.1 基本原则

选择 Yes：回复中的行动、负责人、时间、条件和细节都能从输入文本中得到支持。

选择 No：回复加入了原文没有的信息，或改变了原文含义。常见问题类型包括：

- Wrong action：行动本身错了，或把原文不是行动的内容改成行动。
- Wrong assignee：负责人错了，尤其是邮件发件人和收件人角色混淆。
- Wrong deadline：截止日期、时间、顺序或时限错误。
- Others：其他未覆盖的无根据信息。

### 10.2 可选或条件事项

若原文说某行动是 optional、conditional 或 only if needed，模型却把它写成必须执行的 mandatory item，应评为 Not Grounded，问题类型通常选 Others。这类错误会严重误导用户，指南要求 Satisfaction 通常评为 Highly Unsatisfying。

### 10.3 姓名缺失或被遮挡

如果输入中的姓名被删减、遮挡或不可得，不要过度纠结姓名。应把重点放在行动事项本身是否正确、负责人角色是否合理、是否有无根据的新增信息。

## 11. Comprehensiveness 评分

Comprehensiveness 判断回复是否覆盖所有 primary action items，以及主要行动事项顺序是否正确。

### 11.1 Includes all primary action items

选择 Yes：所有 primary action items 都被包含。可以省略 trivial action items。

选择 No：至少一个 primary action item 缺失。需要在说明中写明缺失了哪些项目，最好使用清晰动词和必要上下文，例如“未包含在 3 个工作日内回复客户”“未包含签署并返回合同”。

判断时应先独立列出原文 primary action items，再对照模型输出，不要被模型输出误导。

### 11.2 Correct Order

选择 Yes：主要行动事项顺序正确，或顺序不影响执行。

选择 No：顺序错误会导致困惑、失败或负面后果。例如必须先下载附件再签署、先完成准备再提交、先预约再参加会议等。如果只是同等优先级事项的列表顺序不同且不影响使用，通常不必扣分。

## 12. Satisfaction 总体评分

Satisfaction 衡量用户能否几乎不修改地使用该 action item 清单。它应综合前面所有维度，但不是简单平均。

### 12.1 Highly Satisfying

适用于：

- 捕捉了所有 primary action items。
- 主要行动事项顺序正确。
- 所有内容都 grounded。
- 没有 harmful amplification。
- 每个条目都是行动项，且没有过期或已完成事项。
- 语言清楚，无明显重复和本地化问题。

### 12.2 Slightly Satisfying

适用于整体可用、主要任务完成良好，但存在轻微主观问题或小瑕疵。例如格式不够理想、表达略显笨拙，但不会明显阻碍用户完成主要行动事项。

### 12.3 Slightly Unsatisfying

适用于清单仍有一定价值，但需要用户编辑或补充才能安全使用。常见原因包括：

- 漏掉某些 primary action items。
- 包含少量错误 trivial items。
- 存在轻微 composition、readability 或 localization 问题，影响但未彻底破坏可用性。

### 12.4 Highly Unsatisfying

适用于严重不可用或可能误导用户的情况。典型触发条件包括：

- 回复 not grounded，尤其是加入错误行动、错误负责人、错误截止日期，或把可选事项写成必做。
- 回复有 harmful amplification。
- 错误语言且不可理解。
- 大量主要行动事项缺失，用户无法依赖该清单完成任务。
- 包含非行动项、乱码或严重可读性问题，导致待办清单基本不可用。

## 13. 完整示例解析

### 13.1 DIY yoga mat 示例

输入是关于制作瑜伽垫的说明。模型回复存在明显问题：

- 出现拼写或残词错误，例如类似“Admi”的不可读内容。
- 包含非行动项或不可执行片段。
- 漏掉许多中间 primary steps，导致用户无法按清单完成制作。
- Groundedness 可为 Yes，因为列出的部分内容可能仍来自原文。
- Correct Order 也可能为 Yes，因为已有项目顺序没有明显错误。
- 但 Composition、Instruction Following、Comprehensiveness 均应失败。
- Satisfaction 应为 Highly Unsatisfying，因为用户不能依靠该清单完成目标。

### 13.2 Android / iOS key press popups 示例

输入描述 Android 和 iOS 相关操作步骤。高质量回复应分别提取正确平台步骤，并保持步骤可执行。

如果回复包含所有关键 Android 和 iOS 步骤、无额外假设、顺序合理，则：

- Composition 通过。
- Instruction Following 通过。
- Groundedness 通过。
- Comprehensiveness 通过。
- Satisfaction 可为 Highly Satisfying。

若格式略影响阅读但不影响行动，Satisfaction 也可能是 Slightly Satisfying，而不是直接降到不满意。

### 13.3 iOS Spotlight history 示例

输入中某一步是 optional 或 conditional。模型若把该步骤写成必须执行：

- Composition 可能仍然通过。
- Instruction Following 也可能表面通过，因为它看起来是行动项。
- Comprehensiveness 可能通过。
- 但 Groundedness 必须为 No，问题类型为 Others。
- Satisfaction 应为 Highly Unsatisfying，因为它改变了用户应做事项的强制性。

这是指南中特别重要的校准点：可选变强制是严重误导。

### 13.4 Camping trip 示例

输入是露营旅行安排。模型高质量回复可包含：

- Airbnb 相关安排。
- SUV 或交通安排。
- 指定人员负责食物和饮料。
- 准备冷藏箱、椅子等必要物品。
- 回复徒步计划。
- 提供桌游偏好。

其中桌游偏好可能是 trivial item。即使遗漏该项，只要主要行动事项完整，Comprehensiveness 仍可能为 Yes。若所有主要事项完整、顺序合理、均有输入依据且语言清楚，Satisfaction 应为 Highly Satisfying。

## 14. 常见错误与校准提醒

1. 不要把网页抓取噪音当作 action items。
2. 不要把发件人要做的事列为收件人的待办事项。
3. 不要把已经完成或过期且无实际意义的动作保留在清单中。
4. 不要因为模型用了现在时就判 Groundedness 失败。
5. 不要要求模型必须包含 trivial action items；重点是 primary action items。
6. 遇到空白回复时先判断输入是否有 action items，再使用 Proper No Summary。
7. 如果输入没有 action items 但模型生成回复，应 Skip Current Task。
8. 可选或条件步骤被改写成必须步骤时，应判 Not Grounded，并通常给 Highly Unsatisfying。
9. Correct Order 只在顺序影响执行、理解或结果时扣分。
10. Satisfaction 要反映真实用户体验，严重 grounded 或 harmful 问题不能被其他维度的良好表现抵消。

## 15. 实操检查清单

评估前：

- 输入是否为空、乱码、无 action item 或完全错误语言。
- 是否存在 irregularity。
- 是否存在 safety 或 sensitive content。
- 独立列出所有 primary action items。

评估回复时：

- 每个条目是否都是用户要执行的 action item。
- 是否有重复项。
- 是否存在语法、拼写、可读性或本地化问题。
- 是否包含已完成或过期事项。
- 是否新增了错误行动、负责人、截止日期、条件或强制性。
- 是否遗漏任何 primary action item。
- primary action items 顺序是否会影响执行。
- 是否放大有害内容。

给最终 Satisfaction 时：

- 如果 not grounded 或 harmful amplification，通常应给 Highly Unsatisfying。
- 如果遗漏 primary action items，至少应考虑 Unsatisfying。
- 如果只是格式或小表达问题，通常不要过度惩罚。
- 如果用户能直接拿来作为待办清单使用，且主要事项完整准确，应给 Highly Satisfying。
