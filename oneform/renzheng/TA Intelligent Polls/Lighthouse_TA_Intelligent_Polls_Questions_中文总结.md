# Lighthouse_TA Intelligent Polls_Questions 中文总结

> 来源：`Lighthouse_TA Intelligent Polls_Questions.pdf`  
> 主题：Intelligent Polls 评分中的常见问题与工程方澄清。

## 一、文档定位

这份 Questions 文档是对主评分指南的 FAQ 补充，重点澄清四类容易误判的场景：

1. 不应该生成投票且响应为空时，其他维度是否需要扣分。
2. 不应该生成投票但响应生成了投票时，Comprehensiveness 如何评估。
3. Following Instructions 是否会被 Groundedness 或 Comprehensiveness 自动影响。
4. 投票格式和标点是否必须严格遵循示例格式。

## 二、No poll is appropriate + 空响应

如果已经选择 `No poll is appropriate`，且模型响应为空，这表示模型行为正确。

评分要点：

- 不要因为响应为空而惩罚任何维度。
- 空响应是预期结果。
- 不应把这种正确的空响应在后台标记成低质量结果。
- 该场景下的判断应与主指南一致：不应投票时不生成投票就是正确行为。

## 三、No poll is appropriate + 非空投票响应

如果你判断不应该有投票，但模型仍生成了投票，需要继续尽力评估生成内容本身的各个维度，尤其是 Comprehensiveness。

工程方澄清：

- 即使你已经判断“不该有投票”，仍应按照 Comprehensiveness 指南判断该投票是否覆盖了对话中可识别的明确选项。
- 这类场景可能看起来很奇怪，因为投票本身已经不合适，但维度仍要尽量独立评估。
- Following Instructions、Composition、Groundedness 等也应根据各自规则判断。
- 从主指南看，不该投票却生成投票会让整体 Satisfaction 走向 Highly Unsatisfying，但这不代表所有子维度都自动失败。

实操理解：

- 先记住“生成投票”本身是错误行为。
- 再看这个错误投票内部是否写得好、是否扎根、是否覆盖明确选项。
- 不要因为 Proper No Reply 错误就停止评估所有可评估维度，除非界面流程要求停止。

## 四、Following Instructions 与其他维度的独立性

问题背景：主指南提到，如果投票遗漏选项或重复选项，可能导致 `Not Following`。评分者担心这是否意味着 Comprehensiveness 或 Groundedness 会自动影响 Following Instructions。

工程方澄清：

- 不要建立“某选项不 grounded，所以一定 Not Following”的自动连接。
- 指南没有写这种自动推导，因此不能这样评分。
- 一个投票可以有标题和 2 个或更多选项，因此在结构上满足 Following Instructions；但它的标题或选项仍可能不 grounded。
- 各维度应独立评估，不要让一个维度的判断污染另一个维度。

实操规则：

- Groundedness 只处理标题和选项是否来自对话。
- Comprehensiveness 只处理是否覆盖所有明确选项并保持顺序。
- Following Instructions 只按本维度定义判断是否遵循生成/不生成投票和基本结构要求。
- 如果确实存在重复、缺标题、选项不足等本维度明示问题，再判 Not Following。
- 不要仅因“幻觉选项”就自动判 Not Following；应至少在 Groundedness 中扣分。

## 五、格式与标点不必完全照搬示例

问题背景：主指南示例常用如下格式：

```text
Title:
XXX
Options:
- XXX
- XXX
```

工程方澄清：

- 投票不需要严格遵循示例中的格式和标点。
- 如果指南没有明确规定某种标点，不应因为标点不同而惩罚。
- 但投票必须有明确标题和明确选项集合。
- 真正要评估的是标题和选项的质量，而不是是否完全复制示例排版。

实操规则：

- 不要因为 `Title:`、`Options:`、短横线、冒号、大小写或标点风格不同就直接扣 Composition。
- 如果标题和选项清楚可识别，格式差异一般不构成问题。
- 如果格式导致标题或选项无法明确识别，则可能影响 Following Instructions 或 Composition。

## 六、综合操作建议

遇到边界案例时，按以下原则处理：

1. 先判断是否应该生成投票。
2. 空响应在“不该投票”时是正确行为，不要额外惩罚。
3. 不该投票却生成投票时，仍尽量独立评估投票内部质量。
4. 不要把 Groundedness、Comprehensiveness 和 Following Instructions 混成一个总判断。
5. 标题和选项必须明确，但格式和标点不必与示例完全一致。
