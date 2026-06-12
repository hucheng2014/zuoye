# Localization

## Purpose
Evaluate whether the draft complies with the punctuation, formatting, and typographic conventions of its target locale. This dimension covers ONLY locale-specific format rules, NOT general spelling or grammar.

## CRITICAL RULE
**Spelling errors and grammar errors are NOT localization issues.** They belong to their own categories. Never check Localization Issue for a typo or grammatical mistake. Localization covers only punctuation format, symbol usage, and locale-specific typographic conventions.

## Per-Locale Rules

### zh_TW (Taiwan Traditional Chinese)

**Full-width colon rule:**
- Greeting must use full-width colon `：` (e.g. `奕安啊：`)
- All in-text punctuation must be full-width Chinese punctuation
- Mixed half-width/full-width punctuation = **Localization Issue**

**Format standards:**
- Consistent use of Taiwan-standard punctuation throughout
- No mainland-specific formatting conventions
- Proper paragraph structure per Taiwan email norms

**Example violation:**
- Draft uses half-width colon after greeting: `奕安啊:` -> Localization Issue
- Draft mixes full-width and half-width commas inconsistently -> Localization Issue

### zh_CN (Simplified Chinese)

**Consistency checks:**
- Simplified Chinese character consistency (no random Traditional characters)
- CJK-English mixed text: appropriate spacing conventions
- Greeting, colon, and line break format follows mainland Chinese email norms
- Colons and commas in proper simplified Chinese style

### zh_HK (Hong Kong Cantonese Traditional)

**Minor styling leniency (IMPORTANT):**
- If the draft uses natural Cantonese vocabulary, appropriate tone, and follows instructions, BUT has minor formatting issues, it is STILL compliant.
- Specifically tolerated:
  - Missing space after greeting comma: `你好嘉欣,` (no space before next sentence) -> OK
  - Sign-off and name on same line: `祝好, 宇瀚` (no line break) -> OK
  - Slightly informal paragraph structure -> OK
- These are classified as "minor stylistic issues" in Hong Kong business email context
- **Do NOT over-penalize zh_HK for formatting when content and tone are appropriate**

### da_DK (Danish)

**ABSOLUTE: No comma after greeting or sign-off.**
- Greeting: `Kære Lykke` (no comma) -> CORRECT
- Greeting: `Kære Lykke,` -> WRONG, **Localization Issue**
- Greeting: `Hej Maria` (no comma) -> CORRECT
- Greeting: `Hej Maria,` -> WRONG, **Localization Issue**
- Sign-off: `Med venlig hilsen` (no comma) -> CORRECT
- Sign-off: `Med venlig hilsen,` -> WRONG, **Localization Issue**
- Sign-off: `De bedste hilsner` (no comma) -> CORRECT
- Sign-off: `De bedste hilsner,` -> WRONG, **Localization Issue**

Separation between greeting/sign-off and body is achieved through line breaks only, NOT punctuation.

### nb_NO (Norwegian Bokmal)

**Comma rules for names:**
- Comma BETWEEN greeting word and name: `Hei, Thomas` -> CORRECT
- Comma AFTER name: `Hei Thomas,` -> WRONG, **Localization Issue**
- No comma after sign-off: same rule as Danish

Correct patterns:
- `Hei, Thomas` (comma separates greeting from name, no comma after name)
- `Med vennlig hilsen` (no comma after sign-off)

Wrong patterns:
- `Hei Thomas,` (comma after name instead of between greeting and name)
- `Med vennlig hilsen,` (comma after sign-off)

## Judgment Process
1. Identify the locale from the task
2. Check greeting punctuation against locale rules
3. Check sign-off punctuation against locale rules
4. Check body text punctuation consistency
5. Only flag issues that are locale-specific format violations, NOT spelling/grammar
