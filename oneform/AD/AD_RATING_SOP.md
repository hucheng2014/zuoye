每个页面的做题时间要大于10分钟，一个页面5道题，做题时间要大于10分钟。
# AD Search Ads 做题标准流程（SOP）

版本：2026-05-18 v1.0  
权威教程：`Search Ads.md` / `01HA2C76XJKDS0NMM4PDA01STS.md`（April 2025）

本项目已经移除自动打分、自动循环、自动提交脚本。以后 AD 题只能按本 SOP 逐题判断、记录、复核。目标是：即使使用能力较弱的模型，也能按统一标准稳定做题，避免“关键词硬匹配”和“坐标乱点”。

---

## 0. 硬性禁令

1. **禁止使用自动规则直接判题并提交**：不得用关键词表、粗分类、固定模板批量决定评分。
2. **禁止无人复核自动提交**：提交前必须逐题核对评分、评论、页面是否真的选中。
3. **禁止刷新当前题页**，除非用户明确要求。刷新可能丢失已填写内容。
4. **禁止新开标签页替代当前题页操作**。需要查询时可用搜索/资料页，但最终填写必须回到当前题页。
5. **禁止循环赶速度**。每批题按“识别 → 研究 → 判断 → 填写 → 复核 → 提交”的顺序做。
6. **不确定时不要猜**：标记“需要补充研究/需要人工确认”，先查清再填。

---

## 1. 每道题必须记录的信息

对每一题建立记录，至少包含：

- Task ID（如页面有）
- Query 原文
- Query 意图：用户到底想找什么？是具体 App/开发者/品牌/功能/游戏/本地服务代码？
- Ad 信息：App 名、Subtitle、Developer、是否游戏、核心功能/玩法
- 研究依据：App Store 搜索结果、App Store 详情页、网页搜索或本地常识说明
- 最终评分：`Excellent` / `Good` / `Acceptable` / `Bad`
- Comments：说明评分理由；Bad 必须解释原因；建议所有题都写简短理由
- 提交前核对状态：单选框是否已选、评论是否对应本题、是否有 required 报错

建议使用：`records/ad_batch_template.json` 或 `tools/validate_ad_batch.py --init records/YYYY-MM-DD_batchN.json --count 5`。

---

## 2. 研究顺序

每题按以下顺序判断：

1. **看 Query 原文**
   - 是否为具体 App 名称、开发者名、品牌名？
   - 是否为通用功能，例如“mp3 转换器”“天气”“健身”？
   - 是否为游戏名称、游戏类型、IP、玩法？
   - 是否为本地服务/代码，例如 `12123`、`12315`？需结合地区常识。

2. **看广告 App**
   - App 名 + subtitle + developer 是最重要信息。
   - 需要时打开 App Store Preview 看描述。
   - 不因评论少、评分低、收费、描述差而降级。

3. **看 App Store 搜索结果**
   - 只看自然搜索结果，不看顶部广告。
   - 用来判断 Query 的真实意图和主要候选 App。

4. **必要时做网页搜索**
   - 对缩写、本地词、中文品牌、游戏俗称必须确认含义。
   - Comments 中可写“Research indicates ...”或记录链接/来源。

---

## 3. 评分标准速查

### Excellent

给 `Excellent` 的条件：广告与用户最可能意图强相关，用户很可能点击。

常见情况：

- Query 与 Ad App 名称精确/近似匹配。
- Query 是开发者名，Ad 来自该开发者。
- Ad 是 Query 指向 App 的直接竞品，核心功能高度相同。
- Query 是宽泛类别，Ad 明确满足该类别核心需求。
- 游戏题：同一游戏、同类强竞品，或玩法/主题/受众高度一致。

### Good

给 `Good` 的条件：明显相关、用户较可能感兴趣，但不是最直接结果。

常见情况：

- 功能相近但不是精确功能。
- 是目标 App/Game 的辅助工具、插件、周边功能。
- 同一生态或同一需求链，但范围更窄/更宽。
- 游戏题：玩法或主题接近，但存在明显差异。

### Acceptable

给 `Acceptable` 的条件：有轻微关系，用户不至于惊讶，但不太可能感兴趣。

常见情况：

- 同大类但具体需求不同，只能算弱相关。
- 同一开发者但功能/主题不同，且没有更强关联；通常不低于 Acceptable。
- 相关但在测试地区不可用。
- 金融、教育、工具等大类存在宽泛关联，但核心意图不一致。

### Bad

给 `Bad` 的条件：无可感知关系，或虽然有表面词重合但实际意图错位，会让用户困惑/反感。

常见情况：

- Query 与 Ad 功能、受众、使用场景完全不同。
- 只有表面词重合，例如“扫描”分别是文档扫描和病毒扫描。
- 同大类但细分领域互不相关，例如买菜 App vs 服装购物 App。
- 游戏题：玩法、主题、受众明显割裂，例如儿童益智 vs 恐怖赛车。
- 可能冒犯或明显不合时宜的广告。

---

## 4. App 题判断流程

逐题回答以下问题：

1. Query 最自然的用户意图是什么？
2. Ad App 的核心功能是什么？
3. 两者是否为同一个 App、同开发者、或直接竞品？
4. 如果不是，功能是否能满足同一核心需求？
5. 如果只是同大类，细分需求、目标用户、使用场景是否仍然接近？
6. 如果用户看到这个广告，会是“很想点 / 可能点 / 不惊讶但不想点 / 困惑或反感”？

映射到评分：

- 很想点、最可能相关 → Excellent
- 可能点、明显有用 → Good
- 不惊讶但兴趣弱 → Acceptable
- 困惑、反感、没有逻辑关系 → Bad

---

## 5. Game 题判断流程

游戏题不要只看“都是游戏”。必须比较：

1. **Play style**：动作、射击、放置、解谜、竞速、模拟、策略等。
2. **Presentation/theme**：现实/卡通/恐怖/二次元/体育/战争/儿童等。
3. **Audience**：儿童、休闲玩家、硬核玩家、体育粉、IP 粉等。

评分：

- 同游戏/同 IP/强竞品/玩法主题受众高度一致 → Excellent
- 玩法或主题较接近，但不完全匹配 → Good
- 都是游戏且有弱联系，但用户不太会点 → Acceptable
- 玩法、主题、受众割裂，或只是同为游戏 → Bad

---

## 6. Comments 写法

Comments 要短但必须对应本题，不能复制错题内容。

推荐结构：

```text
The query "{query}" indicates the user wants {query_intent}. The advertised app "{app}" is {ad_function}. {relationship_reason}. Rated {rating}.
```

Bad 示例：

```text
The query "12315" refers to China’s consumer complaint/reporting service. The advertised app "布球人" is for clothing/fabric-related services, which serves a completely different need and audience. There is no logical relevance, so this is Bad.
```

Acceptable 示例：

```text
The query "mp3 转换器" indicates a need to convert audio files to MP3. The advertised app is a voice recorder, so it is in the broad audio tools area but does not directly provide the requested conversion function. The connection is weak but understandable. Rated Acceptable.
```

提交前必须检查：评论里的 Query/App 是否与当前题一致；不得出现上一题的 Query、App 或无关内容。

---

## 7. 每批题操作流程

### A. 准备

1. 确认自动脚本未运行。
2. 在当前页面读取全部题目。
3. 创建本批记录文件。

### B. 逐题判断

对 1~5 题逐题完成：

1. 复制 Query 和 Ad 信息到记录。
2. 研究 Query 意图和 Ad 功能。
3. 写出“为什么不是更高/更低”的理由。
4. 决定评分。
5. 写 Comments。

### C. 填写页面

1. 逐题选择单选框。
2. 逐题填写 Comments。
3. 不要用坐标批量乱点；优先按题目区域和标签定位。

### D. 提交前复核（必须）

逐题检查：

- [ ] 5 道题都选了一个 Ad Relevance
- [ ] 每题 Comments 不为空
- [ ] Bad 题 Comments 明确解释为什么 Bad
- [ ] Comments 中 Query/App 没串题
- [ ] 页面没有 `This field is required!`
- [ ] 记录文件与页面内容一致

只有全部通过，才允许提交。

### E. 提交后

1. 点击 `Submit Rating` 后等待约 2 秒。
2. 如果出现 required 报错，不刷新，直接在当前页面修正。
3. 如果新题刷出，重新开始 A~D。
4. 如果没有题，记录结束状态。

---

## 8. 典型校准案例

| Query | Ad | 评分 | 核心理由 |
|---|---|---:|---|
| 163 邮箱 | 网易新闻 | Acceptable | 同公司/同生态弱相关，但邮箱和新闻功能不同 |
| 12123 | 饿了么 | Bad | 交通管理服务 vs 外卖，无逻辑关系 |
| 预定鲜花 | 花礼网 | Excellent | 鲜花预订需求精确匹配 |
| mp3 转换器 | MP3转换器 | Excellent | 功能精确匹配 |
| mp3 转换器 | 录音机 | Acceptable | 同为音频工具，但不直接转换 MP3 |
| 12315 | 布球人 | Bad | 消费者投诉热线 vs 服装/面料服务，无关 |
| 高清卫星地球 | 街景/地图类 App | Good/Excellent | 若确实提供卫星/地图/街景浏览，通常高度相关；需看功能描述 |

> 校准案例不是死规则；实际题仍需按 Query 意图和 Ad 功能判断。

## 知识库集成（替代全量 Search Ads.md 加载）

做题时**不再需要**读取完整 Search Ads.md（50KB）。改用精简知识库：

### 基础上下文

```bash
cat pipeline/knowledge/ad/compact_sop.md    # 精简评分规则 (~1.7KB)
cat pipeline/knowledge/ad/flow.md            # 纯操作流程
```

### 按需查询

```bash
node pipeline/scripts/query_knowledge.js --task ad --query "landing page relevance vs query"
node pipeline/scripts/query_knowledge.js --task ad --query "ad text misleading"
node pipeline/scripts/query_knowledge.js --task ad --chunk relevance_levels
node pipeline/scripts/query_knowledge.js --task ad --chunk query_interpretation
node pipeline/scripts/query_knowledge.js --task ad --chunk landing_page
node pipeline/scripts/query_knowledge.js --task ad --chunk ad_text_quality
node pipeline/scripts/query_knowledge.js --task ad --chunk edge_cases
```

### 效果

- 之前：每题加载 50KB Search Ads.md
- 之后：固定 4KB + 按需 2-3KB = 每题 ~6KB（节省 88%）
