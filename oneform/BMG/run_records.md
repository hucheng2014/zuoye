# BMG 做题记录

## 2026-05-12 第一次做题

**题包类型**: Search Ads Close Variants (Broad Match)
**题数**: 10
**状态**: 已填写，未提交

### 评分结果

| # | Keyword | Expansion | Rating | Category | 理由 |
|---|---------|-----------|--------|----------|------|
| 1 | 网上挣钱 | 网赚赚钱 | Good | Same meaning with addition/removal of words | 同义表达，都是网上赚钱的意思 |
| 2 | safari 浏览器 | safair 浏览器 | Good | Spell correction | safair 是 safari 的拼写变体 |
| 3 | 泉城通 | 泉城行 | Acceptable | Competitors | 都是济南本地出行/交通类 app |
| 4 | 打金传奇 | 一刀传奇 | Acceptable | Competitors | 都是传奇类手游，直接竞品 |
| 5 | 苏宁快递 | 苏宁金融 | Bad | Brand terms Different functionality | 同品牌但功能完全不同（物流 vs 金融） |
| 6 | 火柴人大逃网 | 火柴人大逃亡 | Good | Spell correction | 网是亡的错别字 |
| 7 | 三国群雄传 | 三国名将传 | Acceptable | Competitors | 都是三国策略游戏竞品 |
| 8 | 汽车报价 | 汽车之家 | Acceptable | Brand term offering same functionality as Non brand term | 汽车之家提供汽车报价功能 |
| 9 | 植 | 植物 | Good | Same meaning with addition of words | 单字补全为完整词，意图相同 |
| 10 | 三亚免税 | 离岛免税 | Good | Same meaning (Non Brand Terms same intent) | 同一概念不同表述（海南离岛免税） |

### 技术细节

- 页面有 30 个 radio input（10题 x 3选项）
- 通过  选择
- 点击索引: [0, 3, 7, 10, 14, 15, 19, 22, 24, 27]
