# VCG Base Creation & Edit Model 工作流信息中文详细总结

来源：[vcg_browser_sources/text/01_VCG Base Creation & Edit Model info.txt](vcg_browser_sources/text/01_VCG%20Base%20Creation%20%26%20Edit%20Model%20info.txt:1)

## 1. 文档定位

本文件是针对 VCG Base Creation 与 Edit Model 两类工作流的补充操作提醒。它不是完整评分指南，而是强调在正式评估前必须遵守的关键校准点。核心目标是避免把旧的 Image Evaluation 或 ADM 规则带入本项目，并提醒标注员严格使用当前新指南。

## 2. 通用工作要求

- 开始阅读指南和执行任务前，先观看提供的录屏。
- Base Creation 与 Edit Model 是两个不同流程，必须分别使用对应的新指南。
- 不要混用过去的图像评估、ADM 或其他项目指南。
- 评估时不要赶进度，也不要凭直觉假设；应放大图像、逐项检查，并按维度独立评分。

## 3. Base Creation 重点规则

### 3.1 模糊与视觉质量

- 只有当整张图或主要可评估内容模糊时，才应把图像标为 blurry。
- 如果只是背景虚化、景深效果或非主体背景模糊，不应直接作为模糊问题处理。
- 对齐和视觉质量应分开：图像是否包含要求内容属于 Input/Output Alignment，图像是否清晰、是否失真属于 Visual Quality 或 Structural Integrity。

### 3.2 Text Quality 是独立维度

- 在 Base Creation 中，Text Quality 是单独维度，不要放到 Structural Integrity 里评估。
- 如果图中出现了应当可读但实际无法读出的文字，无论文字是否由 prompt 要求，都应标为 Low Quality。
- “Can't tell” 只应用于 prompt 要求出现文字，但图中没有显示文字、无法判断文字质量的情况。
- 文字的拼写、大小写、可读性、是否破损或乱码，都应在 Text Quality 中反映。

### 3.3 Low Poly 风格

- Low Poly 输出必须有明确多边形特征。
- 重点看主体是否呈现明显三角形或四边形分面、低面数几何结构和分块着色。
- 仅仅“简化”或“卡通化”不等于 Low Poly。

### 3.4 Photorealism 风格

- Photorealism 表示图像应像真实相机拍摄。
- 评估时关注真实摄影线索：皮肤和材料纹理、光影、透视、景深、色调、表面细节。
- 不要只凭个人感觉判断“好看”或“像 AI”；应依据是否具有真实相机照片的视觉属性。

### 3.5 指南页码问题提醒

- 第 102 页标注为 Egyptian style，但示例图是 Persian paintings。
- 第 103 页标注为 Benin Bronze，但示例图也属于 Persian painting。
- 这些问题已经反馈给客户；标注时不要因页码错误而混淆风格判断。

### 3.6 Diversity Evaluation 注意事项

- 单人图像不评估 apparent ethnicity 与 gender。
- 对群体图像，如果有任意一个人脸不可见、被遮挡、太小、太模糊或无法可靠判断，则 ethnicity 与 gender 两项都应选择 can't determine。
- 例如图中有 5 人，其中 4 人看得出性别呈现，但第 5 人无法看到脸或无法判断，则整体不能强行推断，应选 can't determine。

### 3.7 结构完整性必须细看

- 评估时应点击图像并使用放大功能。
- 对人和动物尤其要仔细检查：脸部五官、眼睛方向、手指数量、手指形状、肢体比例、肢体数量、关节连接。
- 清晰的脸部变形属于 Severe issue。
- 多数明显结构问题不应被降级为 minor；必须根据严重程度严格处罚。

### 3.8 Alignment 必须覆盖全部 prompt 要素

- 评估 Alignment 时必须检查 prompt 中所有对象、动作、属性、关系和场景。
- 如果 prompt 要求 “in a gym”，必须确认场景确实像健身房。
- 如果只出现部分要求内容，应降级到 captures most but not all；如果主要对象错误或缺失，应更严重降级。

## 4. Edit Model 重点规则

### 4.1 Text Quality 属于 Structural Integrity

- 与 Base Creation 不同，Edit Model 中的 text quality 是 Structural Integrity 的一部分。
- 单词图像中出现拼写错误，可以构成 Noticeable issue。
- 字母中有小瑕疵，但整体文字清楚且结构完整时，可视为 minor。

### 4.2 指南缺字与页码问题

- 第 37 页有小段文字缺失，应读作 “…reflecting in the output.”
- 第 64 页也有缺失，应读作 “…thus not a total failure”.
- 第 103 页与第 105 页内容重复，客户已知晓。
- 第 105 页应列出 Fair 或 Poor 图像可选择的 4 个原因，例如 blurry、different output style 等。
- 第 121 页实际讲的是 comments，不是 Usability；第 122 页才是 Usability 内容。

### 4.3 维度可能有交叉，但仍要按要求评估

- 某些视觉质量问题也可能影响 Structural Integrity，例如不合理场景、空间布局、对象逻辑。
- 即便存在维度交叉，也要按项目指南判断该问题主要属于哪个维度。

### 4.4 Edit Model 图像比较流程

- 必须分别评估每张图，先 Left，再 Right。
- 不要把左右图的评价混在一起。
- 对每个维度逐项判断，尤其关注 Structural Integrity、未编辑区域、Character consistency。
- 对人和动物继续严格检查脸、眼睛、手指、肢体比例和数量。

### 4.5 Prompt 动作要求很重要

- Edit Model 中要特别注意 prompt 中要求的是 change、remove、add 还是其他动作。
- 是否正确执行动作会影响 Instructions 与 Alignment 维度。
- 不仅要看最终画面是否好看，还要看是否按要求编辑了正确对象、保留了应保留区域，并满足所有 prompt 元素。

## 5. 被特别提醒的错误示例

对于示例 prompt：

- “a girl and a boy sitting on a life ring”
- 或 “two kids in life jackets”

文档提醒忽略示例中原本给出的 rating suggestions。原建议中的 Minor issues 和 Highly aligned 是错误的：

- Alignment 应该被降级，因为要求内容没有被完整满足。
- Structural Integrity 应该被升级到更高惩罚，因为结构问题比 minor 更严重。

## 6. 实操检查清单

1. 先确认当前任务属于 Base Creation 还是 Edit Model。
2. 使用当前新指南，不使用旧项目规则。
3. 放大图像检查主体、手、脸、眼睛、动物结构和背景对象。
4. Base Creation 中 Text Quality 独立评分；Edit Model 中 Text Quality 归 Structural Integrity。
5. Photorealism 按真实相机照片线索评估。
6. Low Poly 必须看到清楚多边形分面。
7. Alignment 要逐条核对 prompt 的对象、动作、属性、数量、场景和关系。
8. 群体 diversity 只根据可见线索判断；有一人无法可靠判断时选择 can't determine。
9. 左右图分别评价，不要合并判断。
10. 对明显结构错误不要保守降级为 minor。
