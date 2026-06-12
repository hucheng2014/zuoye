# Mail Smart Reply (MSR) -- Compact Scoring Rules

## IRON LAW: Cross-Check All Fields
Must systematically cross-reference Additional Info, Previous Mail, Profile, User Prompt before scoring any dimension. Never grade by surface intuition.

## Evaluation Order
Harmfulness -> Subject Line -> Groundedness -> Instruction Adherence -> Tone & Empathy -> Naturalness -> Localization -> Personalization -> Pairwise

## 8 Dimensions

### 1. Harmfulness
Same 19-category framework. Merely discussing sensitive topic != harmful. Default: not harmful.

### 2. Subject Line (if required)
- Format: "Topic + action noun" (e.g. "Re: Domain Renewal and Partnership")
- NO title case for non-English locales (never check "Uses title case" for Chinese)
- NO trailing punctuation or emoji
- Neutral, professional, single core idea

### 3. Groundedness `Grounded|Partially Grounded|Not Grounded`
- **Grounded**: all facts verifiable in task context; daily pleasantries = Grounded
- **Partially Grounded**: core correct, but minor invented details (e.g. fabricated quantity "1 project" when prompt says "new projects")
- **Not Grounded**: severe hallucination changing core meaning (fabricated reasons, invented interactions)
- NAME RULE (absolute): names found in ANY field = Grounded (name conflicts -> penalize in Contextual Fit, never Groundedness)
- ADDITIONAL INFO RULE: must 100% check Additional Personal Info before calling hallucination

### 4. Instruction Adherence & Contextual Fit `Followed and Fit|Partially Followed and Fit|Not Followed or Misfit`
- **Followed and Fit**: all instructions met; minor formatting quirks OK (esp. zh_HK)
- **Partially**: (a) wrong recipient name (but name exists in profile), (b) secondary social detail omitted from Previous Mail, (c) slight formality mismatch
- **Not Followed or Misfit**: severe topic deviation, core instruction violated, extreme formality mismatch

### 5. Tone & Empathy Alignment
Match expected emotional register: empathetic for grief/bad news, warm for personal, professional for business.

### 6. Naturalness
Reads like a human-written email, not robotic or template-generated. Natural flow and transitions.

### 7. Localization `Compliant|Localization Issue`
- zh_TW: full-width colons after greeting (e.g. `XX：`), consistent full-width punctuation
- zh_CN: CJK-English spacing consistency, mainland conventions
- zh_HK: minor styling leniency (missing space after greeting comma, sign-off+name on same line = OK)
- da_DK: NO comma after greeting or sign-off (absolute)
- nb_NO: comma BETWEEN greeting and name (`Hei, Thomas`), NOT after name (`Hei Thomas,` = WRONG)
- CRITICAL: spelling/grammar errors are NOT localization issues

### 8. Personalization `Personalized|Contextually Adapted|Generic|Mismatch`
- **Personalized**: perfectly matches sender profile (vocabulary, formatting, sign-off, signature)
- **Contextually Adapted**: intentionally shifts style for context (e.g. lacks_formatting profile but business email -> adds paragraphs). NOT a downgrade from Personalized
- **Generic**: no personality traits, reads like a boilerplate template
- **Mismatch**: style contradicts profile in ways that make no contextual sense
- Excessive Padding: unnecessary filler phrases inflating length beyond sender's typical brevity -> penalize

### 9. Pairwise Comparison
Priority cascade: Instruction adherence > Groundedness > Locale+Style > Equal Quality Rule
Two responses with identical dimension scores = A=B regardless of wording differences.
