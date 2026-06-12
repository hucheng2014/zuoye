# VCG Creation RCA Apr09'26 中文详细总结

来源：[vcg_browser_sources/text/04_VCG Creation RCA Apr09'26 v1.2.txt](vcg_browser_sources/text/04_VCG%20Creation%20RCA%20Apr09%2726%20v1.2.txt:1)

## 1. 文档定位

本文件是 Apr09'26 的 VCG Base Creation 反馈与根因分析。它指出团队在 Structural Integrity、Style Match、Contains All Requests 和 Text 相关评分中错误集中，并给出严重程度校准、处罚校准、Genmoji 风格校准和图像比较改进方案。

核心结论：团队最大问题是低罚、指南解释不一致、prompt 检查不完整，以及在 A/B 比较中没有选择错误更少的图。

## 2. 错误集中区域

高错误维度包括：

1. Structural Integrity：高，错误数量 5+。
2. Style Match：高，错误数量 5+。
3. Contains All Requests：高，错误数量 4–5。
4. Text-related errors：显著，错误数量 5。

团队最困难的方面：

- 判断图像结构上应该是什么样。
- 错误解释风格，尤其是 Genmoji、Chibi 等。
- 没有完整检查 prompt 的所有要求。

## 3. 错误拆解

### 3.1 Under-penalization 是主要问题

反复出现以下情况：

- 应该是 major 或 severe 的问题被标为 minor。
- 缺失元素没有被充分处罚。
- 结构问题被淡化。
- 多余手指、肢体扭曲只被标 minor。
- 缺失关键 prompt 元素仍被评为 captures most。

趋势：团队整体评分过于宽松和保守。

### 3.2 指南误解频繁

根因标签反复出现：

- GL Misunderstanding。
- Misread Context。
- Missed Key Information。

尤其影响：

- Style Match。
- Text inclusion。
- A/B comparisons。

文档强调这不单是能力问题，而是指南清晰度、解释和校准问题。

### 3.3 Text handling 混乱

常见问题：

- prompt 要求文字但输出缺失，未被捕捉。
- 图中文字存在，但判断错误。
- 拼写和大小写错误被忽略或评分不当。
- 例如 “SIILENCE” 没有被正确处罚。
- prompt 要求文字却被标成 not needed，或相反。

趋势：团队缺少一致的文字评估框架。

### 3.4 A/B 判断错误

- 把 “A slightly better” 与 “B perfect” 判断错误。
- 比较时忽略上下文。
- 即使某张图有明确缺陷，仍选错 winner。

趋势：相对评价能力薄弱，不只是单图绝对评分问题。

## 4. 根因分析

RCA 总结：

1. 标注员不知道 minor、noticeable、severe 的明确边界，因此默认选择安全的低罚。
2. 图像观察是随机的，没有固定扫描流程。
3. 风格理解浅，只认识风格名称，不验证实际视觉特征。
4. Prompt 只读部分，漏掉对象、动作、文字、风格等约束。

## 5. 改进方案

### 5.1 严格图像扫描顺序

建议每次按以下顺序检查：

1. Structural Integrity：手指、手、脸、解剖结构。
2. Prompt coverage：缺失元素、动作、关系和属性。
3. Style match：是否真正符合目标风格。
4. Text accuracy：文字内容、拼写、大小写、位置和可读性。
5. Visual quality：清晰度、模糊、拉伸、技术性缺陷。
6. 改善缩放体验，尤其用于小文字。
7. 提高文字渲染检查准确性。

### 5.2 Severity Calibration

#### Noticeable 升级规则

眼睛、鼻子、嘴、耳朵等五官问题，即使第一眼不明显，也可能根据最新标准升级为 Noticeable，而不再是 Minor。

示例：

- 法官左眼底部不够圆，属于 Noticeable。
- 游泳者脚部小瑕疵，放大后可见，属于 Noticeable。
- 拇指异常和眼睛轻微变形，属于 Noticeable。
- 建筑、塔楼装饰或背景雕像轻微扭曲，如果第一眼不明显，可仍为 Minor。

#### Noticeable：可见但不彻底破坏

- 杠铃片位置不合理，像漂浮，会破坏场景流畅感。
- 车辆出现两个方向盘，不现实，应为 Noticeable。
- 松露与棍子连接关系不清，难以识别，应为 Noticeable。

#### Severe：破坏真实感或意图

Severe 表示问题破坏基本结构、真实感或 prompt 意图。

示例：

- 女性手指严重畸形。
- 恐龙头与根或骨状结构融合，人物手缺失，持物不明确。
- 婴儿脸部多个五官重复，整体严重扭曲。
- 人物头部拉长、手融化且无清晰手指、嘴唇区域异常。
- 游泳者没有脸部特征，手比例极小，脚异常，第二条手臂扭曲。
- 人脸和手明显扭曲，胡萝卜比例过大。

## 6. Penalty Calibration

### 6.1 手指数错误

- 手指数不正确属于 Severe Structural Integrity。
- 多手指或少手指都要处罚，不应降为 minor。
- 该问题只影响 Structural Integrity，不应随意转移到其他维度。

### 6.2 缺失部分元素

缺失颜色、动作、氛围、对象或关系时，通常影响 Input/Output Alignment。

示例：

- Prompt 要求 “I Ustand” 霓虹灯完全由 spaghetti 制成，但输出把 spaghetti 分开放置，没有构成霓虹字，应为 Captures most but not all。
- Prompt 要求枯萎花朵在暴风雨中弯向裂开的窗户，但 flower 与 window 的关系没有表达，应为 Captures most but not all。

### 6.3 主要对象错误或缺失

- Prompt 要求 rusty dumbbells，但输出没有 dumbbells，而是完全不同的 rusty object，应为 Not aligned。
- 如果输出是普通 dumbbells 但不 rusty，则可以是 captures most but not all，因为主要对象存在但属性缺失。

### 6.4 模糊属于 Visual Quality

- 主要对象或重要区域缺乏清晰度，应在 Visual Quality 降级。
- 图像底部或主体部分明显模糊，应处罚。
- 如果脸部畸形，这属于 Structural Integrity，不应错误归入 Visual Quality。

## 7. Genmoji 校准

文档要求专门校准 Genmoji：

- Genmoji 是用户可在设备上即时生成的 AI emoji。
- 应参考 demo examples 或进行研究，理解 Genmoji 的风格、颜色和光滑特征。
- Genmoji 不等于普通 illustration，也不等于 Chibi 或 generic 3D art。
- 如果图像呈现完全不同、不相关风格，应标为 Does not Match。
- 如果右图或左图只是普通 illustration，而非 emoji 风格，也应标 Does not Match。

判断 Genmoji 时关注：

- 是否像原生 emoji。
- 是否圆润、简洁、小尺寸可读。
- 背景是否符合要求。
- 角色表情是否清楚。
- 是否避免过复杂、写实或插画化背景。

## 8. Image Comparison 理解

A/B 比较的核心原则：选择 less wrong image，而不是 better-looking image。

比较检查清单：

1. 哪张图缺失 prompt 元素更少？
2. 哪张图结构问题更少？
3. 哪张图风格更接近要求？
4. 哪张图文字错误更少？
5. 哪张图 Visual Quality 更好？
6. 最终选择是否与前面维度评分一致？

如果一张图更漂亮但漏掉关键 prompt 或结构错误更严重，它不应在 Overall Quality 中胜出。

## 9. 最重要执行规则

- 先检查结构，再检查 prompt，再检查风格、文字和视觉质量。
- 对手、脸、五官、手指和肢体问题要放大检查。
- 不要把明显结构错误标为 minor。
- 文字缺失、拼错、大小写错误和伪文字必须被评分反映。
- Style Match 要看真实视觉特征，尤其是 Genmoji。
- Missing primary object 应严厉处罚为 Not aligned。
- 比较时选择错误更少者，而不是画面更吸引者。
