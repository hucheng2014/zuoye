# Lighthouse 0 to 1 Composition Feedback 中文反馈总结

> 来源：`Lighthouse_0 to 1 Composition Feedback.pdf`  
> 主题：0-to-1 Composition 新 workflow 的认证/实操反馈，集中说明评分中最容易误判的维度。

---

## 1. 开始前要求

文档提醒：尚未观看该新 workflow webinar 的评估者，应先观看培训再进行第一次尝试。该任务的很多判断依赖对流程和 rubric 的一致理解。

---

## 2. Necessity for Additional Information

“是否需要额外信息”只看完成任务是否真的需要额外条件，包括：

- 用户个人信息；
- 上下文中的关键细节；
- 需要事实核查或网络搜索的信息。

评估前必须仔细理解用户 instruction 和 context。很多任务虽然有更多信息会更好，但没有也能完成，此时不应判为 Critical。

### 典型例子

- `Thank him for reaching out and propose a new meeting time`  
  需要用户的可用时间等个人信息才能合理提出新时间，因此需要额外信息。

- `Tell Ian I’ll check the price for the laptop for Rohan`  
  这是直接回复，不需要更多信息，也没有明显 supplementary need。

- `Ask John to let me know his availability`  
  虽然与时间相关，但用户只是要求询问 John 的可用性，不需要用户自己的可用时间。

核心原则：**Critical information 是完成任务所必需的信息，不是“有了更好”的信息。**

---

## 3. Critical Issue / Hallucination

不要把来自 **Additional Personal Information** 的正确信息判为 hallucination。判断幻觉时，应同时查看：

- 用户输入；
- 上下文；
- Additional Personal Information；
- 必要时可通过一般知识或 web search 核查。

应判 Hallucination 的情况：

- 编造具体姓名、地点、价格、数字、日期、事实；
- 编造需要用户个人信息或外部事实核查才能知道的内容；
- 编造公司流程、政策等任务中没有给出的具体信息。

不应轻易判 Hallucination 的情况：

- 响应写到 `office celebration for the hard work` 这类泛化场景表达，通常不算具体编造；
- 信息能从 Additional Personal Information 找到依据；
- 只是普通背景性措辞，而不是可验证的具体事实。

文档特别提醒：认证中只有一个真正 hallucinated response，但很多人漏判，因此要重点警惕具体、无依据的事实。

---

## 4. Email Subject Evaluation

邮件主题评分采用“选择所有适用项”的方式。如果某个标准不满足，就不要勾选对应选项。

常见问题：

- Topic + action noun 顺序错误，例如 `Request to Meet` 不如 `Meeting Request`；
- 一个 subject 包含多个 topic；
- conjunctions、articles、prepositions 在非首尾位置被错误大写；
- 首词、尾词、名词、动词、副词、形容词没有按 Title Case 大写；
- 主题过于 verbose / detailed，不够概括；
- 主题不够中立、专业，带有夸张或主观营销色彩。

核心原则：**每个 checkbox 对应一个明确标准，不要因为 subject 整体可懂就全选。**

---

## 5. Instruction Following、Tone、Completeness、Length

多数任务在这些维度上比较直观，但仍要抓住少数潜在问题。

### Instruction Following

响应必须：

- 包含用户要求的关键点；
- 与 instruction 直接相关；
- 使用用户要求的格式，如列表、项目符号、邮件、标题等。

### Markdown 格式

输出是 Markdown：

- 用户要求加粗时，应表现为 `**text**`；
- 标题/header 应表现为 `# text`。

### Tone

Tone 要适合受众和上下文。大多数任务是 semi-formal，但也可能出现更 casual 或更 formal 的场景。不要只看语言是否自然，还要看是否符合对象和目的。

### Completeness

Completeness 只看用户要求或上下文中应包含的 critical details：

- 如果用户给了日期、地点、对象、事件等重要信息，遗漏则失败；
- 如果这些信息本来没有提到，不应因为响应没有包含而处罚。

### Length

长度要结合任务要求：

- 若任务本身需要大量内容，不要因为长而处罚；
- 若用户要求简单、简短、concise，但响应加入很多额外细节，可降级。

---

## 6. Helpful Suggestions

Suggestions 的作用是补充 composition，而不是默认都算有用。

应标 Helpful：

- 提供能补充正文的有用想法；
- 补足时间、日期、地点、主题等对写作有帮助的信息；
- 帮助用户让输出更完整或更可执行。

应标 Neutral：

- 建议用户做设备动作，如设置提醒、打电话等，且与 composition 无关；
- 建议内容已经被提供或可能重复；
- 建议虽然相关，但只是泛泛补充。

应标 Missing：

- 明显需要建议补充关键上下文，如时间、日期、地点，但模型完全没有提供。

核心原则：**不要自动把所有 suggestions 视为 Helpful。**

---

## 7. Overall Rating

整体评分应参考工具给出的 suggested rating，但最终仍要按任务复杂度和输出可用性判断。

注意：

- 有些用户指令非常简单，不需要特别有创意或洞察；
- 简单任务如果准确、得体、可直接使用，仍可以评 Excellent；
- 不要因为内容短就自动降低分数，关键是是否满足任务预期。

---

## 8. 快速评分提醒

1. Critical additional information 必须是完成任务不可缺的信息。
2. Additional Personal Information 中的正确信息不是 hallucination。
3. Hallucination 主要看无依据的具体事实、数字、日期、地点、价格、姓名等。
4. 邮件主题逐项勾选，尤其注意 Topic + action noun、Title Case、单一主题和简洁性。
5. 指令遵循要看关键点和格式。
6. Tone 要适合受众和场景。
7. Completeness 只处罚遗漏已给出或必需的关键信息。
8. Length 要结合任务本身，不机械处罚长或短。
9. Suggestions 只有真正补充 composition 时才 Helpful。
10. 简单任务也可以 Excellent，只要完成得准确且可用。
