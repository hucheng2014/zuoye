# BMG - Broad Match Guidelines 评估任务

## 任务概述

评估广告关键词(keyword)与扩展查询(expansion)之间的匹配质量。
平台：tryrating.com，容器名：oneform-agent，noVNC：http://localhost:6081/vnc.html

## 评分标准（三档）

| 评分 | 含义 | 判断依据 |
|------|------|----------|
| **Good** | keyword 和 expansion 看起来相似 | 拼写纠正、空格变化、词序调换、音译、单复数、缩写、加减词但意思不变、旧应用名、翻译 |
| **Acceptable** | 视觉不同但共享关系和意图 | 直接竞品、非竞品但同功能品牌、品牌与非品牌同功能、非品牌词不同但同意图 |
| **Bad** | 不共享意图 | 同品牌不同功能、不同行业品牌、品牌与非品牌不同功能、非品牌词不同意图 |

## Good 的 9 个子类别

1. **Spell correction** — 拼写纠正（不影响辨识）
2. **Space** — 空格增减（不影响辨识）
3. **Reordering** — 词序调换（意思不变）
4. **Transliteration** — 音译
5. **Singular/Plural** — 单复数变化
6. **Abbreviations** — 全称/缩写
7. **Same meaning with addition or removal of words** — 加减词但意思不变
8. **Former app name** — 旧应用名（如 Twitter → X）
9. **Translation** — 翻译

## Acceptable 的 4 个子类别

1. **Competitors** — 直接竞品（如 linkedin → indeed）
2. **Brand terms (not competing) offering same functionality** — 非竞品但同功能品牌（如 uber → instacart）
3. **Brand term offering same functionality as Non brand term** — 品牌与非品牌同功能（如 whatsapp → Free calls）
4. **Non Brand Terms same meaning and intent** — 非品牌词不同但同意图（如 fitness → Workout）

## Bad 的 4 个子类别

1. **Non Brand/Brand terms with Different intent (despite same genre)** — 同行业但不同意图（如 Coinbase → Amazon）
2. **Brand term offering different functionality than Non brand terms** — 品牌与非品牌不同功能（如 khan academy → brain games）
3. **Brand terms Different functionality or features** — 品牌间不同功能（如 kindle → alexa）
4. **Non Brand Terms different meaning and intent** — 非品牌词不同意图（如 video editor → collage maker）

## 关键判断原则

- **意图(Intent)是核心**：keyword intent = 广告主期望结果；expansion intent = 用户搜索意图
- **同品牌不等于同意图**：google maps → google translator = Bad（导航 vs 翻译）
- **同类别不等于同意图**：shooting games → toddler games = Bad（成人射击 vs 幼儿游戏）
- **泛化关键词扩展到具体品牌 = Bad**：App → Netflix, Free → Facebook
- **具体到泛化也可能 Bad**：Shooting games → Online games（具体→泛化）
- **竞品 = Acceptable**：即使视觉完全不同，只要共享核心功能意图

## Comments 填写规则

- **仅在特殊情况下填写**：keyword 或 expansion 是非本地市场语言时，翻译后在 Comments 说明
- 正常情况下不需要填写 Comments

## 研究方法

- **品牌词**：优先 App Store 搜索，查看 app 描述确认功能
- **非品牌词**：Web 搜索 + App Store 搜索，理解含义和意图
- **忽略搜索结果顶部广告**，只看自然结果

## 做题环境

- 容器名：
- CDP：，HTTP 加 
- WebSocket： -> 
- 页面：
- 评分控件：，每题 3 个（Good/Acceptable/Bad），共 N*3 个
- 提交按钮：

## 做题流程

1. 通过 CDP 读取页面文本，提取所有 keyword-expansion 对
2. 对每对进行意图分析，按规则判断 Good/Acceptable/Bad
3. 通过 JS 点击对应 radio button（）
4. 验证所有选择已生效
5. **禁止自动提交** — 等待用户确认
