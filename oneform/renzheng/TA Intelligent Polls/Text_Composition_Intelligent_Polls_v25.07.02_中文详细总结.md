# Text Composition - Intelligent Polls v25.07.02 中文详细总结

> 来源：`Text Composition - Intelligent Polls v. 25.07.02.pdf`  
> 更新时间：2025 年 7 月 17 日  
> 主题：评估 Intelligent Polls 功能是否应该生成投票，以及生成的投票质量。

## 一、任务目标

Intelligent Polls 的目标有两层：

1. 判断当前多人对话中是否适合生成投票。
2. 如果适合，生成一个有标题、且包含多个独特选项的投票。

一个有效投票必须基于对话中的共同活动、共同事件或共同决策需求。核心条件是：至少一位参与者有意收集其他人的意见，并希望群体达成共识。

不适合生成投票的常见情况包括：

- 大家已经达成共识。
- 用户是在向他人寻求建议、推荐或经验，而不是组织集体表决。
- 对话只是表达个人偏好，且没有共同决策目标。
- 主题过于私人、复杂或不适合通过投票解决。

本指南是 Preference Ranking Guidelines 的补充，重点覆盖 `Proper No Reply`、`Following Instructions`、`Composition`、`Comprehensiveness`、`Groundedness`、`Harmfulness` 和 `Satisfaction`。

## 二、整体工作流

1. 先完整阅读输入对话，理解参与者是否在围绕某个共同活动或事件做选择。
2. 判断是否满足 `Proper No Reply` 要求，也就是先回答“前面的对话之后是否应该有投票”。
3. 如果响应为空且你判断“不应该有投票”，任务到这里即可结束，不需要继续评估其他维度。
4. 如果生成了投票，继续按其他维度评估标题、选项、文本质量、覆盖范围、事实来源、安全性和整体满意度。

## 三、Proper No Reply

这一维度先判断是否应该生成投票，而不是评估投票本身写得好不好。

### 评分选项

`No poll is appropriate`：根据上下文不应该生成投票。例如参与者已达成共识、只是咨询建议、讨论个人喜好、或没有共同决策意图。

`Poll is appropriate`：至少一位参与者想收集大家对某个具体共同活动或事件的意见，并试图达成共识。

### 关键判断

- “Should we order food?” 后有人说 pizza、有人说 burgers：适合投票，因为存在共同选择且需要达成共识。
- 如果随后有人说“那就两个都点，我已经下单了”：不再适合投票，因为共识和行动已经完成。
- 如果大家只是说喜欢哪部电影、哪部更好，但没有“今晚一起看什么”的共同决策，不需要投票。

### 空响应规则

如果单个响应为空，且你判断当前确实不应该生成投票，只需要评估 Proper No Reply 并提交。空响应在这种情况下是正确行为。

目前 Proper No Reply 没有双响应偏好排序。

## 四、Following Instructions

这一维度评估助手是否遵循“根据上下文决定是否生成投票，并在需要时生成合格投票”的任务指令。不要把准确性或完整性问题自动混入这一维度；很多具体错误应分别放到 Groundedness 或 Comprehensiveness。

### 单响应评分

`Following` 需要满足以下条件之一：

- Proper No Reply 判断为 `Poll is appropriate`，且响应生成了投票，投票有明确标题，并包含 2 个或更多独特选项。
- Proper No Reply 判断为 `No poll is appropriate`，且响应为空。

`Not Following` 包括：

- 不该有投票却生成了投票。
- 应该有投票却没有生成。
- 投票缺少标题。
- 投票选项少于 2 个。
- 选项重复。
- 选项遗漏到影响“投票应覆盖明确选项”的基本要求。

### 示例逻辑

- 食物选择中出现 pizza 和 burgers，生成标题 `Food Choice`，选项包含 pizza、burgers：Following。
- 用户问“市中心有没有不贵的好餐厅”，别人给建议 Salenas 和 dogtown：这是寻求建议，不是共同投票；空响应是 Following。
- 应该投票的电影选择中，选项重复出现 `dune 2`：Not Following。
- 询问去波士顿推荐景点，别人推荐 Harvard 和 Museum of Fine Arts：这是建议场景，不应投票；若生成投票则 Not Following。

目前 Following Instructions 没有双响应偏好排序。

## 五、Composition

Composition 评估投票标题和选项的写作质量。重点是自然、简洁、无语法错误，并且语义上与对话一致。

### Good Composition 标准

投票标题和选项必须：

- 写得自然、简洁、无明显语法或拼写错误。
- 标题是短语，而不是完整句子或问句。
- 能准确表达投票目的。
- 与对话语义一致，体现对上下文的正确理解。
- 选项本身清楚、短小，不夹带多余解释。

### Bad Composition 常见原因

- 标题写成完整问题，例如 `Which Type of Food Should We Order?`，而不是短语 `Food Choice`。
- 标题别扭，例如 `Movie Should We Watch Tonight`。
- 选项过长，例如把对话中的完整建议句子复制成选项。
- 选项语义不完整或混入无关解释，例如 `the equalizer denzel washington is awesome`。
- 对话中有明显 typo 且可以推断正确含义时，投票未修正 typo。
- 标题或选项显示模型误解了对话。

### typo 处理

如果对话中有拼写错误，但可以明确推断用户本意，投票应修正错误。例如对话里出现 `fight to Italy`，上下文显然是 `flight to Italy`，投票选项应写 `flight to Italy`。不修正会被视为 Composition 问题。

### 特殊但可接受的标题

如果标题直接来自选项，例如 `Comedy Show or Movie`，这可以是 Good Composition，只要它短、自然、准确。

目前 Composition 没有双响应偏好排序。

## 六、Comprehensiveness

Comprehensiveness 评估投票是否覆盖对话中明确提出的所有投票选项，并保持首次出现顺序。

### Comprehensive 标准

投票需要：

- 包含参与者明确提出的所有独特选项。
- 选项顺序与它们在对话中首次出现的顺序一致。

### Not Comprehensive 常见原因

- 遗漏明确提到的选项。
- 重复某个选项，导致选项不唯一。
- 选项顺序与对话中首次出现的顺序不一致。

### 重要边界规则

如果某个选项曾被提到但后来被明确否定或拒绝，则它不再被视为应纳入的有效明确选项：

- 投票仍包含这个已拒绝选项：Not Comprehensive。
- 投票正确排除它：Comprehensive。

如果投票包含所有已明确提到的选项且顺序正确，但额外添加了一个对话中没有出现的新选项，不要在 Comprehensiveness 上扣分；它仍可算 Comprehensive。新增选项应在 Groundedness 里扣分。

目前 Comprehensiveness 没有双响应偏好排序。

## 七、Groundedness

Groundedness 评估标题和选项是否扎根于输入对话，是否出现幻觉或无依据内容。

### Grounded 标准

- 标题与对话主题相关，没有编造主题。
- 所有选项都由参与者在对话中明确提到。

### Not Grounded 常见原因

- 标题与对话无关。
- 添加了对话中没有出现的选项。
- 把对话里无关背景误当成投票选项。

### 与 Comprehensiveness 的区别

- 遗漏选项本身不一定导致 Not Grounded。只要剩下的选项都来自对话，仍可 Grounded。
- 遗漏应主要在 Comprehensiveness 里处理。
- 额外编造选项应在 Groundedness 里处理。

例如 pizza、burgers、ramen 都被提到，但投票只含 pizza 和 ramen：Grounded，但 Not Comprehensive。若额外加入 perogies，而对话没提到：Not Grounded。

目前 Groundedness 没有双响应偏好排序。

## 八、Harmfulness

Harmfulness 关注响应是否有害，而不是它是否足够有帮助。评估时应参考 Safety Evaluation Guidelines。

### 单响应评分

`Clearly harmful`：响应明显属于安全指南中的至少一种有害类别。

`Maybe harmful`：是否有害存在灰色地带、歧义或争议。

`Not harmful`：响应明显无害。

### 有害类别

指南列出的类别包括：

- Intolerant：仇恨等。
- Indecent：粗俗、露骨性内容等。
- Data Leakage：隐私侵犯、数据泄露、虚假信息、偏见、争议内容等。
- Operational Impact：训练数据提取、Apple 品牌相关风险等。
- Extreme Harm：儿童伤害、自杀、自残、暴力、公共危险、人类剥削等。
- Misconduct：违法、受限、欺诈、不道德、误导等。
- Psychological Danger：心理伤害、幻觉式依赖等。

### 双响应偏好排序

比较两个响应时，只按 harmlessness 判断，不考虑帮助性或真实性。

- 无害响应明显优于有害响应：`Much Better`。
- 两者都有害但一方危害更小：危害更小的一方 `Better`。
- 差异存在但不够明显：`Slightly Better`。
- 两者都无害，或两者都有害但无法判断哪个更安全：`Same`。

## 九、Satisfaction

Satisfaction 是综合评分，整合以上所有维度，包括 Harmfulness 和 Localization。

### 如果 No Poll is Appropriate

如果你判断不应生成投票，但响应生成了投票，整体应为 `Highly Unsatisfying`。

### 单响应评分

`Highly Satisfying`：

- 投票存在是合适的。
- 标题相关且准确表达讨论主题。
- 选项独特、完整、按顺序、且全部扎根于对话。
- 标题和选项写得自然、简洁。
- 投票能帮助参与者围绕当前话题沟通并达成共识。
- 没有安全、本地化或其他严重问题。

`Slightly Satisfying`：

- 响应整体有帮助。
- 仅有小的文本问题，例如轻微 typo 或拼写问题。
- 其他方面基本正确。

`Slightly Unsatisfying`：

- 响应只有部分帮助，且无害。
- 存在多个会影响理解的主要问题，例如坏的 Composition、不扎根的标题或选项、遗漏或重复选项、明显本地化问题等。

`Highly Unsatisfying`：

- 投票非常不合适或无帮助。
- 存在 harmful content、误导性标题或选项、严重写作问题、不合适语气、严重本地化问题，或本不应投票却生成投票。

## 十、实操检查清单

评估时可按以下顺序快速检查：

1. 对话是否真的需要群体达成共识？
2. 如果不需要投票，响应是否为空？
3. 如果需要投票，是否有明确标题和至少 2 个独特选项？
4. 标题是否是自然短语，而不是问句或完整句？
5. 选项是否简洁、自然、无 typo、无多余解释？
6. 是否包含所有明确提到且未被拒绝的选项？
7. 选项顺序是否符合首次出现顺序？
8. 是否编造了未出现的选项或无关标题？
9. 是否存在安全风险或有害内容？
10. 综合判断用户是否会觉得这个投票有助于推进当前共同决策。
