# Milky Way - Lightspeed 搜索满意度评估培训教程详细总结
*(Milky Way - Lightspeed Search Satisfaction Orientation Module Summary)*

本文件是对 OneForma `Milky Way - Lightspeed` 搜索满意度评估（Search Satisfaction）培训课程的全面而准确的本地化总结。内容基于从受控浏览器中提取的 13 个课程 Lesson 的完整文本及附带的图表资产，旨在帮助评估员全面掌握项目规则，为认证考试与实际工作提供核心参考。

---

## 目录
1. [安全与合规要求 (Lesson 1: Welcome)](#1-安全与合规要求-lesson-1-welcome)
2. [项目核心目标 (Lesson 3: Core Purpose)](#2-项目核心目标-lesson-3-core-purpose)
3. [核心专业词汇表 (Lesson 4: Glossary)](#3-核心专业词汇表-lesson-4-glossary)
4. [评估界面与组件 (Lesson 5: Process Overview)](#4-评估界面与组件-lesson-5-process-overview)
5. [搜索词意图理解 (Lesson 6: Process in Detail)](#5-搜索词意图理解-lesson-6-process-in-detail)
6. [满意度评估四大原则 (Lesson 7: Satisfaction Principles)](#6-满意度评估四大原则-lesson-7-satisfaction-principles)
7. [特殊情况与结果类型处理规则 (Lesson 8: Special Case Handling)](#7-特殊情况与结果类型处理规则-lesson-8-special-case-handling)
8. [侧对比偏好评估 (Lesson 9: Overall Preference Rating - OPR)](#8-侧对比偏好评估-lesson-9-overall-preference-rating---opr)
9. [OPR 侧对比 12 个实战案例解析 (Lesson 10: OPR and Comment Examples)](#9-opr-侧对比-12-个实战案例解析-lesson-10-opr-and-comment-examples)
10. [技术支持与沟通方式 (Lesson 12: Communication and Contact)](#10-技术支持与沟通方式-lesson-12-communication-and-contact)
11. [认证考试须知 (Lesson 13: Next Steps & Lesson 2)](#11-认证考试须知-lesson-13-next-steps--lesson-2)

---

## 1. 安全与合规要求 (Lesson 1: Welcome)

项目参与者必须严格遵守信息安全与保密协议（NDA）。项目对任何安全违规行为均持**零容忍**态度，违规者将面临严重后果甚至法律诉讼。

### 🚫 严厉禁止的行为
*   **禁止截图或录屏**：严禁以任何形式捕获、留存课程及项目材料。
*   **禁止公开分享信息**：严禁在互联网、公开平台、论坛、社交媒体等处分享任何项目文档、截图或录像。
*   **禁止私下讨论**：严禁与任何无关人员（包括非项目成员）讨论机密信息或项目内容。
*   **禁止复制或修改**：严禁私自复制、更改向您展示的任何项目资产。
*   **禁止使用生成式人工智能/大语言模型**：**在流程的任何阶段，均严禁使用 ChatGPT、Claude 等大语言模型工具**。禁止使用它们来生成内容、核对事实或头脑风暴。使用此类工具属于严重违规，会导致账号被直接终止。

### 良好行为规范
*   理解并遵守 NDA 指导说明，确保已阅读并完全知晓合规要求。
*   仅在安全、私密且合规的网络环境下访问项目材料，严禁在公共场所或使用公共不安全 Wi-Fi 访问项目信息。

---

## 2. 项目核心目标 (Lesson 3: Core Purpose)

Milky Way - Lightspeed 项目是一个提升搜索引擎质量的质量保证项目，围绕以下三个基本维度展开：

*   **What（是什么）**：一个支持不同浏览器和搜索应用程序的**质量保证倡议（Quality Assurance Initiative）**。
*   **Why（为什么）**：在用户发起查询（Query）时，**提升搜索引擎返回结果的质量与满意度**。
*   **How（怎么做）**：评估员根据项目给定的指导方针（Guidelines），**对搜索结果的满意度进行分级与评估**。

> [!IMPORTANT]
> 本 orientation 课程仅提供简化版的逐步介绍。在实际评估中，**官方指南（Guidelines, 简称 GL）是判定满意度的唯一权威标准**。当遇到复杂或边界案例时，请务必以 Document Reference Library 中的 GL 文档为准。

---

## 3. 核心专业词汇表 (Lesson 4: Glossary)

在评估过程中，正确识别 and 分类查询词中的实体至关重要。以下为六个最核心的专业术语定义及示例：

| 术语名称 | 英文名称 | 定义 | 典型示例 |
| :--- | :--- | :--- | :--- |
| **命名实体** | Named Entity | 在英语中通常需要大写的人名、地名、组织机构、商业公司、产品、服务或事件（包含虚构实体）。 | Stephen Curry, Yellowstone National Park, Jupiter, Médecins Sans Frontières (无国界医生), Starbucks, Post-It Notes, Skype, Super Bowl LI, Boxer Rebellion, Frodo Baggins |
| **知识术语** | Knowledge Term | 描述一个概念或研究对象（非命名实体）的词或短语，用户可能希望对其进行深入学习。可来自科学、技术、数学、医学、历史、哲学、文学、艺术、经济等领域，通常为名词短语。 | Photosynthesis (光合作用), Elephant (大象), ROC curve (ROC曲线), Linear algebra (线性代数), Cancer (癌症), Oligarchy (寡头政治), Veto (否决权), Existentialism (存在主义), Metaphor (暗喻), Impressionism (印象派), Interest rate (利率) |
| **官方网站** | Official Site | 由命名实体（或其雇主/组织）提供，代表该实体希望向在线世界展示其自身形象的官方网站。 | Microsoft: `www.microsoft.com`<br>U.S. Internal Revenue Service: `www.irs.gov`<br>Taylor Swift: `www.taylorswift.com`<br>Henry Louis Gates Jr. (哈佛教授个人主页): `https://aaas.fas.harvard.edu/people/henry-louis-gates-jr` |
| **官方在线主页** | Official Online Presence | 官方网站的延伸。指命名实体在商业第三方服务/社交网络上创建的在线“大本营”。 | 官方 Twitter: `https://twitter.com/StephenKing`<br>官方 YouTube: `https://www.youtube.com/user/therock`<br>官方 Instagram: `https://www.instagram.com/badbunnypr/` |
| **连锁商家** | Chain Business | 包含多个地理位置的分支，各个地点提供基本相同的产品或服务，且用户与该商家的主要互动方式是**亲自前往这些实体地点**。 | Starbucks (星巴克), Taco Bell (塔可钟), Party City, California Department of Motor Vehicles (加州车管所) |
| **视觉特征实体** | Visually Distinctive Entity | 能够通过视觉图片被有用且直观地表达其概念或身份的实体。人和地点是视觉特征实体，某些工具、几何图形、地质或建筑特征以及视觉艺术品也属于此类。 | Jacinda Ardern, Taj Mahal (泰姬陵), ball-peen hammer (圆头锤), dodecahedron (十二面体), mesa (台地), flying buttress (飞扶壁), "The Thinker" (罗丹雕塑《思想者》) |

---

## 4. 评估界面与组件 (Lesson 5: Process Overview)

在评级工具的界面中，除了提供查询词和待评估的结果外，还会显示丰富的背景上下文辅助评估。核心 UI 组件包括：

1.  **Search Mode (搜索模式)**：指明搜索是在网页浏览器（Web Browser）中进行的，还是设备内置的本地搜索功能（On-device Search Feature）。评估时必须关注产品类型。
2.  **User Location (用户位置)**：用户发起搜索时的地理位置上下文（例如：`ca/alberta/division_no._6`）。
3.  **Date (搜索日期)**：用户搜索时的具体日期（例如：`2023-07-13`），用于判定信息的时效性与新鲜度。
4.  **Web Search Link (搜索研究链接)**：提供跳转至搜索引擎的链接，供评估员调查用户查询意图。
5.  **Query (查询词)**：用户输入的具体搜索文本。
6.  **Result (搜索结果)**：待评估的内容，可能是网页、应用、地图卡片、图片组等形式。

---

## 5. 搜索词意图理解 (Lesson 6: Process in Detail)

在评估结果之前，**首要任务是彻底理解用户搜索词（Query）的真实意图**。

### 标准工作流：
1.  **点击任务界面中提供的 Web Search Link**。
2.  **浏览搜索引擎返回的搜索结果**，收集上下文并锁定查询词背后最可能的意图。

### 备用方案（若研究链接失效或未加载）：
*   **手动复制查询词**在主流搜索引擎中进行检索。
*   检查并**确保您的浏览器设置为正确的 Locale（语言和区域）**，避免因区域不同导致意图偏离。

---

## 6. 满意度评估四大原则 (Lesson 7: Satisfaction Principles)

在对搜索结果进行满意度打分时，应当以以下四个满意度要素（Satisfaction Factors）作为指导准则：

1.  **Degrees of Separation（分离度）**：衡量结果与查询词之间的概念距离。**概念距离越远，评级越低**。
2.  **Think meaning, not just words（关关注字面，更关关注意图）**：必须匹配用户的搜索意图（Intent），而不是简单地寻找包含相同关键字的结果。
3.  **User Effort（用户工作量）**：用户获取最终所需信息需要付出的劳动。**越省力（比如不用点击或点击极少），满意度越高**。
4.  **Source Quality（信息源质量）**：信息源的权威性。**倾向于选择声誉良好、编写严谨、客观中立的来源**。

---

## 7. 特殊情况与结果类型处理规则 (Lesson 8: Special Case Handling)

在不同查询类型与搜索场景下，满意度评级的标准需进行相应微调：

*   **歧义查询（Ambiguous Queries）**：
    *   如果有某一个含义明显占据主导地位（Dominant Meaning），则基于主导意图进行评估。
    *   如果没有主导意图（即有多个同样合理的解释），需要对结果进行降级：原本可以评为 Highly Satisfying 的结果应**降级评为 Satisfying**。
*   **Locale 敏感度（Locale Sensitivity）**：
    *   密切关注用户的地理位置（Location）。结果必须符合该地用户的生活常识与本地化需求。
    *   区域错配（Mismatched Locales，例如搜索本地快餐展示了其他国家的结果）会导致评级下降，甚至直接评为 **Not Satisfying**。
*   **非英语 Locale 中的英语结果（English Results in Non-English Locales）**：
    *   在非英语母语地区，返回英语结果是否满意取决于该地区对英语的普及/熟悉程度，以及该查询是否为通用英语品牌。若不适用，则需要进行降级。
*   **重定向页面（Redirected Pages）**：
    *   必须评估**最终重定向落地的页面**，而不是点击前的原始 URL。
*   **应用程序（Apps）**：
    *   判定 App 是否为官方提供、是否属于该查询在当地最常使用的应用，或是否与查询意图高度相关。
*   **新闻结果（News）**：
    *   着重评估新闻的**时效性（Timeliness）**、相关性，以及该文章是否确实在深入报道查询的主题，而非仅仅提及。
*   **地图结果（Maps）**：
    *   根据距离远近、数据准确性以及用户当时是否具有潜在的寻址/导航需求来进行评估。
*   **网络视频（Web Video）**：
    *   根据视频的密切相关性、在主流平台上的流行度以及是否符合查询的富媒体意图进行评估。
*   **垂直直答卡片（垂直领域：字典、天气、股票、知识回答/Sports/“Learn About” 查询）**：
    *   直接基于**卡片里直接展示出来的信息**是否准确和完整进行满意度判定。
*   **建议网页/普通网页（Suggested Web Sites）**：
    *   评估该网站是否为官方网站、是否高度相关，并且能否有效满足用户的搜索意图。
*   **网页图片（Web Images）**：
    *   将返回的整组图片作为一个整体进行评估，关注图片的清晰度、相关性、多样性以及是否具有独特性。
*   **产品搜索（Product Searches）**：
    *   如果目标商品处于缺货状态（Out of stock），评级高低取决于用户的搜索是针对非常具体的唯一商品（Specific），还是泛指一类商品（General）。

---

## 8. 侧对比偏好评估 (Lesson 9: Overall Preference Rating - OPR)

侧对比（OPR）是评估员在**同一个查询词**下，对比左侧（Left）和右侧（Right）两组搜索结果并判定整体偏好的过程。

> [!WARNING]
> OPR 和单侧的搜索满意度（Search Satisfaction）是两项独立的任务。它们的评估指南不能混用。如果在做单侧评估，切勿套用 OPR 的侧对比规则。

### OPR 评估步骤
1.  **评估单条结果**：首先使用单侧满意度指南，评估两边列表里每一个搜索结果的满意度级别。
2.  **确定偏好侧**：对比左右两组结果的整体表现，根据判定标准做出整体偏好选择。

### OPR 评级标尺（OPR Rating Scale）
OPR 提供以下 7 个互斥选项：
1.  **Left Much Better** (左侧好很多)
2.  **Left Better** (左侧好一些)
3.  **Left Slightly Better** (左侧稍好一点)
4.  **About the Same** (难分伯仲 / 基本一致)
5.  **Right Slightly Better** (右侧稍好一点)
6.  **Right Better** (右侧好一些)
7.  **Right Much Better** (右侧好很多)

### OPR 5 大核心准则
1.  **满意度级别更高（Higher Satisfaction Grades）**：优先偏好拥有更高满意度单条评级（如 Highly Satisfying 结果更多）的那一侧。
2.  **结果的排序（Ranking of Results）**：优先偏好将满意度更高的结果**排在越靠前位置（如 Position 1、Position 2）**的那一侧。高满意度结果在首位对偏好的正面影响极大，而在末尾（如 Position 4）的影响则较小。
3.  **结果的多样性（Variety of Results）**：优先偏好结果类型更多样（合理包含地图、App、官方网页等不同媒介类型），且能覆盖查询词多种合理潜在意图的那一侧。
4.  **结果的数量（Number of Results）**：注意，**结果的数量多并不代表那一侧更好**。低质量或重复的结果反而会扣分。
5.  **抉择困难（Difficulty Deciding）**：如果您反复对比后依然觉得很难决出优劣，或者两边优缺点完全对等，应当坚定选择 **About the Same**。

---

## 9. OPR 侧对比 12 个实战案例解析 (Lesson 10: OPR and Comment Examples)

以下为课程官方提供的 12 个侧对比实战案例，包含了具体的查询意图、位置和详细的判定逻辑。

### 案例 1：银行分支与官方信息的权衡
*   **查询词（Query）**: `tdecu` (德克萨斯教师信用合作社，一家银行机构)
*   **用户位置与日期**: Richwood, TX
*   **左右侧结果对比**:
    *   **左侧 (Left)**: 官方 TDECU 数字银行 App；TDECU 简化版贷款 App；地图直答卡片（展示 3 英里外的 TDECU 分行，带路线指引）；地图直照卡片（展示 4 英里外的分行）。
    *   **右侧 (Right)**: 官方 TDECU 数字银行 App；TDECU 简化版贷款 App；TDECU 官网首页；TDECU 官网 "About Us"（关于我们）页面；TDECU 官方 Twitter。
*   **评级结果**: **About the Same** (难分伯仲)
*   **官方解析**:
    用户的搜索意图包括进行网银交易、前往网点或获取基本信息。两边前两项结果相同，都是高满意度（Highly Satisfying）的 App。左侧提供了分行地图（满足出行需要），右侧提供了官网首页（满足线上信息获取需要）。左侧满足了 3 种搜索需求，右侧满足了 4 种（含 Twitter，但 Twitter 属于非常低频的意图）。由于无法证实用户更倾向于地图还是官网，且两边都有极强的核心结果支撑，因此评为 **About the Same**。

---

### 案例 2：错误语言结果的扣分与意图多样性
*   **查询词（Query）**: `diesel` (可能指时装品牌 Diesel，也可能指柴油)
*   **用户位置与日期**: Cambridge, MA
*   **左右侧结果对比**:
    *   **左侧 (Left)**: Diesel 英文在线商店；**Diesel 日本官方在线商店（日语页面）**；柴油（Diesel Fuel）维基百科英文页。
    *   **右侧 (Right)**: Diesel 英文在线商店；柴油（Diesel Fuel）维基百科英文页；Diesel 时装店地图结果（位于波士顿 Newbury 街，距离用户 2 英里）。
*   **评级结果**: **Right Better** (右侧好一些)
*   **官方解析**:
    此查询属于歧义词，同时指向服装品牌和燃料。两边都包含 2 个相同的英文结果。然而，左侧返回了一个**日语网站**（对美国用户来说是不懂的语言，属于 Not Satisfying）；而右侧不仅没有语言错误，还在第三位提供了一个距离用户 2 英里外的服装店地图结果（增加了结果多样性，同时覆盖了网页与地图类型）。右侧具有多项明确的优势，但因列表整体差异不是颠覆性的，故评为 **Right Better** 而不是 Much Better。

---

### 案例 3：弱相关与完全无关结果的比较
*   **查询词（Query）**: `apollo project` (阿波罗登月计划)
*   **用户位置与日期**: Cincinnati, OH | 2020-02-13
*   **左右侧结果对比**:
    *   **左侧 (Left)**: 阿波罗登月计划维基百科；阿波罗计划纪录片电影；**一首名为 "Project Apollo" 的太空致敬氛围音乐 (Apple Music)**。
    *   **右侧 (Right)**: 阿波罗登月计划维基百科；阿波罗计划纪录片电影；**阿波罗剧院（Apollo Theater, 位于哈林区）的全球视频项目 (YouTube)**。
*   **评级结果**: **Left Slightly Better** (左侧稍好一点)
*   **官方解析**:
    用户的意图是寻找 1960 年代的人类登月计划。两边的前两个结果完全一致。差异在于第三个结果：左侧是一个致敬登月计划的太空主题氛围音乐，虽然比较冷门，但至少主题上和登月有微弱的关联（Slightly Satisfying）；而右侧则是纽约阿波罗剧院的视频，与登月计划毫无关系（Not Satisfying）。既然只有最后一项结果不同，且左侧的不良结果比右侧的完全无关结果“危害更小”，因此左侧 **Slightly Better**。

---

### 案例 4：直答卡片（零工作量）的巨大优势
*   **查询词（Query）**: `best actor winner` (最佳男主角得主)
*   **用户位置与日期**: Bellevue, WA | 2020-02-13
*   **左右侧结果对比**:
    *   **左侧 (Left)**: 历届奥斯卡男主角及男配角获奖者页面（网页，需下滑到底部才能找答案）；安迪·瑟金斯 2011 年的男主角提名粉丝视频；Ranker 网站上关于“处女作即获得奥斯卡的最佳男演员”列表。
    *   **右侧 (Right)**: **华金·菲尼克斯（Joaquin Phoenix）荣获 2020 年奥斯卡最佳男主角直答信息卡（免点击直达答案）**；历届奥斯卡获奖者页面；华金·菲尼克斯因同一角色获得金球奖的视频。
*   **评级结果**: **Right Much Better** (右侧好很多)
*   **官方解析**:
    由于搜索时间是 2020 年 2 月 13 日（奥斯卡颁奖典礼刚结束几天），用户极度渴望知道最新一届的获奖者（华金·菲尼克斯）。左侧第一位虽然有答案，但需要用户点击并滑动很久才能看到；而右侧第一位直接展示了获奖者的直答卡片，实现了**零工作量获取信息（User Effort 极小，Highly Satisfying）**。此外，左侧的第二、三位结果是陈旧或无关的，而右侧提供了该演员获金球奖的补充视频（相关性高）。基于直答卡片带来的突破性体验和结果质量的全面领先，右侧 **Much Better**。

---

### 案例 5：内容多样性与官方链接的偏好
*   **查询词（Query）**: `anthony ramos` (美国演员/歌手，曾出演音乐剧《汉密尔顿》)
*   **用户位置与日期**: Fairfax, VA | 2021-04-17
*   **左右侧结果对比**:
    *   **左侧 (Left)**: 维基百科页；2021 年新歌 "Lose My Mind" 官方MV；2021 年歌曲 "Blessings" 官方MV；2021 年新歌 "Say Less" 官方MV。
    *   **右侧 (Right)**: **安东尼·拉莫斯官方网站**；"Lose My Mind" 官方MV；NBC 关于他的新闻报道（2021-02）；**安东尼·拉莫斯官方 Instagram 主页**。
*   **评级结果**: **Right Better** (右侧好一些)
*   **官方解析**:
    两边均包含高满意度的结果。但左侧除了维基百科外，几乎全都是他的单曲音乐视频（信息冗余且单一）；而右侧不仅提供了最核心的**官方网站**（Highly Satisfying），还提供了新闻和官方社媒 Instagram 账号（满足了用户多样化的探索需求）。右侧在广度与官方权威度上表现更好，判定为 **Right Better**。

---

### 案例 6：无主导意图的多样无用信息对比
*   **查询词（Query）**: `dana` (多义词，人名/品牌)
*   **用户位置与日期**: Hampton, VA | 2021-08-17
*   **左右侧结果对比**:
    *   **左侧 (Left)**: 印尼数字钱包 DANA 应用程序；尼日利亚达纳航空（Dana Air）官网首页；Now United 组合的单曲 "Dana Dana" 视频。
    *   **右侧 (Right)**: 德纳股份有限公司（Dana Inc., 生产乘用车传动零件的公司）官网；以色列歌手 Dana International 在 1998 年欧洲歌唱大赛的视频；韩国女歌手 Dana 的维基百科页。
*   **评级结果**: **About the Same** (难分伯仲)
*   **官方解析**:
    该查询词是一个极度分散、没有主导意图的多义词。对美国弗吉尼亚州的用户来说，印尼电子钱包、尼日利亚航空、以色列三十年前的歌手、韩国小众明星，都属于极低概率的检索目标（全部都是 Somewhat Satisfying 或 Not Satisfying）。由于两边都没有任何一个能够真正匹配本地主流意图的结果，且质量同样平庸，因此两边 **About the Same**。

---

### 案例 7：根据日期推断最新排名的重要性
*   **查询词（Query）**: `tina turner movie` (蒂娜·特纳电影/纪录片)
*   **用户位置与日期**: Kansas City, MO | 2021-08-17
*   **左右侧结果对比**:
    *   **左侧 (Left)**: 1985 年电影《疯狂的麦克斯3》（蒂娜联合主演）；1993 年自传电影《爱又如何》；**2021 年 HBO 最新热播纪录片《蒂娜》（Tina）介绍页**。
    *   **右侧 (Right)**: **2021 年 HBO 最新热播纪录片《蒂娜》（Tina）介绍页**；1993 年自传电影《爱又如何》；1985 年电影《疯狂的麦克斯3》。
*   **评级结果**: **Right Better** (右侧好一些)
*   **官方解析**:
    两边展示的结果列表完全相同，唯一的区别是**排序（Ranking）**。考虑到搜索时间是 2021 年 8 月，2021 年上映的 HBO 最新个人纪录片《蒂娜》绝对是当下热度最高、最符合用户寻新意图的结果。右侧将这个最高满意度的结果排在第 1 位，而左侧将其放在第 3 位。由于排序更优，右侧 **Right Better**。

---

### 案例 8：消除低价值重复信息
*   **查询词（Query）**: `hannah waddingham` (英国女演员，因出演《泰德·拉索》知名)
*   **用户位置与日期**: Dickinson, TX | 2021-09-22
*   **左右侧结果对比**:
    *   **左侧 (Left)**: 关于她在 2021 年艾美奖凭借《泰德·拉索》获奖的新闻 A；网站展示的 2021 年艾美奖完整获奖名单。
    *   **右侧 (Right)**: **汉娜·沃丁厄姆的 IMDb 职业档案主页**；关于她艾美奖获奖的新闻 B（不同媒体报道）。
*   **评级结果**: **Right Better** (右侧好一些)
*   **官方解析**:
    两边都包含时效性极佳的新闻报道（2021年9月22日紧邻艾美奖颁奖礼）。然而，左侧的第二位是艾美奖的通盘获奖名单，对专门搜索该女演员的用户来说，信息过于宽泛。右侧第一位给出了该女演员的官方 IMDb 页面，这对于搜索人名的用户是绝佳的常青树信息源（Highly Satisfying）。右侧的结构是“核心个人档案页 + 最新新闻”，排序极其科学，故评为 **Right Better**。

---

### 案例 9：特定版本与泛化版本的匹配
*   **查询词（Query）**: `monster hunter stories 2` (怪物猎人物语2，一款电子游戏)
*   **用户位置与日期**: Miami, FL | 2021-08-10
*   **左右侧结果对比**:
    *   **左侧 (Left)**: 怪物猎人物语系列维基词条（整体系列介绍，偏概括）。
    *   **右侧 (Right)**: 维基百科上的《怪物猎人物语2：毁灭之翼》专有词条（**指向第 2 代精确游戏**）。
*   **评级结果**: **Right Better** (右侧好一些)
*   **官方解析**:
    用户明确在搜索“第 2 代”游戏。左侧返回的是系列通用网页，用户仍需在里面寻找 2 代的内容；右侧直接返回了 2 代的专属页面，匹配度最高（Highly Satisfying）。所以右侧更好。但如果右侧在此基础上能加入 2 代的官方网站或多样化的评测，才能达到 Much Better 的级别，故最终判定为 **Right Better**。

---

### 案例 10：卡片与外链质量的权衡（微弱优势）
*   **查询词（Query）**: `audra mcdonald` (美国女歌手/演员)
*   **用户位置与日期**: Bergen, NJ | 2021-09-22
*   **左右侧结果对比**:
    *   **左侧 (Left)**: 歌手简短知识卡（包含官网和 Twitter 链接）；她一首不太有名的老歌 "My Man's Gone Now" (2007) 的网页视频；另一首歌曲 "Rainbow High" 的网页视频。
    *   **右侧 (Right)**: 歌手简短知识卡；**Audra McDonald 官方网站（直达网页结果）**；**官方 Twitter 账号页面**。
*   **评级结果**: **Right Slightly Better** (右侧稍好一点)
*   **官方解析**:
    两边首位都有相同的歌手知识卡。左侧第二、三位返回了两个相对冷门的歌曲视频；右侧则返回了非常高权威的官网和 Twitter 外链（虽然知识卡里也有，但单独作为列表结果展示依然拥有很高的满意度分值）。由于右侧的外链权重显著高于左侧的非主打歌曲视频，因此右侧偏好。但鉴于右侧完全缺失了任何视频展示（用户可能也想听歌），这限制了其偏好幅度，故右侧仅为 **Slightly Better**。

---

### 案例 11：不良结果与排名的综合负面效应
*   **查询词（Query）**: `sunrise` (日出 / 日出时间)
*   **用户位置与日期**: West Melbourne, FL | 2021-09-01
*   **左右侧结果对比**:
    *   **左侧 (Left)**: **West Melbourne 本地日出/日落时间的天气直答卡片**；App Store 里的日出日落时间应用下载链接；关于日出（Sunrise）物理现象的知识卡。
    *   **右侧 (Right)**: **一个正在出售 `http://www.sunrise.am` 域名的垃圾广告网站**；West Melbourne 本地日出时间天气直答卡片；关于日出的知识卡。
*   **评级结果**: **Left Better** (左侧好一些)
*   **官方解析**:
    用户很可能是想了解当地今天的日出时间。两边都包含日出时间的直答卡片（Highly Satisfying），但左侧将其排在第 1 位（最佳体验），而右侧却将其排在第 2 位。右侧将第 1 位分配给了一个**出售域名的广告网站**，这对普通用户完全没有价值（Not Satisfying），属于严重的体验扣分。左侧排序更佳且无垃圾广告干扰，因此左侧 **Left Better**。

---

### 案例 12：地域属性与核心官网的优劣
*   **查询词（Query）**: `huffington post` (赫芬顿邮报，美国知名新闻网站)
*   **用户位置与日期**: Paxtonia, PA | 2021-09-22
*   **左右侧结果对比**:
    *   **左侧 (Left)**: 赫芬顿邮报主站官方网站；官方 Twitter 账号页。
    *   **右侧 (Right)**: **赫芬顿邮报英国分站（UK Site）官网**；赫芬顿邮报官方新闻 App 下载链接。
*   **评级结果**: **Left Better** (左侧好一些)
*   **官方解析**:
    用户位于美国宾夕法尼亚州，搜索一个知名美国媒体。左侧第一位给出了美国主站的官网（Highly Satisfying）；而右侧第一位给出了**英国分站**。对于美国本地用户，英国分站的内容与其地域属性不符，仅属于 Somewhat Satisfying。左侧提供了最完美的美国官方主站，即使结果数量只有 2 个也显著优于右侧。故左侧 **Left Better**。

---

## 10. 技术支持与沟通方式 (Lesson 12: Communication and Contact)

如果评估员在工作或认证考试期间遇到任何技术故障或管理问题，应通过电子邮件联系 Centific 团队。

### 📧 联络邮箱（按区域划分）：
*   **亚太地区支持（Asia Hub）**：`DGS_Milkyway_Asiahub@centific.com`
*   **美国地区支持（US Hub）**：`DGS_Milkyway_UShub@centific.com`
*   **欧洲地区支持（EU Hub）**：`DGS_Milkyway_EUhub@centific.com`

### ✉️ 邮件主题格式（必须一字不差）：
1.  **邮件主题格式**：`MilkyWay/Lightspeed :: QA`
    *(此格式用于系统后台的自动分流与优先级排队，请务必保证格式完全正确。)*
2.  **正文必备要素**：
    *   清晰、简洁地描述您的问题。
    *   提供相关的背景上下文、具体的例子或任务 ID（Request ID）。
    *   附上必要的截图或错误信息附件。
    *   **合并问题**：尽量将多个疑问汇总到一封邮件中提交，以减少往复沟通的时间消耗。

---

## 11. 认证考试须知 (Lesson 13: Next Steps & Lesson 2)

在系统学习本课程后，评估员将进入认证考试环节：

*   **考试入口**：在 OneForma 中点击 **PROCEED TO EXAM**。
*   **参考资料**：在答题时，**可以并且推荐**随时参考 Document Reference Library 中的官方指南（GL）、本培训课程记录以及自己记录的笔记。
*   **题目数量**：考试包含 **30 道随机选择题**。请务必仔细阅读每一道题。
*   **答题连贯性**：建议在**一次会话中连续完成所有题目**。如果在未完成时强行退出，将**直接消耗一次考试机会**。
*   **尝试机会与及格标准**：
    *   共有 **2 次考试尝试机会**。
    *   及格分数线为 **80%** (即至少答对 24 道题)。
*   **网络提示**：由于数据加载，题目切换之间可能存在短暂延迟，请耐心等待，勿频繁刷新页面。
