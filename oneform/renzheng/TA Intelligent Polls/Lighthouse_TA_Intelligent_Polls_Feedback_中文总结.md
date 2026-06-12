# Lighthouse_TA Intelligent Polls_Feedback 中文总结

> 来源：`Lighthouse_TA Intelligent Polls_Feedback.pdf`  
> 主题：关于“多个实际选项被合并成一个选项，另一个选项为空”的评分澄清。

## 一、文档定位

这份 Feedback 文档只讨论一个具体边界案例，但它对维度独立性很重要。场景是：实际输入文本中明确有两个选项，例如 Pizza 和 Burgers，但模型输出把两个选项合在同一行，并给出一个空选项。

示例结构：

```text
Title: Food Options

Options:
- Pizza and Burgers
- [empty]
```

## 二、Instruction Following

该示例在 Instruction Following 上表现良好。

原因：

- 它有明确标题。
- 它形式上提供了选项集合。
- 按照指南中 Following 的定义，这不应直接判为失败。

注意：这里的重点是不要因为 Composition 或 Comprehensiveness 的问题自动让 Instruction Following 失败。

## 三、Groundedness

该示例一般也应在 Groundedness 上表现良好。

原因：

- Pizza 和 Burgers 都来自实际输入文本。
- 标题 `Food Options` 与食物选择主题相关。
- 没有明显编造未出现的新选项。

需要注意的是，Groundedness 关心“内容是否来自对话”，不主要关心选项是否拆分得好。

## 四、Composition

该示例在 Composition 上表现差。

原因：

- 两个本应分开的选项被合并成一个选项。
- 第二个选项为空，说明投票结构和文本呈现不自然。
- 这种写法不清晰，会影响用户理解和投票可用性。

因此应按主指南将其视为 Composition 问题。

## 五、Comprehensiveness

Comprehensiveness 在这个例子中是有争议的。

文档给出的判断逻辑：

- 主指南要求选项按照它们在对话中首次出现的顺序呈现。
- 当 `Pizza and Burgers` 被放在同一个选项里时，可以认为它们不是分别按顺序作为投票选项呈现，而是同时混在一起。
- 因此可争论它没有满足 Comprehensiveness 的顺序和选项呈现要求。

实操建议：

- 不要简单认为“两个词都出现了，所以一定 Comprehensive”。
- 要看它们是否作为独立投票选项清楚呈现。
- 如果选项被合并，导致投票无法分别表达两个选择，Comprehensiveness 至少存在明显风险。
- 文档没有给出绝对唯一答案，而是说明该维度可辩论，需要结合主指南和界面要求判断。

## 六、核心结论

这个案例的推荐理解是：

| 维度 | 结论 |
|---|---|
| Instruction Following | 表现良好，不应自动失败 |
| Groundedness | 通常表现良好，因为内容来自输入 |
| Composition | 表现差，因为选项合并且有空选项 |
| Comprehensiveness | 有争议；可认为未按独立顺序呈现选项 |

最大要点：维度应独立评分。一个响应可以在 Instruction Following 和 Groundedness 上可接受，同时在 Composition 上明显失败，并在 Comprehensiveness 上需要谨慎判断。
