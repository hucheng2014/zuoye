# Intelligent Polls 判题检查清单

## Step 1: Should a poll exist?
- 只有 shared decision / consensus intent 才该生成 poll
- 纯建议/推荐/个人选择 = 不该生成 → proper_no_reply
- 已达成共识 = 不该生成 → proper_no_reply

## Step 2: Parse poll
- Title:
- Options:
- Empty response? → 如果不该生成且为空 = proper_no_reply

## Step 3: Extract candidate options from conversation
- 按首次出现顺序列出所有明确提到的选项
- 排除已被 rejected / 已达成共识的

## Step 4: Dimension ratings (独立判定！)

### Following Instructions
- generate/no-generate 是否正确
- 基本结构：有title + ≥2 unique options
- **不受 Groundedness/Comprehensiveness 影响**

### Composition
- 标题是否自然、简洁（非完整问题）
- 选项是否简洁（非冗长描述）
- 语法、语义一致性
- typo → composition 问题

### Comprehensiveness  
- 所有明确提到的有效选项是否都包含
- 是否保持首次出现顺序
- 遗漏选项 = comprehensiveness 问题（不是 groundedness）

### Groundedness
- title 和每个 option 是否被对话支持
- 幻觉选项 = ungrounded
- **遗漏选项 ≠ ungrounded，那是 comprehensiveness**

### Localization (value="yes"=无问题, value="no"=有问题)
- zh_CN: 检查中文表达是否自然

### Harmfulness
- 安全性 only

### Satisfaction
- 整体结果质量

## Step 5: Boundary cases checklist
- [ ] inappropriate poll generated
- [ ] empty response when poll not needed
- [ ] merged options (e.g. "pizza and burgers" as one)
- [ ] empty option
- [ ] hallucinated option
- [ ] omitted option
- [ ] repeated option  
- [ ] rejected option included
- [ ] consensus already reached
- [ ] advice/recommendation instead of group decision
- [ ] title is a full question (composition issue)
- [ ] options not in first-mention order

## Radio value mapping
- proper_no_reply: yes_reply | no_reply
- following: following_instructions | not_following_instructions
- composition: good | bad
- comprehensiveness: comprehensive | not_comprehensive
- groundedness: truthful | not_truthful
- localization: yes(=无问题) | no(=有问题)  ← 反直觉！
- harmfulness: not_harmful | maybe_harmful | harmful
- satisfaction: highly_satisfying | satisfying | slightly_satisfying | not_satisfying
