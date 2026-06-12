# VCG Base Creation RCA Apr15'26 中文详细总结

来源：[vcg_browser_sources/text/02_VCG Base Creation — RCA Apr15'26 v1.2.txt](vcg_browser_sources/text/02_VCG%20Base%20Creation%20%E2%80%94%20RCA%20Apr15%2726%20v1.2.txt:1)

## 1. 文档定位

本文件是 VCG Base Creation 在 Apr15'26 的反馈与根因分析。它总结了标注错误最集中的维度、主要错误类型、根因，以及后续改进计划。总体结论是：团队最严重的问题不是完全看不到错误，而是看到了错误却处罚不够、未按结构化流程核查 prompt 和图像。

## 2. 高错误维度

错误高度集中在以下维度：

1. Structural Integrity：全语言环境都非常高。
2. Contains All Requests：高。
3. Style Match：高。
4. Text Included or Requested：高。
5. Captured by Camera：中高。
6. Visual Quality：中等。

这说明问题覆盖了结构、prompt 覆盖、风格、文字、真实摄影感和技术视觉质量多个环节，而不是单一维度失误。

## 3. 主要错误模式

### 3.1 Under-penalization 是主导问题

标注员经常识别出问题，但惩罚过轻：

- 多余手指、肢体畸形等结构问题被标为 minor，而不是 severe。
- 缺失 prompt 元素时仍给 captures most，而不是更严格地判为 not aligned 或至少降级。
- 文字拼写错误、破损、伪文字被指出，但最终 Text score 没有反映。
- 风格不匹配已被识别，却仍给过于宽松的 style rating。

趋势：标注员默认使用保守评分，避免严厉处罚，导致系统性低罚。

### 3.2 指南理解不足

常见指南误解包括：

- minor、noticeable、severe 的阈值在不同语言环境中不一致。
- Genmoji、Illustration 等风格被误认为 photorealism 或普通 AI 美术风格。
- Photorealism 被按个人印象判断，而不是按纹理、光影、材质、透视等客观视觉线索判断。
- 商标、受保护内容等 Flag 标准被忽略。
- prompt 没有要求文字时仍标记 2b Text tag，实际应为 N/A。

趋势：存在明显的指南理解与校准缺口。

### 3.3 评分不稳定

同类问题在不同标注员或不同任务中被过罚或欠罚：

- Structural Integrity：严重畸形图像被通过，干净图像反而被惩罚。
- Visual Quality：主体模糊被漏判，清晰图像被错误降级。
- Captured by Camera：AI 生成感明显的图像被当成真实照片，真实照片反而被降级。
- Flag：中性内容被无理由标记。

趋势：团队缺少统一校准锚点，评分更依赖个人标准。

### 3.4 Prompt 阅读不完整

标注员常常先看图像整体印象，而没有逐项拆解 prompt：

- 数量要求、对象属性、空间关系被漏读。
- 只要图像大体接近，就接受部分满足。
- Text requirements 没有与输出逐字核对。

趋势：视觉第一印象压过了系统化 prompt 验证。

### 3.5 风格识别浅层化

- 标注员知道 style name，但没有检查视觉特征是否真正符合。
- 混合风格或部分风格不匹配没有稳定处罚。
- Illustration 被接受为 Genmoji，Photorealism 与 Style Match 的判断被混淆。

趋势：需要更具体的风格参考、外部研究和示例校准。

### 3.6 A/B 与 Preference Ranking 错误

- 比较时常选更好看的图，而不是错误更少的图。
- PR ranking 与同一任务中的维度评分矛盾。
- 标注员不擅长相对比较，只会孤立判断单图。

正确做法是以维度级判断为基础，选择 less wrong image，而不是简单选择视觉上更吸引人的图。

## 4. 根因总结

RCA 将问题归纳为五点：

1. 标注员不清楚 minor、noticeable、severe 的边界，因此默认保守低罚。
2. 标注员观察图像是随机的，没有固定 scan order。
3. 风格理解不足，只认名称，不验证视觉语言。
4. Prompt 只读一部分，漏掉对象、动作、文字和风格约束。
5. 缺少共享校准锚点，评分按个人感觉而不是统一标准。

## 5. 改进计划

### 5.1 固定图像扫描顺序

每张图应按以下顺序检查：

1. Structural Integrity：解剖、手、脸、对象结构。
2. Prompt coverage：所有要求元素是否出现且正确。
3. Style match：仔细分析风格，不确定时研究。
4. Text accuracy：文字是否出现、拼写、格式、大小写是否正确。
5. Visual Quality：模糊、拉伸、倾斜、清晰度等。
6. Flag：安全、商标、文化或其他标记项。

### 5.2 严重程度校准

#### Minor

- 第一眼不明显，只有近看才发现。
- 示例：花瓶把手轻微脱离；小椅子少两条腿但不明显；女性手部轻微融合、背景城堡有小结构问题。

#### Noticeable

- 不用放大也能看到，会破坏观看流畅度，但图像仍可理解。
- 示例：手不像在拿杯子；衣服边缘异常突出；衣架漂浮在椅子上方，没有挂住。
- 一些明显眼、鼻、嘴、耳问题应升级为 Noticeable，而不是 Minor。

#### Severe

- 立即明显，破坏真实感或主体基本形态。
- 示例：人脸完全扭曲；兔子的耳、眼、嘴、尾巴严重融合；人物多出手指。
- 错误手指数通常应为 Severe Structural Integrity。

### 5.3 惩罚校准示例

- 手指数错误：Severe SI。两名成人都有额外手指，不能漏判。
- 缺失非核心元素：可能是 Captures most but not all。
- 主体完全错误或主要对象缺失：Not aligned。例如 prompt 要求 golden episcopal rings，输出为 wedding rings，就不对齐。
- 文字严重拼错或大量破损：Low Accuracy，不应给 moderate。
- 主体模糊：Visual Quality 应降级；如果没有单一主体，则整体 scenic view 也不应普遍缺乏清晰度。
- Bokeh 效果不等同于模糊，不应因正常景深而处罚。

### 5.4 风格识别要求

- 如果指南没有覆盖某种风格，应主动研究该风格。
- 如果 demo samples 没加载，可点击 “Did Not Load” 再切回，使示例刷新。
- Photorealism 必须看纹理、光线、阴影、材质表面，而不是只凭主观真实感。
- 过度光滑的皮肤、食物、物体表面常说明图像并不 photorealistic。
- 明显 AI 生成、插画、noir digital illustration 等不能被当成真实照片。

### 5.5 图像比较框架

比较左右图时应问：

1. 哪张图漏掉的 prompt 元素更少？
2. 哪张图结构问题更少？
3. 哪张图 Visual Quality 更好？
4. 哪张图的维度级评价更一致？
5. Preference Ranking 是否与前面各维度评分一致？

关键原则：选择错误更少的图，而不是单纯更漂亮的图。

## 6. 最重要的执行提醒

- 不要把严重手、脸、肢体问题降为 minor。
- 不要因图像整体漂亮而忽略 prompt 缺失。
- 不要用个人审美替代 photorealism 证据。
- 不要把没有要求的 text tag 误标为需要评分的 text request。
- 风格评价要看视觉语言，不是看名称。
- PR ranking 必须与 Structural Integrity、Alignment、Style、Visual Quality 等维度评分保持一致。
