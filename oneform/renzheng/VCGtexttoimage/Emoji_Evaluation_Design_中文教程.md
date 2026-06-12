# Emoji Evaluation Design — 中文教程

## 1. 任务目标

本任务属于 Visual Content Generation（视觉内容生成）评估项目。总体目标是判断机器生成内容是否符合输入请求或 prompt。生成物可能包括文本、草图、emoji 等；本项目专门评估 **生成的 emoji 图像**。

评估时你会看到：

- **Input Prompt（输入提示词）**；
- **Output Image(s)（输出 emoji 图像）**；
- **Reference Emojis（参考 emoji）**：这些是 Apple 已有的、与 prompt 中人物或物体相关的 emoji，例如粉色爱心、笑哭、合十等；某些 prompt 可能没有参考 emoji。

你的任务是结合通用 **Image Evaluation Guidelines** 和本项目规则，评估输出 emoji 是否高质量、是否符合 prompt、是否像一个可用的 Apple 风格 emoji。

---

## 2. 需要使用的 Flags（标记）

如果适用，应给输出图像添加以下标记。具体定义参考通用 Image Evaluation Guidelines。

| Flag | 何时考虑 |
|---|---|
| **Inappropriate** | 输出包含不适宜内容。 |
| **Sensitive** | 输出涉及敏感主题、敏感人群或需要谨慎处理的内容。 |
| **Stereotype** | 输出强化刻板印象或以不当方式呈现群体特征。 |

> 这些 flag 与质量评分不同：即使图像结构好、对齐 prompt，也可能因为内容问题需要标记。

---

## 3. 评分维度

每个输出 emoji 主要从以下维度评估：

1. **Structural Integrity（结构完整性）**
2. **Input/Output Alignment（输入/输出一致性）**
   - **Text-to-Image Alignment（文本到图像一致性）**
   - **Image-to-Image Alignment（图像到图像一致性，如果有参考图或参考 emoji）**

---

## 4. 结构完整性 Structural Integrity

### 4.1 核心判断

结构完整性评估 emoji 是否视觉上完整、自然、没有明显缺陷。需要关注：

- 是否存在明显变形、伪影、破碎、融合错误；
- 主体部件是否合理，例如手、脚、尾巴、脸、身体比例；
- 物体形状是否符合常识，例如虾不应长出螯、猫脸不应一侧严重扭曲；
- 是否符合 emoji 风格，尤其是 Apple emoji 的清晰、圆润、可识别视觉语言；
- 分割后的边缘是否干净，是否有误切、缺块或背景残留。

### 4.2 问题等级理解

- **No Structural Integrity Issue**：没有可见缺陷，主体清楚自然，适合作为 emoji。
- **Minor Structural Integrity Issue**：有轻微瑕疵，但不严重影响识别或整体质量，例如手部有小伪影。
- **Noticeable Structural Integrity Issue**：明显缺陷，会影响观感或主体真实性，例如猫脸右侧明显扭曲、冰淇淋甜筒不完整。
- **Severe Structural Integrity Issue**：严重错误，主体类别或结构基本不成立，例如把虾画成虫，或虾长出不该有的螯。

---

## 5. 输入/输出一致性 Input/Output Alignment

### 5.1 核心判断

输入/输出一致性关注 emoji 是否表达了 prompt 要求。检查：

- 主体是否正确；
- 是否包含 prompt 中关键对象；
- 动作是否正确；
- 场景是否被表达；
- 属性是否正确，例如颜色、帽子、气球、冲浪板、森林、阳光等；
- 如果 prompt 要求全身、数量、特定关系，是否满足。

### 5.2 对齐等级理解

| 等级 | 含义 |
|---|---|
| **High** | 输出准确表达 prompt 的核心要求，关键元素齐全。 |
| **Moderate** | 大体相关，但有关键元素弱化、部分缺失或表达不充分。 |
| **Low** | 输出与 prompt 明显不符，主体错误或缺失关键上下文。 |

---

## 6. 排名 Ranking Scale

需要根据已评估的维度比较并排序各输出图像，重点参考：

- 结构完整性；
- 文本到图像一致性；
- 图像到图像一致性；
- flag 情况；
- 是否整体像一个可用、清楚、自然的 emoji。

通常优先选择：

1. 没有严重内容风险；
2. 结构完整；
3. 高度符合 prompt；
4. 风格接近 Apple emoji；
5. 细节简洁、可识别。

---

## 7. 评论要求 Leave a Comment

需要写简洁、具体、结构清晰的评论，向工程师说明你的判断过程。

推荐评论结构：

1. 先说明结构完整性；
2. 再说明 prompt 对齐情况；
3. 如有 flag 或特殊问题，明确指出；
4. 给出最终排序/评分理由。

示例表达：

- “The emoji has no visible structural defects and clearly depicts the requested subject, so alignment is High.”
- “The output is structurally acceptable, but it misses the bamboo forest context, so alignment is Moderate/Low.”
- “The hand contains minor artifacts, but the prompt is still clearly represented.”

---

## 8. 背景分割特别说明

某些评估项目需要检查人物或物体是否从背景中正确分离。此时工具 UI 会把 emoji 放在 **纯绿色背景** 上，帮助你发现：

- 边缘误切；
- 背景残留；
- 主体缺块；
- 不自然的透明区域；
- 分割后被错误挖掉的区域。

规则：

- 绿色背景可以当作白色背景处理；
- 在评估 input-output alignment 时，如果 prompt 提到 beach、forest、city 等背景元素，需要判断这些元素是否被输出 emoji 保留；
- 不要因为背景是绿色就认为 prompt 中的场景缺失；绿色只是 UI 用来检查分割的辅助背景。

---

## 9. 典型示例总结

### 9.1 “An emoji of rainbow flag heart shaped”

- **结构完整性**：No Structural Integrity Issue。
- **原因**：emoji 没有明显缺陷，准确表达用户意图，风格接近 Apple Emoji。
- **对齐**：High。

### 9.2 “yellow shrimp”

| 情况 | 结构完整性 | 对齐 | 原因 |
|---|---|---|---|
| 虾长出螯，只显示虾头 | Severe | Low | 虾通常应呈现完整身体，且虾不应有螯，这是结构伪影。 |
| 输出像虫而不是虾 | Severe | Low | 主体类别错误。 |
| 蛇和虾融合 | Noticeable | Low | 结构上像混合生物，偏离真实虾。 |

### 9.3 “An emoji of a cat wearing sunglasses”

- 如果猫脸右侧明显扭曲：**Noticeable Structural Integrity Issue**，但如果仍清楚是戴墨镜的猫，对齐可为 **High**。
- 其他无明显缺陷版本：**No Structural Integrity Issue**，对齐 **High**。

### 9.4 “A giant panda practicing Tai Chi in a serene bamboo forest”

| 情况 | 结构完整性 | 对齐 | 原因 |
|---|---|---|---|
| 熊猫打太极，但没有竹林 | No issue | Low | 缺少关键场景“serene bamboo forest”。 |
| 熊猫打太极并拿着竹子，但没有完整森林氛围 | No issue | Moderate | 部分表达竹元素，但没有充分表达森林。 |
| 熊猫、太极、竹林氛围都清楚 | No issue | High | 关键对象、动作和场景均满足。 |

### 9.5 “a blob-face wearing a Christmas hat and holding balloons”

| 情况 | 结构完整性 | 对齐 | 原因 |
|---|---|---|---|
| 抱抱 blob-face 拿着气球，但没有圣诞帽 | Noticeable | Moderate | 气球存在，但帽子缺失。 |
| 圣诞帽几乎被紫色气球挡住 | Noticeable | Moderate | 帽子元素过弱，几乎不可见。 |
| blob-face、圣诞帽、气球都清楚 | No issue | High | 准确表达 prompt。 |

### 9.6 “a dog with full body surfing on the sea on a sunny day”

| 情况 | 结构完整性 | 对齐 | 原因 |
|---|---|---|---|
| 只显示狗脸 | No issue | Low | 缺少全身、冲浪、海、晴天等关键上下文。 |
| 狗和冲浪板相关，但场景表达弱 | No issue | Moderate | 与冲浪相关，但 prompt 完整信息不足。 |
| 狗在海上冲浪，但晴天不明显 | Minor issue | Moderate | 主体和动作基本正确，但 sunny day 元素不突出。 |
| 全身狗在晴天海上冲浪 | No issue | High | 准确表达 prompt。 |

### 9.7 其他示例

| Prompt | 结构完整性 | 对齐 | 备注 |
|---|---|---|---|
| a kid wearing a backpack | No issue | High | 主体和背包清楚。 |
| a boy holding a balloon | No issue | High | 男孩和气球关系清楚。 |
| a man holding a kitten | Minor issue | High | 手部有少量伪影，但语义清楚。 |
| a rainbow ice-cream | Noticeable | Moderate | 甜筒不完整；prompt 要一个冰淇淋，输出却显示两个。 |
| bowl of oatmeal with blueberries | No issue | High | 燕麦和蓝莓清楚。 |
| a bathroom with a shower and a toilet | Minor issue | Moderate | 左侧马桶形状不佳，且出现两个马桶；左侧更应是浴缸/淋浴元素。 |
| a bicycle with a basket full of flowers | No issue | High | 自行车、花篮准确。 |
| a candle on a shelf | No issue | High | 蜡烛和架子清楚。 |
| person wearing a bowler hat | No issue | High | 人和圆顶礼帽清楚。 |
| a person giving a presentation | No issue | High | 演示动作/场景清楚。 |

---

## 10. 快速检查清单

提交前检查：

- [ ] 是否先看了 prompt，再看输出？
- [ ] 是否参考了 reference emojis，但没有盲目要求输出完全复制参考 emoji？
- [ ] 是否检查了结构缺陷、伪影、部件错误？
- [ ] 是否确认 prompt 中关键对象、动作、场景、属性都被表达？
- [ ] 若有绿色背景，是否把它当作分割检查辅助，而不是实际 prompt 背景？
- [ ] 是否应用了 Inappropriate / Sensitive / Stereotype flag（如适用）？
- [ ] 评论是否简洁、具体，并能解释评分/排序依据？
