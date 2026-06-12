# Roads - Painted Features w/ Bounding Box 教程总结 / Tutorial Summary

> 来源：页面内联指南（Roads - Painted Features w/ Bounding Box Evaluation Guidelines，May 2026；Quick Reference updated May 14, 2026）。

---

## 中文版教程总结

### 1. 任务目标
- 你会看到一张数字化 **3D 道路渲染截图**，其中用 **bounding box（边界框）** 标出需要检查的区域。
- 任务是只检查边界框内的道路 **喷绘/标线类 painted features** 是否存在视觉问题，并判断严重程度。
- 不需要查看卫星图或街景图，也不需要核对真实世界情况；评分只基于给出的截图。目标不是找与真实情况的差异，而是找在截图中明显影响视觉质量的渲染错误。

### 2. 边界框范围规则
- **只评估边界框内的问题**。
- 边界框外的问题不要计入严重程度，也不要据此选择问题类型。
- 部分教程示例来自旧版本，图片中可能没有边界框；遇到这类示例时，只需把示例逻辑应用到“如果该问题出现在边界框内”的情况。

### 3. 评分选项
对边界框内截图选择最合适的一项：

1. **Major issue seen within bounding box（重大问题）**  
   一个或多个问题不放大也能被普通观察者明显看到，或边界框内的 painted features 整体看起来明显有问题。
2. **Minor issue seen within bounding box（轻微问题）**  
   需要仔细检查或放大才能确认的问题；不显著影响边界框内特征的整体外观。
3. **No issues seen within bounding box（无问题）**  
   边界框内道路可见，并且没有可观察到的问题。
4. **No 3D road visible in the screenshot（无 3D 道路）**  
   截图不在具有 3D 道路渲染的道路位置，或道路/道路标线没有正常渲染。

选择 Major 或 Minor 后，会出现按特征类型组织的复选框。需要为边界框内发现的 **所有问题** 勾选相应的特征和问题类型；同一个缺陷可以多选多个问题类型。

### 4. 需要评估的 painted features
- **Lane markings（车道线/车道标线）**：表示机动车或自行车车道边界的线。
- **Colored lanes（彩色车道）**：如绿色自行车道、红/黄色 HOV/Cab/Bus 车道等；不要把 painted crosswalks（喷绘人行横道）误认为 colored lanes。
- **RSM text（道路表面文字标识）**：例如 “STOP”“BUS ONLY”“KEEP CLEAR”等路面文字。
- **RSM glyph（道路表面图形标识）**：例如转向箭头、直行箭头、合流箭头、自行车图标等。
- **Painted medians（喷绘隔离区/导流区）**：禁止车辆使用的喷绘限制区域，通常由边界轮廓和内部填充图案组成。

道路范围包括高速路、主干道、非主干道等。若问题位于路口附近，按正常规则评分；若问题就在路口处，可在评论中备注 “intersection”。本任务不评估 crosswalks 或其他物理设施本身。

### 5. 问题类型与判定
可用于所有 painted feature 类型；如果一个缺陷同时符合多个类型，应全部勾选。

#### 5.1 Geometry / Poor Geometry（几何形状错误）
特征形状异常或形成错误，包括：边界弯曲/粗糙、区域变形、闭合失败、过短、端点包裹错误、重复渲染、线型错误（该实线却是虚线或相反）、相邻喷绘区域过渡不平滑等。

常见例子：
- painted median 边界不规则、波浪形，或整体形状错误；
- stop line / lane marking 明显锯齿状；
- bus stop 区域白色车道线没有闭合成完整形状；
- 绿色自行车道突然结束、端点包裹错误或明显过短；
- painted median 的边界车道线缺失；
- painted medians 在不同段之间异常地来回交替方向。

#### 5.2 Colliding（碰撞/重叠）
两个或多个本应独立的特征在不应重叠的位置相互重叠。包括同类重叠、跨类型重叠和颜色边界侵入。

常见例子：
- RSM text 或 glyph 与 painted median 重叠；
- 多个 RSM glyph 相互重叠；
- 两个 painted median 区域互相重叠；
- colored lane 与 lane markings 或转向箭头重叠；
- 黄色线侵入白色喷绘区域等。

#### 5.3 Void（缺失/空洞）
在明显应该连续的位置出现缺口或缺失部分。重点是“本应存在但没有”。

常见例子：
- lane marking 中间出现不应有的断裂；
- painted median 内部 chevron / 填充图案缺失，边界还在但内部有空白；
- 自行车道标识缺少必要的方向箭头；
- “KEEP CLEAR”等路面文字本应跨两条车道或在每条车道重复，但只渲染在一条车道，导致缺失。

**Void 与可接受间隔的区分**：如果相同 median 的相邻区域形成了清晰重复图案，但中间突然缺失，通常是 Void；如果整个填充图案本来就稀疏或分段设计，尤其是 disjointed/broken painted median stripes，则不是 Void。

自行车箭头规则：当 bike symbol 或 “BIKE LANE” text 出现在实际自行车道中时，应有方向箭头；若缺失则标为 RSM glyph void。若自行车图标位于路口绿色框内表示自行车等待区，则不一定需要箭头。如果箭头存在，即使边界框没有覆盖箭头本身，也不要因箭头位置不在框内而判错。

#### 5.4 Excess Paint（多余喷绘/多余标线）
在不应该有喷绘或标线的地方出现了 paint、markings 或 colored areas，或它们远超预期范围。此时形状可能本身没问题，问题是“不该出现”或“延伸过多”。

常见例子：
- painted median 过大并延伸到路口中间；
- 自行车道内出现多余白色车道线；
- 道路表面有多余虚线、实线、点状标记或大块 paint blob。

#### 5.5 Other（其他）
不适合归入 Geometry、Colliding、Void、Excess Paint 的问题。选择 Other 时应在文本框中简短说明。若 void 无法归因到明确 painted feature，可使用 Other/Unclear Feature Type Void Issue。

### 6. 类别边界决策规则
- **Excess Paint vs. Geometry**：
  - Geometry = 特征本应存在，但形状、边界或线型错了。
  - Excess Paint = 特征或标记本不应出现在那里，或延伸到不该去的地方。
  - 两者可同时成立：例如不该出现的 oversized painted median 同时边界又很扭曲，应同时勾选 Excess Paint 和 Geometry。
- **Excess Paint vs. Colliding**：
  - 如果能识别出两个独立且本应存在的特征相互重叠，选 Colliding。
  - 如果只是没有对应真实/预期特征的多余 paint，选 Excess Paint。
- **Multi-tagging**：同一缺陷若同时变形、重叠、缺失或多余，应勾选所有适用类型。

### 7. 不应标为问题的情况
以下情况即使看起来奇怪，也不要计为问题：
- 地图上的半透明箭头不是 RSM glyph，即使看似与其他特征重叠也不标。
- 道路名称/道路标签与道路特征重叠是正常的。
- 穿过道路的灰色 rail lines 是正常渲染。
- painted median 内部的 broken / disjointed stripe filling pattern 通常不是问题。
- 穿过 sidewalk、crosswalk 等的透明线不是问题。
- 紫色或红色线表示州界/边界，不是道路喷绘问题。
- RSM 周围轻微白色描边是已知小伪影，不要报错。
- 模糊的黄色双黄线若反映 ground truth 双黄线渲染风格，视为无问题；但如果黄色边界明显侵入 painted median 区域，仍应按问题处理。
- 不要因为 sidewalk、crosswalk、非 painted features 缺失或真实世界中可能不存在/存在而报错；不要用坐标核对真实世界来评估“额外”或“缺失”特征。

### 8. 严重程度判断
- **Major**：普通观察者不放大也能明显看到；或边界框内特征整体明显糟糕。即使只有一个缺陷，只要一眼可见，通常也是 Major。
- **Minor**：需要仔细观察或放大才确认；例如轻微边界抖动、局部粗糙，且不明显改变整体外观。
- **No Issue**：边界框内道路可见，没有可观察问题。
- **No 3D Road**：截图不是具有 3D 道路渲染的道路位置，或没有道路/道路喷绘渲染。

### 9. 典型评分示例逻辑
- **Major 示例**：明显的 RSM text/glyph 碰撞；自行车道缺少必要方向箭头；多个 glyph 互相重叠；colored lane 与 lane marking 或右转箭头明显重叠；道路几何缺失；colored lane 明显断开；painted medians 方向异常交替；painted median 内明显 void；painted median 缺少应有边界车道线。
- **Minor 示例**：lane marking 轻微越过应结束位置；painted median 与 physical median 的碰撞不太明显；较轻的 poor geometry。
- **No Issue 示例**：道路整体符合预期；painted median 内部 broken/disjointed stripes 属于正常图案。

---

## English Tutorial Summary

### 1. Task Goal
- You are shown a screenshot of a digitized **3D road rendering** with a **bounding box** highlighting the area to review.
- Evaluate only the **painted road features** inside the bounding box for visual/rendering issues and assign a severity.
- Do not use satellite or street imagery, and do not verify against real-world ground truth. Ratings must be based only on the provided screenshot. The goal is to catch visible screenshot/rendering errors, not map-data discrepancies.

### 2. Bounding Box Scope
- **Only evaluate issues inside the bounding box.**
- Issues outside the box must not affect the severity or selected issue types.
- Some guideline examples come from an older version without bounding boxes. Apply their logic as if the illustrated issue were inside the bounding box.

### 3. Rating Options
Select the most appropriate option for the bounding box:

1. **Major issue seen within bounding box**  
   One or more issues are obvious to a casual viewer without zooming, or the painted features in the box look clearly problematic overall.
2. **Minor issue seen within bounding box**  
   Issues require careful inspection or zooming to confirm and do not significantly affect the feature’s appearance in the box.
3. **No issues seen within bounding box**  
   A road is visible in the box and no issue is observable.
4. **No 3D road visible in the screenshot**  
   The screenshot is not at a road location with a 3D rendering, or the road/painted road rendering is missing.

If you select Major or Minor, issue checkboxes appear by feature type. Select **all** applicable feature/issue combinations found inside the bounding box. A single defect may require multiple tags.

### 4. Feature Types to Evaluate
- **Lane markings**: Lines representing vehicle or bicycle lane boundaries.
- **Colored lanes**: Green bike lanes, red/yellow HOV/Cab/Bus lanes, etc.; do not confuse painted crosswalks with colored lanes.
- **RSM text**: Pavement signage text such as “STOP,” “BUS ONLY,” or “KEEP CLEAR.”
- **RSM glyph**: Pavement signage symbols such as turn arrows, straight arrows, merge arrows, or bike icons.
- **Painted medians**: Painted restrictive/blocked-off areas where vehicles should not drive, usually with a boundary outline and fill pattern.

The task covers highways, arterial roads, and non-arterial roads. Intersection-area issues should be rated normally; add “intersection” in comments if relevant. Crosswalks and other physical features are not the target features themselves.

### 5. Issue Types
All issue types can apply to all painted feature categories. Tag every applicable issue type.

#### 5.1 Geometry / Poor Geometry
The feature has an odd or incorrectly formed shape: wobbly/rough borders, misshaped areas, failed closures, too short, incorrect endpoint wrapping, double rendering, wrong line type, or non-smooth transitions.

Examples include irregular painted median borders, jagged stop lines, incomplete bus-stop lane-marking shapes, green bike lanes ending abruptly or wrapping incorrectly, missing painted-median boundary lane markings, and painted medians alternating direction unexpectedly.

#### 5.2 Colliding
Two or more distinct intended features overlap where they should not. This includes same-type overlaps, cross-type overlaps, and color-boundary intrusions.

Examples include RSM text/glyph colliding with painted medians, glyphs colliding with each other, two painted medians overlapping, colored lanes overlapping lane markings or turn arrows, and yellow lines intruding into white painted areas.

#### 5.3 Void
A gap or missing section appears where continuity is clearly expected.

Examples include unexpected gaps in lane markings, missing chevron/fill sections inside painted medians, missing required directional arrows for bike-lane markings, and KEEP CLEAR text missing from a lane where it should span or repeat.

Void vs. acceptable gap: a void exists when a clear repeated pattern appears on both sides but is missing in the middle. If the fill pattern is sparse or segmented by design, especially disjointed painted-median stripes, it is not a void.

Bike-arrow rule: A bike symbol or “BIKE LANE” text in an actual bike lane requires an arrow; if missing, tag an RSM glyph void. A bike symbol in a green box at an intersection/bike stop area does not necessarily require an arrow. If the arrow exists, do not mark an issue merely because the bounding box is not over the arrow.

#### 5.4 Excess Paint
Paint, markings, or colored areas appear where they should not, or extend far beyond the intended area. The shape may be fine; the issue is that the paint should not be there.

Examples include an oversized painted median extending into an intersection, extra white lane markings inside a bike lane, extra dashes/solid lines/dots, or large paint blobs.

#### 5.5 Other
Use Other for issues that do not fit Geometry, Colliding, Void, or Excess Paint. Provide a brief description in the text box. Use the Other/Unclear Feature Type Void option when a void cannot be assigned to a specific painted feature.

### 6. Category Boundary Rules
- **Excess Paint vs. Geometry**: Geometry means the intended feature is shaped/rendered incorrectly. Excess Paint means the feature/mark should not be present or extends where it should not. Both can apply to the same defect.
- **Excess Paint vs. Colliding**: If two separate intended features overlap, choose Colliding. If there is paint with no corresponding intended feature, choose Excess Paint.
- **Multi-tagging**: If one defect is misshaped, overlapping, missing, or excessive in multiple ways, tag all applicable issue types.

### 7. Non-Issues
Do not flag the following:
- Semi-transparent map arrows; they are not RSM glyphs.
- Road labels overlapping road features.
- Gray rail lines crossing roads.
- Broken/disjointed stripe fill patterns inside painted medians.
- Transparent lines crossing sidewalks, crosswalks, etc.
- Purple/reddish state-boundary lines.
- Slight white outlines around RSMs; this is a known artifact.
- Blurry yellow double-line rendering when it reflects the intended double-yellow style. Exception: irregular yellow borders intruding into painted medians remain issues.
- Missing sidewalks, crosswalks, or other non-painted features; do not check coordinates or real-world imagery to decide whether a feature is extra or missing.

### 8. Severity Rules
- **Major**: Obvious without zooming to a casual viewer, or the overall quality inside the bounding box is clearly problematic. A single obvious defect is usually Major.
- **Minor**: Requires careful inspection/zooming and does not significantly affect the overall appearance, such as a slight wobble or minor roughness.
- **No Issue**: The road is visible in the bounding box and no issue is observable.
- **No 3D Road**: The screenshot lacks a road location with 3D rendering or lacks the road/painted-road rendering.

### 9. Common Example Logic
- **Major**: Obvious RSM text/glyph collisions; missing required bike-lane arrow; glyphs colliding; colored lanes overlapping lane markings or right-turn arrows; missing road geometry; obvious colored-lane gaps; painted medians alternating direction; clear painted-median voids; missing boundary lane markings for painted medians.
- **Minor**: Lane markings slightly extend beyond where they should end; subtle painted-median collision with a physical median; less obvious poor geometry.
- **No Issue**: The road matches expectations; broken/disjointed painted-median stripes are normal.
