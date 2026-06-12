# WT Rewrite Follow-Ups IAA Feedback 中文反馈文档

> 来源：`WT_Rewrite FollowUps_IAA feedback_08May.pdf`  
> 页数：3 页  
> 主题：基于 IAA（Inter-Analyst Agreement，分析员间一致性）反馈，校准 Rewrite Follow-Ups 任务中最容易产生分歧的评分步骤和维度。

## 1. 文档背景

本反馈基于 IAA，也就是不同分析员评估同一任务时的一致程度。文档中的观察和反馈按最常复现的问题排序：越靠前，代表一致性越低、越需要重点注意。

Rewrite Follow-Ups 中主要风险集中在：

- Step 2 的 Personalization
- Step 3 的 Grammar & Clarity、Tone Appropriateness
- Step 4 的 Follow-up Suggestions
- Step 5 的 Suggestion Adherence、Meaning Preservation、Quality Improvement
- Localization

## 2. Personalization — Step 2

这是跨 locale 风险最高的维度，一致性经常低于 40%。

评估者需要注意：

- 样例输出并不是映射 to 真实用户本人；它们只是在展示一种写作风格模式。评估时必须只关注风格信号，例如句子长度、词汇复杂度、正式程度标记等。
- 不要因为样例输出和 rewrite 在事实内容上不同就处罚。Step 2 关注的是风格，而不是样例内容和 rewrite 内容是否事实一致。
- **Well matched** 不代表 rewrite 必须和样例输出一模一样，而是 rewrite 稳定体现同一类风格。
- 如果整体是随意风格，只出现一个偏正式词汇，不应因此直接降到 **Partially matched**。
- 对亚洲和欧洲 locale 来说，“formal”“casual”“advanced vocabulary”等判断带有文化差异。评估时要锚定该任务给出的样例输出，而不是使用自己对这些标签的文化默认值。

核心判断：rewrite 是否稳定呈现与样例相同的风格类别，而不是是否逐词模仿样例。

## 3. Fix Errors — Step 3 Grammar & Clarity

该维度在亚洲 locale 的一致性明显下降，在欧洲 locale 中也不稳定。指南中的问题看似是简单的 yes/no，但实际分歧说明评估者执行得不一致。

评估者需要注意：

- 第一个问题只问：原文中已有的错误是否被修复。
- 对语法规则复杂或“错误”边界较模糊的语言，例如中文中标点或字词选择可能存在争议，欧洲语言中有性数一致等问题，需要先做二元判断：输入里是否存在明确错误？rewrite 是否修复了它？
- 如果原文没有明确语法错误，应标 **Not applicable**，而不是 **Yes**。
- **Not applicable** 很可能被使用得不够。原文没有语法错误时，答案是 N/A，不是 Yes；混淆这两项会放大一致性问题。
- Q1 不问 rewrite 是否引入了新错误；这是 Q2 的范围。
- Q1 也不问 rewrite 整体是否写得好；这是 Q3 的范围。
- Q2 评估是否引入了新错误。如果原文中的错误没有被修复，这是 Q1 失败，不是 Q2 失败。

核心判断：Q1 看“旧错是否修复”，Q2 看“是否新增错误”，不要互相替代。

## 4. Preserve Style — Step 5 Meaning Preservation Q2

该维度询问：第二个 rewrite 是否保留了第一个 rewrite 中那些没有被所选 suggestion 目标覆盖的风格元素。欧洲 locale 和 tone 相关 suggestion 中，一致性持续偏弱。

评估者需要注意：

- 关键词是 **unrelated**。要先在脑中隔离所选 suggestion 的目标，例如 `Soften tone`。
- 隔离目标后，再检查其他内容是否仍与第一个 rewrite 保持一致，例如词汇选择、句子结构、正式程度、长度等。
- 只有那些与 suggestion 目标无关的区域发生变化，才算 Preserve Style 失败。
- 常见错误是处罚应用 suggestion 的自然副作用。例如 soften tone 可能轻微改变句子结构，这是可以接受的。
- 如果 suggestion 只是要求简洁，但第二个 rewrite 却从正式词汇完全变成随意词汇，这不是自然副作用，应判为问题。
- 对欧洲 locale 来说，tone_balance 本身也弱，说明评估者容易混淆 tone 与 style。Tone 是情绪色彩和自信程度；Style 是结构和词汇模式。这两个问题在 rubric 中是分开的，必须分别评估。

核心判断：只处罚与所选 suggestion 无关的风格漂移，不处罚必要且合理的连带变化。

## 5. Apply Suggestion — Step 5 Suggestion Adherence Q1

该维度在各 locale 中都比较容易出问题，尤其当所选 suggestion 涉及 tone 或 register 时。

评估者需要注意：

- 标准是：suggestion 是否被明显执行，并且是否产生了与 suggestion 直接相关、可看出的变化。
- 可以把第一个 rewrite 和第二个 rewrite 并排比较：如果能立刻看出 suggestion 的效果，应标 **Yes**。
- 对 `Keep it natural`、`Preserve informal tone` 这类宽泛 suggestion，不要要求文本发生彻底改造。
- 对宽泛 suggestion，应寻找至少 2-3 个具体标记，例如用词、句首表达、缩写、标点风格等，确认它们确实体现了 suggestion。
- 对 tone 相关 suggestion，不同 locale 的正式程度规范差异很大。应按照本 locale 的沟通习惯判断，而不是按照英语语境的规范判断。

核心判断：要看到 suggestion 的直接效果；效果可以是具体标记的累积，不一定是大幅改写。

## 6. Negative Side Effects — Step 5 Quality Improvement Q2

该维度在欧洲和亚洲 locale 中都不稳定。

评估者需要注意：

- 只有当应用 suggestion 后引入了清晰、具体的新问题时，才应把该问题视为 negative side effect。
- 不要因为自己更喜欢另一种表达，就判定存在负面副作用。
- 判断门槛是：文本现在是否出现了原本没有的问题？
- **Lost nuance** 只有在有意义的区别被移除时才应标记，例如限定词、缓和语、重要 caveat 被直接删掉。
- 示例：原句是 `I understand why they made the decision, though I still think it was shortsighted`，rewrite 变成 `I think they made a bad decision`。后者删除了“理解对方决定”的缓和和 nuance，因此应视为丢失细微含义。
- 像 `Add more detail` 这类 suggestion 造成长度增加是预期结果，不是负面副作用。
- 只有当长度真正过度时，才把长度视为问题。
- 某些 rewrite 为了完成 suggestion 必然需要轻微改写或长度变化。例如从 20 个词变成 22 个词，不应自动处罚。

核心判断：negative side effect 必须是新增的真实问题，而不是个人偏好或合理的改写代价。

## 7. Redundancy — Step 4 Follow-up Suggestions

指南对 Redundancy 的定义很清楚：两个或更多 suggestion 几乎相同，或覆盖了相似信息。但该维度一致性仍然较弱，尤其在欧洲 locale 中。

评估者需要注意：

- **Similar information** 指的是：如果选择这些 suggestion，得到的第二个 rewrite 本质上会相同。
- 两个 suggestion 可以使用不同措辞，但只要指向同一改写方向，仍可能 redundant。
- 例如 `Keep it brief` 和 `Cut unnecessary words` 是 redundant，因为它们都会导向压缩冗余内容。
- `Keep it brief` 和 `Soften the tone` 不是 redundant，因为一个关注长度，一个关注语气。
- 可以对每一对 suggestion 做心理测试：选择 A 和选择 B 后，第二个 rewrite 是否会产生有意义差异？如果不会，它们就是 redundant。

核心判断：看 suggestion 造成的改写结果是否实质不同，而不是只看字面措辞是否不同。

## 8. Tone Balance — Step 3 Tone Appropriateness Q2

该维度在法语、德语、西班牙语、意大利语中明显偏弱。指南问的是：在满足情境要求的同时，用户个性是否仍然体现出来。这本身有强烈文化因素。

评估者需要注意：

- 这个问题不是问 rewrite 听起来是否自然。
- 它问的是 rewrite 是否在用户已展示的写作风格与当前情境要求之间取得平衡。例如，一个平时随意的人在写工作邮件时，既要保留一定个人风格，也要符合工作场景。
- 欧洲 locale 的职业沟通规范差异很大：法语职业写作通常偏正式，德语通常偏直接，西班牙语可能更温暖。
- 评估 situational appropriateness 时，应按本 locale 的规范校准，而不是使用泛化标准。
- 样例输出是理解用户基础风格的主要参考。
- 如果 rewrite 在没有明确情境理由的情况下明显偏离用户风格，应判失败。
- 如果风格偏移有上下文理由，例如写给上级、提出正式请求，则可以通过。

核心判断：Tone Balance 不是单纯自然度，而是“用户风格”和“场景要求”的平衡。

## 9. Localization

* Writing Tools 指南有自己的 Localization 规则。评估时必须使用 Writing Tools 的规则，不要引用 LE 指南作为判断依据。
* 同时，不要把拼写或语法问题报告到 Localization 下。Spelling/Grammar 与 Localization 是不同维度。

## 10. 实操自检清单

评估 Rewrite Follow-Ups 时，可按以下顺序快速自检：

1. Step 2 只看风格匹配，不看样例和 rewrite 的事实内容差异。
2. Step 3 Q1 看旧错误是否修复；没有明确旧错误时用 N/A。
3. Step 5 Preserve Style 只处罚与 selected suggestion 无关的风格变化。
4. Apply Suggestion 要能看到直接效果，宽泛 suggestion 至少找 2-3 个具体标记。
5. Negative Side Effects 只标新增的具体问题，不按个人偏好处罚。
6. Redundancy 看两个 suggestion 是否会产生实质不同的 second rewrite。
7. Tone Balance 按本 locale 的职业沟通规范和样例风格校准。
8. Localization 使用 Writing Tools 规则，不混入 LE 规则或 Grammar/Spelling 问题。
