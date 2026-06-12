# WT Rewrite Follow-Ups IAA Feedback 中文反馈总结

> 来源：`WT_Rewrite FollowUps_IAA feedback_08May.pdf`  
> 主题：基于 IAA（Inter-Analyst Agreement，分析员间一致性）的 Rewrite Follow-Ups 评分校准。  
> 重点：按一致性最低、最容易产生分歧的维度排序，提醒评估者如何统一判断标准。

---

## 1. 文档背景

这份反馈不是重写完整指南，而是针对标注员最容易不一致的评分点进行校准。核心问题集中在：

- Step 2：Personalization
- Step 3：Grammar & Clarity、Tone Appropriateness
- Step 4：Follow-up Suggestions
- Step 5：Suggestion Adherence、Meaning Preservation、Quality Improvement
- Localization

评分时要优先回到任务自身的 rubric，不要按个人偏好、其他项目指南或泛化语言标准替代当前任务规则。

---

## 2. Personalization — Step 2

这是跨 locale 风险最高的维度，一致性经常低于 40%。

关键原则：

- 样例输出只是展示用户写作风格模式，不代表真实用户事实。
- 评估时只看风格信号：句长、词汇复杂度、正式程度、表达习惯等。
- 不要因为样例和 rewrite 的事实内容不同而处罚。
- “Well matched” 不等于逐字相似，而是 rewrite 稳定落在同一风格类别。
- 一个偶发的正式词或随意词，不应把整体风格直接降为 Partially matched。
- 对亚洲和欧洲 locale，要以任务给出的样例为锚点判断 formal/casual/advanced vocabulary，不要套用自己的文化默认值。

一句话：**Personalization 看风格匹配，不看事实内容映射。**

---

## 3. Fix Errors — Step 3 Grammar & Clarity

该维度看似是 yes/no，但实际分歧很大。

需要区分三个问题：

1. **Q1：原文已有错误是否被修复？**
2. **Q2：rewrite 是否引入新错误？**
3. **Q3：rewrite 整体是否清楚、写得好？**

常见误区：

- 如果原文没有明确语法错误，应选 **Not applicable**，不是 Yes。
- Q1 只问旧错是否修复，不问是否新增错误。
- Q2 只问是否新增错误。旧错没修复是 Q1 的问题，不是 Q2 的问题。
- 对中文、欧洲语言等错误边界较模糊的语言，要先判断是否有“明确错误”，不要把可争议风格当作必须修复的错误。

一句话：**旧错、 新错、整体清晰度要分开评。**

---

## 4. Preserve Style — Step 5 Meaning Preservation Q2

该问题要求判断第二个 rewrite 是否保留了第一个 rewrite 中与所选 suggestion 无关的风格元素。

操作方法：

1. 先隔离 selected suggestion 的目标，例如 `Soften tone`、`Make it shorter`。
2. 再检查不属于该目标的部分：词汇、句式、正式程度、长度、结构等。
3. 只有这些“无关区域”发生明显漂移，才判 Preserve Style 失败。

注意：

- 应用 suggestion 的自然副作用可以接受。例如软化语气可能轻微改变句式。
- 如果 suggestion 只是要求简洁，但第二个 rewrite 完全从正式词汇变成口语词汇，这属于无关风格漂移。
- 不要混淆 tone 和 style：tone 是情绪、态度、自信程度；style 是结构、词汇、表达模式。

一句话：**只处罚与 suggestion 无关的风格变化。**

---

## 5. Apply Suggestion — Step 5 Suggestion Adherence Q1

核心标准：selected suggestion 是否被明显执行，并产生了直接相关、可观察的变化。

评分技巧：

- 把第一个 rewrite 和第二个 rewrite 并排比较。
- 如果能明显看出 suggestion 的效果，应选 Yes。
- 对宽泛 suggestion，如 `Keep it natural`、`Preserve informal tone`，不要求大幅重写。
- 对宽泛 suggestion，应寻找 2–3 个具体标记，例如用词、句首、缩写、标点、语气词等。
- 对 tone/register 类 suggestion，要按本 locale 的沟通习惯判断，不要套用英语语境。

一句话：**要看到 suggestion 的直接效果；宽泛建议看具体标记的累积。**

---

## 6. Negative Side Effects — Step 5 Quality Improvement Q2

该维度只应在应用 suggestion 后引入了清晰、具体的新问题时失败。

不要这样误判：

- 不要因为自己更喜欢另一种表达就判 negative side effect。
- 不要把合理的长度增加当作问题，尤其是 suggestion 本身要求 `Add more detail` 时。
- 轻微改写或从 20 词变 22 词，不应自动处罚。

需要处罚的情况：

- 关键 nuance 被删除，例如限定语、缓和语、重要 caveat 消失。
- 文本出现原来没有的明确语法、语义、语气或事实问题。
- 长度真正过度，影响可用性。

一句话：**Negative side effect 必须是新增的真实问题，不是个人偏好。**

---

## 7. Redundancy — Step 4 Follow-up Suggestions

Redundancy 指两个或更多 suggestion 几乎相同，或会产生本质相同的第二个 rewrite。

判断方法：

- 不只看字面措辞，要看选择这些 suggestion 后会得到什么结果。
- 如果两个 suggestion 会导向同一种改写，它们就是 redundant。
- 例：`Keep it brief` 与 `Cut unnecessary words` 冗余。
- 例：`Keep it brief` 与 `Soften the tone` 不冗余，因为一个改长度，一个改语气。

一句话：**看建议带来的改写结果是否有实质差异。**

---

## 8. Tone Balance — Step 3 Tone Appropriateness Q2

该维度在法语、德语、西班牙语、意大利语等 locale 中尤其弱。

问题不是“听起来是否自然”，而是：

- 是否保留用户样例中的个人风格；
- 是否同时满足当前场景的沟通要求；
- 两者之间是否取得合理平衡。

注意：

- 职业沟通规范因 locale 差异很大。
- 法语职业写作通常更正式，德语更直接，西班牙语可能更温暖。
- 如果 rewrite 无理由偏离用户基线风格，应失败。
- 如果偏离是由场景合理要求造成，例如写给主管、正式请求，则可通过。

一句话：**Tone Balance 是用户风格与场景要求的平衡。**

---

## 9. Localization

Writing Tools 有自己的 Localization 规则：

- 不要用 LE 指南替代 Writing Tools 指南。
- 不要把拼写或语法问题放到 Localization 下。
- Localization 主要看语言、地区、文化、格式、表达习惯是否适合目标 locale。

---

## 10. 快速自检清单

1. Personalization 只看风格，不看样例事实是否对应真实用户。
2. Grammar Q1 看旧错是否修复；无明确旧错用 N/A。
3. Grammar Q2 看是否新增错误，不替 Q1 背锅。
4. Preserve Style 只处罚与 selected suggestion 无关的风格漂移。
5. Apply Suggestion 要看到直接效果；宽泛建议找 2–3 个具体标记。
6. Negative Side Effects 只标新增具体问题，不按个人偏好处罚。
7. Redundancy 看两个 suggestion 是否会产生本质相同的改写。
8. Tone Balance 按本 locale 规范和用户样例风格校准。
9. Localization 使用 Writing Tools 规则，不混入 LE 或 grammar/spelling 判断。
