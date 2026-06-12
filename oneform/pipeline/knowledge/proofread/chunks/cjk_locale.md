# CJK Locale Rules (zh-CN, zh-TW, zh-HK)

## zh-CN (Simplified Chinese)

### Trap 1: Honorific Deletion (Severe Style Violation)
- If input uses `您` (formal "you"), model must NOT change it to `你` or delete it
- Changing `您` -> `你` = severe formality/style destruction
- Penalty: alteredMeaning = Yes / Correctness = some_unnecessary

### Trap 2: Synonym Polishing (Rewriting, Not Proofreading)
- Examples: `只程序性` -> `进行程序性`; `问题` -> `提问`; `描绘` -> `动物园`
- Original may not be elegant but has no grammar error
- This is paraphrasing, violates Minimal Edit Principle
- Penalty: Correctness = some_unnecessary

### Trap 3: Ellipsis Punctuation `。。。` -> `……`
- Chinese standard ellipsis is full-width `……` (centered six dots)
- Model MUST correct `。。。` to `……`
- If not corrected = Localization error, counts toward Completeness miss

### Trap 4: Necessary Word-Order Correction (May 22 Calibration)
- Input: `别用力过猛一上来就。` (completely garbled word order)
- Correct fix: `别一上来就用力过猛。`
- This reordering is NECESSARY objective correction, not polishing
- Correctness = all_necessary

### Trap 5: Semantic Contradiction Miss (May 22 Calibration)
- Input: `我刚订好位子，但还没订到` (logical contradiction: "just booked" vs "haven't booked")
- If model misses this = Completeness downgrade
- If 1 of 6+ total errors: nearly_complete; missedErrors: awkward_edits

---

## zh-TW (Traditional Chinese / Taiwan)

### Trap 1: Modifier Overgeneration
- Input: `幫他找到了洋裝` -> Model: `幫她找到完美的洋裝`
- Fixed `他`->`她` (necessary) BUT added `完美的` (invented modifier, not in original)
- Adding content that does not exist in input = Overgeneration
- Penalty: Correctness = some_unnecessary

### Trap 2: Tense Aspect Marker Residual
- Describing objective product features: `播放了兩分鐘的音樂`
- The `了` implies completed action; objective description should be timeless `播放兩分鐘的音樂`
- If model misses this: Completeness = nearly_complete at best

### Trap 3: Full-Width / Half-Width Punctuation
- zh-TW MUST use full-width comma `，` not half-width `,`
- Half-width comma in response = Localization error

### Trap 4: Micro-Change Q2 Judgment (May 22 Calibration)
- `API回應` -> `API 回應` (added CJK-Latin space)
- `「redis"` -> `「redis」` (paired quotation marks)
- `建议吗` -> `建議嗎` (simplified -> traditional conversion)
- ALL of these count as edits: Q2 = has_edits, absolutely no exception
- Even the tiniest formatting/spacing difference = Q2 must be Yes

### Trap 5: Redundant Pronoun & Character Corrections (May 22 Calibration)
- `請大家們注意` -> `請大家注意` (removed redundant plural marker `們`)
- `几十` -> `幾十` (simplified -> traditional)
- `便色` -> `變色` (typo fix)
- `不懂的珍惜` -> `不懂得珍惜` (auxiliary word fix)
- All are hard grammar/character corrections, fully necessary
- Correctness = all_necessary

---

## zh-HK (Hong Kong Cantonese)

### Trap 1: Dialect Character Standard Corrections
Must recognize and verify these Cantonese-specific corrections:
- `特燈` -> `特登` (meaning: deliberately)
- `震作` -> `振作` (meaning: cheer up)
- `廢事` -> `費事` (meaning: might as well not / to avoid trouble)
- `它` -> `佢` (when referring to person in Cantonese context)
- `我既意見` -> `我嘅意見` (possessive particle correction)
- `立埸` -> `立場` (stroke typo correction)
- `你係不是` -> `你係咪` (mixed Mandarin/Cantonese -> pure Cantonese question form)

### Trap 2: CS/Customer Service Terminology
- Input: `聯絡 Safemoon CS 支緩團隊啦` (CS support team)
- Bad model output: `聯絡 Safemoon CS 支客服團隊啦` (nonsensical merge)
- Model incorrectly split CS abbreviation and created gibberish
- Penalty: severe error

### Trap 3: Oral Pronoun Alteration
- Changing `俾返` to `買返` or `呢道` to `呢份` changes the action/object entirely
- These are NOT corrections -- they are meaning alterations
- Penalty: Correctness penalized, alteredMeaning if Q1=no_errors

### Trap 4: Hidden Preposition Misuse (May 22 Calibration)
- `純粹喺我既意見` -- the `喺` is WRONG here
- `喺` = "at/in" (location), but the meaning here is "is" -> must be `係`
- Correct: `純粹係我嘅意見`
- If model misses `喺` -> `係`: Completeness = nearly_complete (1 of 5-6 errors)
- missedErrors: poor_word_usage
