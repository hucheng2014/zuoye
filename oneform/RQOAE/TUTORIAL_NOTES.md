# RQOAE 教程要点总结

## 教程中的评分示例（从页面文本提取）

### Awful (1分) 示例
- Intro 2s：整段静音 → Awful
- Outro 7s：7秒中有5秒静音 → Awful
- Outro 2s：什么都没加就突然结束 → Awful

### Poor (2分) 示例
- Outro 2s：最后一拍有拖拽感 → Poor
- Post-Extension 6.2s：7.5秒处能听到节拍犹豫/拖拽 → Poor
- Outro 7s：7秒够长但感觉仓促 → Poor

### Average (3分) 示例
- 节拍拖拽不太明显时可以给 Average
- 有轻微声音异常但不严重
- 有些随机不和谐但可接受

### Good (4分) 示例
- 过渡平滑自然
- 几乎听不出编辑痕迹
- 音乐性保持完好

### Excellent (5分) 示例
- 完美无缝
- 完全听不出是编辑的
- 音乐自然流畅

## 关键判断规则

### Intro 评判
- 在人声中间开始 → 不好（除非是淡入+重复段落）
- 开始后能量突然下降 → 不好
- 在某段结尾开始（听到尾巴） → 不好
- 开头太突兀 → 不好

### Outro 评判
- 在人声中间结束 → 不好
- 结束前能量突然上升 → 不好
- 在新段落开始时结束（悬崖感） → 不好
- 结尾太突兀 → 不好

### Bridge 评判
- 两段差异太大导致过渡不自然 → 结构问题
- 人声被截断/变形/不可理解 → 人声问题

### Pre/Post Extension 评判
- 延伸部分不够音乐性 → 不好
- 人声被截断/变形 → 不好

### 通用问题
- 空白/静音 → Awful-Poor
- 节奏拖拽 → Awful-Poor（取决于严重程度）
- 突兀开始/结束 → Poor-Awful
- 嗡嗡声/嘶嘶声/失真 → Poor-Average
- 随机不和谐声音 → Poor-Average
- 爆音/噼啪声 → Awful-Average（取决于严重程度）

## 声学特征与评分对应

| 特征 | 阈值 | 评分 |
|------|------|------|
| silence_ratio > 0.7 | 大部分静音 | Awful (1) |
| silence_ratio > 0.4 | 部分静音 | Awful-Poor (1-2) |
| max_energy_jump > 0.4 | 极度突兀 | Awful-Poor (1-2) |
| max_energy_jump > 0.25 | 轻微突兀 | Poor-Average (2-3) |
| rms < 0.003 | 几乎无声 | Awful (1) |
| silence < 0.1 & energy > 0.02 | 正常音乐 | Good+ (4-5) |
| PANNs top tag = "Music" > 0.7 | 音乐性强 | 加分 |
| PANNs top tag = "Silence" > 0.3 | 静音明显 | 减分 |
