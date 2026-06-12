# Writing Tools Proofread Feedback & RCA 中文汇总总结手册

本手册是对 **Proofread (校对)** 任务中所有历史反馈、QA 日志及 RCA（根因分析）文档的深度汇总与提炼。旨在为标注员提供一份最完整、最权威、极具可操作性的中文做题指导，帮助规避在认证与实际做题中的所有“雷区”。

---

## 目录

1. [核心原则与根本定义](#1-核心原则与根本定义)
2. [维度判定详解与黄金准则](#2-维度判定详解与黄金准则)
   - [Instruction Following (IF - 指令遵循)](#instruction-following-if---指令遵循)
   - [Composition (写作质量)](#composition-写作质量)
   - [Groundedness (忠实度)](#groundedness-忠实度)
   - [Localization (本地化)](#localization-本地化)
   - [Satisfaction (满意度)](#satisfaction-满意度)
3. [多语种本地化避坑指南与 RCA 案例分析](#3-多语种本地化避坑指南与-rca-案例分析)
   - [it-IT (意大利语)](#it-it-意大利语)
   - [da-DK (丹麦语)](#da-dk-丹麦语)
   - [pt-PT / pt-BR (葡萄牙语)](#pt-pt--pt-br-葡萄牙语)
   - [sv-SE (瑞典语)](#sv-se-瑞典语)
   - [ja-JP (日语)](#ja-jp-日语)
   - [zh-CN / zh-TW / zh-HK (中文)](#zh-cn--zh-tw--zh-hk-中文)
   - [tr-TR (土耳其语)](#tr-tr-土耳其语)
   - [vi-VN (越南语)](#vi-vn-越南语)
   - [nb-NO (挪威语)](#nb-no-挪威语)

---

## 1. 核心原则与根本定义

> [!IMPORTANT]
> **Proofreading (校对) ❌ Paraphrasing / Rewriting (改写/重写)**
> 
> 在 Proofread 任务中，模型（Assistant）的唯一职责是**修正客观语法、拼写、标点和排版错误**，同时**最大限度保留原始文本（Minimal Edit Principle - 最小编辑原则）**。
> - 绝对禁止无故改写句子结构、替换近义词、调整语气/风格或进行润色。
> - 即使原句读起来不太通顺（Poor Phrasing），只要语法 and 拼写无客观错误，模型也**必须原封不动保留**。
> - 严禁修正原句中的**事实性错误（Factuality Errors）**。例如，如果原句说 "Shawn Mendes 唱了 Señorita" 或包含其他不符合科学事实的陈述，绝对不能修改其事实内容。

---

## 2. 维度判定详解与黄金准则

### Instruction Following (IF - 指令遵循)

指令遵循是评估模型是否严格按照校对要求处理文本。其判定标准具有极强的“离散性”：

*   **Fully Following (完全遵循)**：
    *   **情况 A：模型完美纠正了输入中的所有错误，没有引入任何多余修改。**
    *   **情况 B (易错点)：模型做出了【完全一致的复制】（Exact Repeat）。即使输入文本里满是错误，只要模型没有改动一个字（包括标点、空格），在 IF 维度上也必须判定为 `Fully Following`。**
    *   *注*：如果输入本身无错误，模型完全复制，自然也是 `Fully Following`。
*   **Partially Following (部分遵循)**：
    *   **少改/漏改**：输入有 5 处错误，模型只改了 4 处，漏掉 1 处。
    *   **多改（无谓修改）**：模型修改了拼写错误，但同时也无故删减了词语、替换了同义词（例如将 "hey" 改为 "hi"）、无故更改了正式度或语气。
    *   *注*：只要保留了原句的基本意图（Intent），但有上述偏离，即判定为 `Partially Following`。
*   **Not Following (未遵循)**：
    *   **彻底改写**：模型直接对原句进行了大范围 Paraphrasing，改变了句式或叙述视角（如从自述改为称呼他人），导致原意改变。
    *   **越界修改事实**：修正了输入中的客观事实错误（如科学常识）。

---

### Composition (写作质量)

写作质量侧重于响应（Response）本身的语言质量和错误修复度。

| 评分等级 | 核心条件 | 典型场景 |
| :--- | :--- | :--- |
| **Good (优)** | 所有错误均被完美修复，且**无任何语气、风格改变，也无无谓修改**；或者输入本身无错，模型做出了完美复制。 | 输入：`I go to school` -> 响应：`I go to school` (Good)<br>输入：`I goes to scool.` -> 响应：`I go to school.` (Good) |
| **Acceptable (良)** | 修复了部分错误但仍有残留；或者虽然修复了错误，但伴随有**轻微句式变动/无谓词语替换**；或者响应的格式/结构被修改。 | 输入有 5 个错，漏改 1 个 (Acceptable)；<br>错误修复了，但把 "Tô viciado" 换成了更正式的 "Tô viciado também..." (Acceptable)。 |
| **Bad (劣)** | **引入了新错误（任何拼写、语法、标点、多余冠词或主谓不一致）**；或者几乎没做任何修正；或者语气/风格发生了剧烈变化。 | 只要响应里出现了模型自己制造的新错误，**直接判定为 Bad**！<br>或者模型复制了一个满是错误的原句（Exact Repeat 且有错 -> Bad）。 |

---

### Groundedness (忠实度)

评估响应是否忠实于输入，没有发生信息偏移或幻觉。

*   **Fully Grounded (完全忠实)**：原意没有受到任何微调。注意，校对不需要改写词语。
*   **Partially Grounded (部分忠实)**：发生了轻微的语义漂移。
    *   *例*：输入 `it should be reviewed` 被改写为被动改主动 `we should review it`，这改变了动作主体，应判为 `Partially Grounded` 并降低 IF。
    *   *例*：无故改变了动词时态、语法性/数（单复数）。
*   **Not Grounded (不忠实)**：响应的内容完全脱离了原意，甚至自相矛盾。

---

### Localization (本地化)

评估响应是否符合目标语言的本地规范。

*   **判定界限**：拼写、语法、标点在校对任务中**只有在“目标 locale 错误但其他 locale 正确”时，才算 Localization 错误**！如果它在所有 locale 都是通用语法错误，那就是 Composition 问题，不要混淆。
*   *例*：丹麦语问候语后不能加逗号（加了是 Localization 问题）；中文必须用全角标点；挪威语应使用专属的引号（`« »` 或 `“ ”` 规范）。

---

### Satisfaction (满意度)

满意度是各维度判定结果的级联体现。

*   **Highly Satisfying (高度满意)**：所有维度均为 Good 且无瑕疵。
*   **Satisfying (满意)**：有极其轻微的无谓修改，但无语法错误残留。
*   **Slightly Unsatisfying (轻微不满意)**：存在部分未修复的错误，或者引入了无谓词语、风格、语气变化。
*   **Highly Unsatisfying (高度不满意)**：**未能修正原句中的核心错误**，或者**引入了新的语法/拼写错误**，或者响应是vulgar（粗俗有害）的内容。

---

## 3. 多语种本地化避坑指南与 RCA 案例分析

### it-IT (意大利语)

1.  **代词微调带来的语义变化 (Groundedness & Composition)**:
    *   *输入*：`venirmi` (到我这来) 
    *   *错误响应*：改成了 `venire` (来)，丢失了代词 `mi`。
    *   *判定*：**Groundedness 降级**（未忠实表达“我”的语义），**Composition 降级**。
2.  **拼写与排版残留 (IF & Composition)**:
    *   *案例*：`anullato` 未修正为正确拼写 `annullato`。
    *   *判定*：漏改拼写，IF 判定为 `Partially Following`，Localization 判定受损。
    *   *标点间距*：问号 `?` 前面的空格未清理，或 `tenuto` 前面有双空格残留。模型漏掉这些细节，必须判定为 `Partially Following` 和 `Acceptable Composition`。
3.  **引言符号规范**:
    *   使用意大利语本地双引号时需留意。另外，如果输入的前后带有包裹代码块的三个反引号 ` ``` ` 或字体样式改变，**直接忽略反引号及字体颜色/样式的干扰，仅聚焦于文本本身的纠错**。

---

### da-DK (丹麦语)

1.  **问候语后加逗号 (经典 Localization 雷区)**:
    *   *案例*：`Hej Morten` (你好 Morten)
    *   *模型响应*：`Hej Morten,` (无故在后面补了逗号)。
    *   *规范*：**在丹麦语标准语法中，问候语后面绝对不能紧跟逗号**。模型无故添加逗号属于**引入 Localization 错误**，Composition 必须判定为 `Bad` 或 `Acceptable`，同时 IF 降为 `Partially Following`。
2.  **冠词不一致导致的 Bad Composition**:
    *   *输入*：`... www.peepo.com, også et grafisk hjælpemiddel til at browse på internettet. Det er designet til... Når du ser et interessant link, klikker du på den.`
    *   *模型错误响应*：将最后的 `klikker du på den` 改成了 `klikker du på det`（认为代指 link），但前面有一处将指代 `hjemmeside` 的词弄错了。
    *   *规范*：`hjelpemiddel` 对应的冠词是 `et`，代词应为 `Det`。若模型无故改写导致性数代指断裂，属于**引入新错误，判定为 Bad Composition**。
3.  **拼写与标点**:
    *   `nogen` 与 `nogle` 的混用纠正。
    *   漏掉缺失的逗号（例如：`gået noget tid, siden der ...`）导致 Composition 只能给 `Acceptable`。

---

### pt-PT / pt-BR (葡萄牙语)

1.  **缺失单词的处理原则 (RCA 经典案例)**:
    *   *输入*：`E como eu falei, eu te Rachel por todas as coisas extras.` (显然，`te` 和 `Rachel` 之间缺失了一个动词，原句语义不全)
    *   *模型响应的处理与判定*：
        *   **如果模型擅自添加了一个动词**（如添加 `agradeço`）来让句子通顺：**IF 降级为 Partially Following** (属于无谓词语修改)；**Groundedness 降级**。
        *   **如果模型做出了 Exact Repeat (完全复制)**：**IF 必须给 Fully Following**！但 **Composition 降级为 Bad**（因为保留了致命的结构缺失错误），**Satisfaction 判定为 Highly Unsatisfying**。
2.  **正式度与口语词汇 (pt-BR)**:
    *   巴西口语日常用词如 `elegantérrimo` (极优雅的) 和 `rapidão` (极快的) 尽管不是官方最严谨的变格，但是在 pt-BR 日常口语场景中是**完全被允许且不需要被纠正的**。
    *   *雷区*：如果模型擅自将口语的 `pra` 修改为正式的 `para`，或者无故调整口语词，属于**无谓修改（Unnecessary Modification），IF 必须判定为 Partially Following**。
3.  **语序与冠词无谓改写 (pt-PT)**:
    *   *语序无谓调整*：`Tô viciado também no álbum novo...` 被模型改为 `no novo álbum`。虽然两者都对，但原句无错，模型此举属于无谓修改，降级。
    *   *无谓添加冠词*：在日期 `dia 12` 前无故添加定冠词 `o`。pt-PT 中日期作为时间状语时不需要冠词，此举为无谓修改。
    *   *协调并列句逗号*：在 `não tenho sorte no jogo, e só fumei…` 中，如果并列句的主语没有发生改变，`e` 前面是不需要逗号的。模型添加逗号属于**引入新标点错误**。

---

### sv-SE (瑞典语)

1.  **复合词拼写 (S-joiner)**:
    *   *案例*：`lördagkväll` (星期六晚上)
    *   *规范*：瑞典语拼写中，`lördag` 与 `kväll` 复合时，**中间必须加上连接字母 `s`**，写成 `lördagskväll`。
    *   *判定*：模型若漏改此类复合词（如保留 `lördagkväll` 或保留 `Icakassas` 的拼写错误），Composition 只能判定为 `Acceptable`，IF 判定为 `Partially Following`。
2.  **专有名词与范畴词的首字母大写**:
    *   根据瑞典语语法，特定范畴和分类名词在特定上下文中**不需要/需要**首字母大写。模型若混淆，需严格对照语法降级。

---

### ja-JP (日语)

1.  **无故转换书写系统 (Script Change)**:
    *   *案例*：模型在无任何语法拼写理由的情况下，将输入文本中的平假名无故转为片假名（Katakana），或反之。
    *   *规范*：**这是 ja-JP 判定中明确禁止的越界行为。必须在 IF 维度上 penalize 并降为 Partially Following**。
2.  **无谓添加助词**:
    *   *案例*：原句很流畅，模型无故插入提示助词 `は`。此举改变了句子的强调重心与语气，判定为 **Partially Following**。
3.  **残留助词缺失导致的 Composition 降级**:
    *   *案例*：输入中缺少格助词 `の`（如 `直行南行き便` 缺少 `の` 写成了 `直行南行き便`）。模型响应做出了 Exact Repeat。
    *   *判定*：由于是 Exact Repeat，**IF 为 Fully Following**。但由于致命助词缺失错误未被修复，**Composition 降级为 Acceptable**。
4.  **时态与语态的语义偏移**:
    *   *案例*：将表示过去或进行状态的 `行ってた` 无故修改为 `行っています`。
    *   *判定*：时态变化改变了原意，**Groundedness 降级，IF 降为 Partially Following**。

---

### zh-CN / zh-TW / zh-HK (中文)

#### zh-CN (简体中文)
1.  **“您”与语气改写**:
    *   若输入文本包含敬称 `您`，模型在响应中无故删去 `您` 或改为 `你`，属于**严重破坏风格和正式度的行为，判定为 Partially Following**。
2.  **无谓的词汇润色**:
    *   *错误案例*：将 `只程序性` 改写为 `进行程序性`；将 `问题` 改写为 `提问`；将 `描绘` 改写为 `动物园`。
    *   *规范*：这些属于改写而非校对，判定为 **Partially Following** 且 **Composition 判定为 Acceptable 或 Bad**。
3.  **全角标点与连续句号 (经典雷区)**:
    *   *案例*：输入文本中出现连续三个句号 `。。。`。
    *   *规范*：**中文的省略号标准规范是 `……`（居中六点）。模型必须将 `。。。` 修正为 `……`**。如果未修正，属于 **Localization 错误**。
4.  **混杂非目标语言与多余空格**:
    *   将 `see` 改变为中文但未合理对齐；专有名词首字母或 Emoji/符标（如 `🆘`、`8️⃣`）后面无故出现多余的半角空格，皆属于 Localization 和标点细节失分项。

#### zh-TW (繁体中文)
1.  **过度生成 (Overgeneration)**:
    *   *案例*：输入為 `幫他找到了洋裝`，模型响应改为 `幫她找到完美的洋裝`。
    *   *分析*：虽然修正了 `他` -> `她`，但原句根本没有 `完美的` 这三个字。**无故添加修饰词属于 Overgeneration，IF 必须降为 Partially Following**。
2.  **功能描述中的时态残留**:
    *   *案例*：描述儿童牙刷的功能，“播放了兩分鐘的音樂”。这里的 `了` 表示动作已发生，但牙刷功能应为客观描述，应去掉 `了` 变为 `播放兩分鐘的音樂`。若模型未修正，Composition 只能给 `Acceptable`。
3.  **全角逗号 `，` 与半角逗号 `,` 的混用**:
    *   在中文语境中，**必须使用全角逗号 `，`**。如果模型响应中残留了半角逗号 `,`，属于 Localization 错误。

#### zh-HK (粤语繁体)
1.  **方言别字修正对照**:
    *   粤语中特定的错别字有标准对应关系，必须严格修正：
        *   `特燈` ❌ -> `特登`   (特意)
        *   `震作` ❌ -> `振作`   (振作)
        *   `廢事` ❌ -> `費事`   (免得)
        *   `它`  ❌ -> `佢`    (他/她/它 - 指代人或动物时)
2.  **CS 缩写与代词误改**:
    *   *输入*：`聯絡 Safemoon CS 支緩團隊啦` (联系 Safemoon 客服支持团队)
    *   *模型响应*：改写为 `聯絡 Safemoon CS 支客服團隊啦`。
    *   *分析*：将支持团队误改成了“客服团队”，并错误地将 `CS` 当作专有名词的前缀，严重改变了原句含义。**判定为 Not Following**。
    *   *代词修改*：将粤语中语义顺畅的 `俾返` 无故改写为 `買返`，或将 `呢道` 无故改为 `呢份`，改变了原意，**Groundedness 降级**。

---

### tr-TR (土耳其语)

1.  **口语缩写与残留错误**:
    *   *输入*：`Korkuyorum, ozaman bu diziyi kulakla dinlemek pekde iyi bi fikir diyil.`
    *   *模型响应*：修正了大部分错误，但**保留了口语化词汇 `bi`**（应为 `bir`）。
    *   *判定*：由于拼写残留，**Composition 只能给 Acceptable**。
2.  **代词误改**:
    *   将 `davrandığını` (你的行为) 无故改成 `davrandığımı` (我的行为)，彻底改变了人称和语义。**Groundedness 降级**。
3.  **自然流畅度与冗余修饰**:
    *   *案例*：输入 `Bizim ekipimiz` (我们团队)，虽然语法通，但在土耳其语中，`Bizim` 是冗余的，直接说 `Ekibimiz` 更加自然。如果模型没有优化或优化过度，需仔细权衡其流畅度。

---

### vi-VN (越南语)

1.  **时态副词误纠**:
    *   *案例*：将 `sẽ` (将要) 纠正为 `đã` (已经) 是符合上下文逻辑的，但模型响应中**遗留了标点前面的多余空格 ` ạ ?`**。
    *   *判定*：由于排版空格错误未被修正，**IF 降为 Partially Following**。
2.  **无故添加修饰词 (Unnecessary Wording Change)**:
    *   *输入*：`được báo bởi anh ấy`
    *   *模型响应*：改为 `được báo trước bởi anh ấy` (无故加了 `trước` - 提前)。
    *   *判定*：属于无谓修改，**Composition 判定为 Acceptable**。

---

### vi-VN 和其他 locale 对比:
*   多余空格的微调必须高度敏感。

---

### nb-NO (挪威语)

1.  **复合词拼写不一致**:
    *   *案例*：`katt unge` (小猫)
    *   *规范*：挪威语中，这必须合并拼写为一个词 `kattunge`。
    *   *残留判定*：模型修正了 `kattunge`，但是**句子开头首字母未大写，句末缺失句号**。模型未修正这些最基础的拼写标点错误，属于 Partial 修复，**IF 降为 Partially Following，Composition 降为 Acceptable**。
2.  **无谓添加连接词**:
    *   *案例*：在校对过程中，无故在句子中添加了挪威语关系代词 `som`。
    *   *判定*：这属于改写句式，**IF 判定为 Partially Following**。
3.  **挪威语标准引号使用规范**:
    *   在挪威语中，必须使用法式尖括号 `« »` 或标准的挪威语双引号。若响应使用了美式双引号且未作修正，属于 Localization 错误。

---

## 4. 结语

本手册结合了自 2025 年 11 月至 2026 年 2 月校对任务的所有真实 RCA 案例，旨在帮助各位标注员在面对任何 locale 的任务时，都能精准把握 **“最小编辑原则”**、**“Exact Repeat 完全复制时 IF 判定”** 以及 **“新错误引入直接判定 Bad Composition”** 这三大核心铁律。请在每次进行做题或Dry-run验证前，对照本手册的特定语言条款进行仔细校对。
