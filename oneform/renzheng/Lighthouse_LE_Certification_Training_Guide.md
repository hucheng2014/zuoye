# Lighthouse 3.0 — LE Certification Training Guide

## Complete Tutorial for Localization Evaluation (LE) Certification

**Based on**: [Lighthouse 3.0] LE Certification Training (Meeting Recording, Jan 16, 2026) + Localization Task Guidelines (February 2025, 41-page PDF)
**Trainer**: Tamara Bozic, Nanat, Ines
**Duration**: ~68 minutes
**Document Type**: Apple Confidential – Internal Use Only

---

## Table of Contents

1. [Overview & Objectives](#1-overview--objectives)
2. [The Evaluation Framework](#2-the-evaluation-framework)
3. [The 13 Localization Error Categories — Complete Definitions & Examples](#3-the-13-localization-error-categories--complete-definitions--examples)
4. [Tone Adjustment Examples (en_GB)](#4-tone-adjustment-examples-en_gb)
5. [Awkward/Unnatural Writing Examples by Locale](#5-awkwardunnatural-writing-examples-by-locale)
6. [Formatting & Punctuation Examples by Locale](#6-formatting--punctuation-examples-by-locale)
7. [Certification Exam Details — How It Works](#7-certification-exam-details--how-it-works)
8. [Common Mistakes & Warnings](#8-common-mistakes--warnings)
9. [FAQ from Q&A Session](#9-faq-from-qa-session)
10. [Quick Reference Checklist](#10-quick-reference-checklist)

---

## 1. Overview & Objectives

### What This Certification Is

The **Localization Evaluation (LE) Certification** is the first and most critical certification in the Lighthouse 3.0 project. It is a **qualifier** — if you fail both attempts, you cannot work on **any** Lighthouse task.

Unlike other Lighthouse certifications (summarization, proofreading, rewriting, device expert, etc.) which are mostly in English, the LE certification is **language-specific**. You will receive tasks in your assigned language/locale.

### What We Are Evaluating

You are asked to evaluate whether an AI model's response shows evidence of being tailored to a **specific locale/language variant**, or whether it contains **localization errors**.

**Critical distinction**: This is NOT about whether the answer is factually correct. The response can be completely wrong factually but still be perfectly localized. You are evaluating **language and cultural appropriateness**, not truthfulness, concision, or harmfulness (those are separate evaluation dimensions).

### The 13 Types of Localization Issues

| # | Error Type | Short Description |
|---|-----------|-------------------|
| 1 | Unlocalized Information | Information that belongs to a different locale |
| 2 | Overly-localized Content | Unnecessarily limiting content to target locale |
| 3 | Spelling | Locale-inappropriate spelling variant |
| 4 | Non-local Perspective | Not writing from the target locale's viewpoint |
| 5 | Vocabulary | Locale-inappropriate word choice |
| 6 | Phrase or Idiom | Phrase/idiom not understood in target locale |
| 7 | Wrong Language | Any element not in the task language |
| 8 | Grammar | Grammar that doesn't fit target locale |
| 9 | Tone | Overemphasis on stereotypical traits |
| 10 | Awkward or Unnatural Writing | Lacks native-speaker fluency; machine-translation feel |
| 11 | Formatting & Punctuation | Locale-inappropriate date/quote/punctuation usage |
| 12 | Units of Measurement (incl. Currency) | Wrong measurement/currency conventions |
| 13 | Other | Any other localization issue (e.g., culturally insensitive content) |

---

## 2. The Evaluation Framework

### How to Evaluate Each Task

For each task you will:

1. **Read the user's prompt** — pay attention to what locale the user is in and what language they are using
2. **Read the AI model's response** — the response should match the user's language (unless the prompt asks for a different language)
3. **Decide**: Does the response have any localization issues?

   - **No** — The response does not appear to be generated for a locale different from the user's. The language is appropriate for the target locale. Everything is fine.
   - **Yes** — At least one element in the response would make a user feel the model was not designed for their locale.

4. **If Yes**, select ALL applicable error categories from the 13 types
5. **Write the rationale in ENGLISH** — be specific and informative. Explain exactly what the issue is, where it appears, and why it's a problem for the target locale.

### The "Purple Text" Rule (MOST IMPORTANT)

For **Spelling (#3)**, **Grammar (#8)**, and **Formatting & Punctuation (#11)** categories:

> **Only report these if the usage is WRONG in your target locale, but WOULD BE CORRECT in another locale.**

If the error would be wrong in ALL locales (e.g., a typo that is universally wrong), do NOT label it as a localization issue. It belongs under **Composition** (a separate evaluation dimension that covers general spelling, grammar, typos, etc.), NOT under localization.

### What's NOT Being Evaluated Here

- Factual accuracy / truthfulness
- Conciseness / verbosity
- Harmfulness / safety
- Overall satisfaction

These are separate dimensions used in other tasks (e.g., Preference Ranking).

---

## 3. The 13 Localization Error Categories — Complete Definitions & Examples

### 3.1 Unlocalized Information (Category 1)

**Definition**: The response provides information relevant to another locale when it could have provided information more relevant to the target locale.

**Key Insight**: This is about information relevance and context. The model should understand where the user is and provide geographically/culturally appropriate information.

**Example 1** (en_GB):
- Prompt: "What's the easiest way to file my taxes?"
- Response mentions: "IRS Free File" (United States Internal Revenue Service)
- **Issue**: The user is in the UK. They would use HMRC, not the IRS. The response failed to recognize the en_GB locale and provided US-specific information.

**Example 2** (en_CA):
- Prompt: "What's the best time to visit Victoria?"
- Response talks about Victoria, Australia
- **Issue**: The user is Canadian (en_CA). They almost certainly meant Victoria, British Columbia, Canada. The model should default to the Canadian Victoria for a Canadian user.

---

### 3.2 Overly-localized Content (Category 2)

**Definition**: The response is unnecessarily fixated on the target locale. While relevant locale-based content should be provided, it should not unnecessarily restrict the scope of information.

**Key Insight**: Localization should add relevant context, not artificially limit the answer. Don't make everything about the locale when the user didn't ask for that.

**Example** (en_CA):
- Prompt: "What are the most influential books of all time?"
- Response lists only Canadian authors: *Anne of Green Gables*, *The Handmaid's Tale*, etc.
- **Issue**: The user did NOT ask for "most influential books by Canadian authors." They asked about "most influential books" globally. By restricting to Canadian authors only, the response is overly localized and misses globally influential works.

---

### 3.3 Spelling (Category 3)

**Definition**: A spelling variant is used that is inappropriate for the target locale.

**PURPLE TEXT RULE APPLIES**: Only report if the spelling is wrong for your target locale but MAY BE CORRECT in another locale. Universal spelling errors belong under Composition.

**Example** (en_GB):
- User prompt: "What is your favourite colour?"
- Response: "My favorite colors are blue and green."
- **Issue**: The user used British English spellings ("favourite", "colour"), but the response used US English spellings ("favorite", "colors"). This is wrong for en_GB but correct for en_US.

**Important**: For languages with only one standardized writing system (e.g., Hindi, Arabic), spelling may not be applicable as a localization issue. If the spelling is simply wrong (typo/misspelling that would be wrong everywhere), use Composition, not this category.

---

### 3.4 Non-local Perspective (Category 4)

**Definition**: The response does not adopt the perspective of the target locale. A common manifestation is when the response unnecessarily emphasizes the user's locale background.

**Key Insight**: The model should speak as if it naturally belongs to and understands the user's locale. It should NOT talk about the user's locale as if from an outsider's perspective.

**Example 1** (en_AU):
- Prompt: "Where is the most expensive property market in the country?"
- Response: "Sydney — median price AU$1.15 million..."
- **Issue**: For an Australian user asking about "the country," Australia is the default assumption. Explicitly marking the currency as "AU$" is unnecessary and makes it seem like the model doesn't assume the Australian context. This is overly localized.

**Example 2** (en_AU — acceptable):
- Prompt: "What's the exchange rate between AUD and USD?"
- Response clearly distinguishes AUD vs. USD
- **No issue**: When comparing currencies, it's necessary to distinguish them.

**Example 3** (en_CA):
- Prompt: "What activities are there for Victoria Day?"
- Response starts by defining what Victoria Day is
- **Issue**: For a Canadian user, Victoria Day is common knowledge. A Canadian doesn't need an explanation of their own national holiday. The response should assume shared cultural knowledge.

---

### 3.5 Vocabulary (Category 5)

**Definition**: A word is used that is not appropriate for the specific geographic/cultural context of the target locale.

**Example** (en_GB):
- Prompt: "What are the most popular sports?"
- Response mentions: "Soccer"
- **Issue**: In the UK, the sport is called "football", not "soccer." Using "soccer" marks the response as US English.

**This is one of the more common error types in Lighthouse tasks, especially for English locale variants.**

---

### 3.6 Phrase or Idiom (Category 6)

**Definition**: The response contains phrases and idioms that are not commonly used or understood in the target locale.

**Example** (en_CA):
- User requests C++ code
- Response says: "I'd be chuffed to bits to help you with that code!"
- **Issue**: "Chuffed to bits" is a distinctly British colloquialism. A Canadian user may not understand it or may find it out of place.

---

### 3.7 Wrong Language (Category 7)

**Definition**: Any part of the response uses a language or locale variant that is not the task language.

**Key Insight**: This does NOT require the entire response to be in the wrong language. A single word in the wrong language counts.

**Acceptable Exceptions** (Do NOT report):

1. **Translation requests** — If the user asked for a translation, the foreign language in the output is expected
2. **Language teaching requests** — If the user asked to learn a foreign expression
3. **Loanwords** — Words borrowed from other languages that are commonly accepted and used in the target language
4. **Coding languages** — Code snippets in programming languages (e.g., `print("hello world")`)

**Loanword Examples** (NOT errors):
- *cul-de-sac* (French → English)
- *fiancé(e)* (French → English)
- *rendezvous* (French → English)
- *entrepreneur* (French → English)
- *angst* (German → English)
- *kindergarten* (German → English)
- *schnitzel* (German → English)
- *online* (English → Italian — commonly accepted)

**Example 1** (Error):
- User writes in Chinese
- Response: "I'm sorry, your message is in a language that I cannot understand."
- **Issue**: The user wrote in Chinese, but the model responded in English. The response is in the wrong language.

**Example 2** (Error):
- User writes in Arabic, task is "rewrite this sentence"
- Response contains an English word that doesn't belong and wasn't requested
- **Issue**: A single English word appears in an otherwise Arabic response with no justification.

**Example 3** (Error — Certification trap):
- In a long text, one single word is in the wrong language (e.g., an English word "common" inserted into an Arabic response for no reason)
- **Issue**: These are intentionally planted to test attention to detail. Many graders miss these because they get caught up in the overall content.

**Coding Languages** (NOT an error):
- If the response contains `print("hello world")` or similar code expressions, this is acceptable
- Coding requests are extremely rare and mostly relate to Preference Ranking tasks, not Lighthouse tasks

---

### 3.8 Grammar (Category 8)

**Definition**: Grammar that doesn't fit the target locale.

**PURPLE TEXT RULE APPLIES**: Only report if the grammar is wrong for your target locale but MAY BE CORRECT in another locale variant.

**Example** (en_GB):
- Response uses past tense "learned"
- **Issue**: In British English, the standard past tense is "learnt." "Learned" is US English. This is wrong for en_GB but correct for en_US.

**Important**: If a grammar error applies to ALL English variants or ALL variants of your language, it's NOT a localization grammar issue — it belongs under Composition.

**Multi-locale languages** (English, Portuguese, French, Spanish, Arabic, Chinese, German, etc.) will have more grammar-related localization issues.

---

### 3.9 Tone (Category 9)

**Definition**: Overemphasis on traits that may be associated with certain groups in the target locale. It borders on stereotyping.

**CRITICAL**: This is NOT about:
- Formal vs. informal tone
- Friendly vs. professional tone
- Serious vs. humorous tone
- Polite vs. casual tone

Those are style choices, not localization tone issues.

**What It IS About**: The model adopts an exaggerated, stereotypical way of speaking associated with a particular group, which might be offensive or inauthentic. It could involve:

- Overusing slang or expressions stereotypically associated with minorities
- Mimicking immigrant speech patterns
- Exaggerating regional dialects

**Example** (en_GB — from tone adjustment examples, Section 4):
- Response about Jared Leto wearing a cat costume uses: "blimey," "pulling our leg," "popped off his rocker," "chap," "nutter," "spot of tomfoolery," "cuppa," "palaver," "gargle down the local," "spotted dick"
- **Issue**: This is an exaggerated caricature of British speech. A real British person would not speak like this in a normal response.

**Frequency**: This is relatively rare in Lighthouse tasks (summarization, rewriting, proofreading) but may appear in the certification to test your knowledge.

---

### 3.10 Awkward or Unnatural Writing (Category 10)

**Definition**: Wording that lacks native-speaker fluency. May sound like it was literally translated from another language (e.g., machine translation from Google Translate) or simply not written by a native speaker.

**Key Insight**: This is one of the **MOST COMMON** error categories in the certification and in production tasks, especially for non-English locales.

**What to Look For**:
- Word-for-word literal translations that don't flow naturally
- Sentence structures that mimic English patterns but sound wrong in the target language
- Expression translated literally that makes no sense in the target language
- Machine-translation artifacts

**Subcategory Examples by Language** (detailed in Section 5):

**Korean (ko_KR)**:
- "여정을 하고있었습니다" → Should be "여정 중이었습니다" or "항해 중이었습니다"
- Sentence component order not following Korean grammar patterns (reads like English translated)
- Medical terminology: "압력골절" → Should be "압박골절" (compression fracture)
- "녹색의 골절" → Should be "若木骨折" (literal translation of "greenstick fracture" is wrong)
- "생활습관" → Should be "생활 습관" (missing space)
- Using colons instead of periods (formatting issue for Korean)

**Spanish (es_ES)**:
- "Aquí está una explicación" → Should use "tener": "aquí tienes una explicación"
- "causarte sentir mal" → Should be "causar malestar"
- "después de una semana o así" → Should be "al cabo de una semana más o menos"
- Overuse of passive voice (common in English but unnatural in Spanish)
- Closing "Con amor" → Should be "Con cariño" or "Un abrazo"

**French (fr_FR)**:
- "de nouveaux matériaux" (literal "new materials") — not applicable in the French context
- French is sensitive to word repetition: same sentence containing "album" twice is awkward
- "Oui, j'ai fait" → "faire" is a transitive verb in French and needs an object
- Mixing "tu" (informal) and "vous" (formal) in the same conversation
- English-style quotation marks (" ") → French traditionally uses guillemets (« »)

**Portuguese (pt_BR)**:
- "fundo de poupar" → Should be "poupança" (savings fund)
- "o osso mais grande" → Should be "o maior osso" (the biggest bone)
- "diplomação na mão" → Should use "graduação" (graduation diploma)

**Japanese (ja_JP)**:
- "室内植物" → Should be "観葉植物" (ornamental plants / houseplants — the standard Japanese term)
- Medical terms: "圧力骨折"→"圧迫骨折", "ねじれ骨折"→"捻転骨折", "緑色の骨折"→"若木骨折"
- "SSRIの間で薬を選択する場合" → "間で" (among) is unnatural; should use "の中から"
- "確かに" used as literal translation of "sure" — "確かに、ここに記事の要約があります" is unnatural sentence-opening

**Chinese (zh_CN)**:
- "如果您发现有⼈停放在您的街区的⻋辆" → "有人" is redundant and confusing
- "在去世后⼏天内离开了我们" → Logical contradiction; "去世" (passed away) followed by "离开" (left us) is redundant
- "除了她在银幕上的成就外，珍还是一个亲切、善良的灵魂" → Chinese does not describe people using "是...的灵魂" (is a soul) the way English does

**German (de_DE)**:
- "Er machte sich Zeit für uns" → Should be "Er nahm sich Zeit für uns"
- Mixing "Sie" (formal you) and "du" (informal you) inconsistently

**Italian (it_IT)**:
- "che stanno fuori" → Overly literal, unnatural phrasing
- "La durata più lunga" → Inappropriate in this context, may cause ambiguity

---

### 3.11 Formatting & Punctuation (Category 11)

**Definition**: Locale-inappropriate use of formatting and punctuation.

**PURPLE TEXT RULE APPLIES**: Only report if it's wrong in your target locale but correct in another locale.

**Subcategories**:

| Type | Examples |
|------|----------|
| Date formats | US: month/day/year; Europe: day/month/year; Asia: year/month/day |
| Quotation marks | English: " " — French: « » — Some locales: „ " or bottom-left to top-right |
| Spaces before punctuation | French: space before colon (:), semicolon (;), question mark (?), exclamation mark (!) — NOT used in English/German |
| Time formats | 12-hour vs. 24-hour |
| Number formatting | Comma vs. dot for decimals; thousands separator (comma, dot, or space) |
| Writing direction | LTR vs. RTL |

**Date Format Example**:
- European locale (e.g., fr_FR, de_DE, es_ES), the model uses month/day/year
- **Issue**: This is wrong for European locales but correct for en_US → report under Formatting & Punctuation

**Quotation Mark Example** (French):
- French text uses English quotation marks " " instead of guillemets « »
- **Issue**: Correct quotation marks for French are « », not " "

**Spacing Example** (French):
- French text missing space before colon: "Slide 3: Amélioration"
- **Issue**: French requires a space before colon: "Slide 3 : Amélioration"

**Common Pitfall**: Formatting and punctuation issues are some of the most **frequently missed errors** in certification because most graders are accustomed to their keyboard's default (usually English-style) punctuation and don't think to check locale-specific rules.

**Mental trigger**: Whenever you see quotation marks, dates, numbers, or colons in a response, immediately think: "Is this correct for MY locale?"

---

### 3.12 Units of Measurement & Currency (Category 12)

**Definition**: Use of incorrect measurement units, currency, or related conventions.

**Subcategories**:

| Category | Examples |
|----------|----------|
| Temperature | Celsius (°C) vs. Fahrenheit (°F) |
| Distance | Kilometers vs. miles |
| Weight | Kilograms vs. pounds vs. stones |
| Currency | Currency code/symbol appropriate to locale |
| Number formatting | Comma vs. dot for decimals; thousands separator conventions |

**Important**: If the user explicitly requested a specific unit/currency, do NOT report it as an error. For example, if the user asked about "US dollars" while doing an Arabic task, US dollars is correct.

**This error category is relatively rare in localization tasks but may appear.**

---

### 3.13 Other (Category 13)

**Definition**: Any other localization issue not covered by the previous 12 categories.

**Most common application**: Culturally insensitive content.

**Example**: Content that would be offensive or inappropriate specifically within the target culture but might not be obvious to an outsider.

**Caution**: Be careful how you use this category. A response might be offensive to you personally but not generally considered culturally insensitive. Use objective standards, not personal feelings.

**No specific examples are provided in the guidelines because these would be highly locale-specific and only recognizable by a native speaker.**

---

## 4. Tone Adjustment Examples (en_GB)

These examples illustrate Category 9 (Tone) — overemphasis on stereotypical British traits.

### Case 1: Jared Leto Wearing Cat Costume

| Aspect | WRONG (Stereotypical British) | BETTER (Natural) |
|--------|------------------------------|-------------------|
| Style | Overloaded with British slang: "blimey," "pulling our leg," "popped off his rocker," "chap," "nutter," "spot of tomfoolery," "cuppa," "palaver," "gargle down the local," "spotted dick" | Formal, natural expression appropriate for news/entertainment context |

### Case 2: Taylor Swift Re-recording Albums

| Aspect | WRONG (Stereotypical British) | BETTER (Natural) |
|--------|------------------------------|-------------------|
| Style | "right bobbish," "flogged," "didn't go down well," "our T-Swizzle," "right miffed," "reckons," "palaver" | Standard journalistic description |

### Case 3: TV Show Recommendations (similar to Breaking Bad)

| Aspect | WRONG (Stereotypical British) | BETTER (Natural) |
|--------|------------------------------|-------------------|
| Style | "innit," "telly," "tickle your fancy," "mate," "smashing," "gobsmacked" | Concise, professional recommendation list |

**Core Issue in All Cases**: Excessive use of stereotypically British slang makes the response feel like it's caricaturing British speech rather than providing a natural, fluent response. A real British person would write more naturally and not cram every British slang term into a single paragraph.

---

## 5. Awkward/Unnatural Writing Examples by Locale

See Section 3.10 for the complete list. This section provides additional examples from the guidelines that were walked through during the training.

### Korean (ko_KR) — Additional Examples
- Overall sentence structure frequently mirrors English word order rather than natural Korean
- Translation of English medical terminology done literally rather than using accepted Korean medical terms
- Missing spaces in compound words

### Spanish (es_ES) — Additional Examples
- "Aquí está una explicación" → Literal translation of "Here is an explanation." Natural Spanish would use "tener" (to have): "Aquí tienes una explicación."
- Passive voice overuse from English translation patterns
- Formal closing phrases mistranslated

### French (fr_FR) — Additional Examples
- Repeated words (French is much more sensitive to repetition than English)
- "Tu"/"Vous" inconsistency — switching between informal and formal address
- Missing spaces before punctuation marks (colon, semicolon, question mark, exclamation mark)

---

## 6. Formatting & Punctuation Examples by Locale

These are issues commonly missed because graders are used to English keyboard conventions.

### Quotation Marks by Locale

| Locale | Correct Quotation Marks | WRONG (English-style) |
|--------|------------------------|----------------------|
| English (US/UK) | " " (straight or curly) | — |
| French (fr_FR) | « » (guillemets) | " " |
| Spanish (es_ES) | « » or " " (varies) | — |
| German (de_DE) | „ " or » « | " " |
| Some locales | Start bottom-left „ end top-right " | " " |

### Spacing Rules for French

| Punctuation | French Rule | English Rule |
|-------------|-------------|--------------|
| Colon (:) | space before AND after | No space before |
| Semicolon (;) | Space before AND after | No space before |
| Question mark (?) | Space before AND after | No space before |
| Exclamation mark (!) | Space before AND after | No space before |

**French example**: "Slide 3 : Amélioration" (correct) vs. "Slide 3: Amélioration" (incorrect — missing space before colon)

### Date Formats

| Region | Format | Example |
|--------|--------|---------|
| US | Month/Day/Year | 02/15/2025 |
| Europe | Day/Month/Year | 15/02/2025 |
| East Asia | Year/Month/Day | 2025/02/15 |

### Currency & Number Formatting

| Locale Example | Decimal | Thousands | Example |
|---------------|---------|-----------|---------|
| US/UK | . (dot) | , (comma) | 1,234.56 |
| Many European | , (comma) | . (dot) or space | 1.234,56 or 1 234,56 |
| Some locales | . (dot) | space | 1 234.56 |

---

## 7. Certification Exam Details — How It Works

### The Certification Hierarchy

The LE (Localization Evaluation) certification is the **first and most critical** certification:

```
LE Certification (Localization) ← YOU ARE HERE
    ↓ (Must pass to proceed)
    ├── Summarization Certification
    ├── Proofreading Certification
    ├── Rewriting Certification
    ├── Device Expert Certification
    ├── Tone Adjustment Certification
    └── ... (other task-specific certifications)
```

- **If you fail both attempts of the LE certification**: You cannot work on ANY Lighthouse task.
- **If you pass LE but fail a specific task certification**: You can still work on tasks you DID pass. For example, failing Device Expert but passing Summarization and Rewriting means you can still do Summarization and Rewriting.

### Attempts

- **2 attempts per certification**
- If you fail the first attempt, you get a second chance
- If you fail both, you don't qualify for that certification

### Number of Tasks

- Certifications have varying numbers of tasks (approximately **15–20 tasks**)
- The number varies by language and by certification type

### Time

- **No countdown timer** — the timer counts UP (tracks how long you spend)
- **No time limit** — you can work at your own pace
- You do NOT have to finish in one sitting. You can do 5 tasks, close the browser, come back later and do more.
- **Ideally**, finish within 24 hours after receiving the link (to keep the project moving fast), but there is no hard deadline during certification

### Passing Score (Pass Rate)

- **Varies by certification**: Some require 70%, some 80%, and some tasks require **90%**
- The team will check your scores after you submit and notify you

### Distribution of Issues in Tasks

- **NOT every task has a localization error**
- Tasks are designed with a balanced approach: roughly 9:11 or 10:10 or 11:9 ratio of tasks with issues to tasks without
- Some languages may have 13-14 tasks with issues, with 6 having none (varies by language)
- **Do NOT assume every task has an issue** — many graders failed in the past because they made this assumption

### What Happens After You Pass

- You move to the next certifications (task-specific ones like summarization, proofreading, etc.)
- Once all required certifications are passed, you get access to the **production environment**
- **In production**:
  - There IS a time-per-task (TPT) expectation (e.g., ~5 minutes average for rewrite, ~10 minutes for device expert)
  - The timer (counting up) becomes important — spending 30 minutes on a single task will result in a bad TPT
  - The certification timer is just for reference; it doesn't matter during certification

---

## 8. Common Mistakes & Warnings

### 1. Assuming Every Task Has a Localization Error
> **This is the #1 reason people fail.** The certification tests whether you can correctly identify BOTH the presence AND absence of localization issues. Don't go hunting for errors that aren't there. Don't nitpick. Read the response naturally and evaluate based on the error categories and descriptions.

### 2. Reporting Universal Errors as Localization Issues
> A spelling/grammar/formatting error that is wrong in ALL language variants is NOT a localization issue. It belongs under **Composition**. Only report it under localization if it would be correct in ANOTHER locale variant.

### 3. Missing Formatting & Punctuation Errors
> These are frequently overlooked because we're used to our keyboard defaults. Any time you see quotation marks, dates, colons, numbers, or currency in a response — pause and verify against your locale's rules.

### 4. Missing Single-Word Wrong-Language Errors
> The certification may intentionally insert a single foreign word in an otherwise correct text. These are easy to miss when you're focused on overall content.

### 5. Not Accounting for Loanwords
> If a word from another language is commonly used and accepted in your language (e.g., "kindergarten" in English, "online" in Italian), do NOT report it as wrong language.

### 6. Reporting Loanwords as Wrong Language
> Opposite of #5. Familiarize yourself with commonly accepted loanwords in your language.

### 7. Confusing Tone with Style
> Tone (Category 9) is ONLY about stereotyping/overemphasizing group traits. Formal vs. informal, friendly vs. serious — these are style choices, not localization tone issues.

### 8. Overthinking the "Other" Category
> Be objective. "I personally find this offensive" is not the same as "this is culturally insensitive." Use Category 13 sparingly and with justification.

### 9. Forgetting to Write Rationale in English
> Regardless of what language your task is in, the rationale MUST be written in English. Be specific — say what the issue is, where it appears, and why it's a problem.

### 10. Not Using Online Sources for Verification
> If you're not 100% sure about a spelling, grammar rule, quotation mark convention, or formatting rule for your locale, you CAN and SHOULD use official online linguistic resources to verify.

---

## 9. FAQ from Q&A Session

### Q: Will the tasks always be available, or only on specific days?
**A**: The certification links will be sent via email by the delivery team/PMs. Once you receive the link, the tasks are always available. You don't have to finish in one sitting. You can do a few, close the browser, and come back later.

### Q: What if I fail? Do I get another chance?
**A**: Yes, each certification has **2 attempts**. If you fail the first, you can take the second. If you fail both, you won't qualify for that task.

### Q: For languages like Hindi (India) that don't have multiple spelling variants, do we still mark spelling issues?
**A**: If your language has only one standardized writing system and the word simply has a typo/misspelling, that belongs under Composition, not localization spelling. However, there may be other types of issues even for languages without multiple variants — like awkward/unnatural writing and format/punctuation errors.

### Q: Will there be PDFs/guidelines we can review?
**A**: Yes. ALL guidelines, links, and instructions will be shared with you via email. You'll have all the reference materials you need before taking the certification.

### Q: Is there a time limit on each task during certification?
**A**: No countdown timer during certification. The timer counts UP and is just for tracking. You can take as long as you need.

### Q: What if I can't complete the account creation within 2 hours?
**A**: Account creation is handled by a separate team. Contact them directly if you have issues. The training team does not manage account creation.

### Q: Will the certification happen over the weekend?
**A**: The delivery team typically doesn't work on weekends. If links aren't sent on Friday, expect them on Monday or as soon as possible.

### Q: What's the overall certification process flow?
**A**:
1. LE Certification (localization, language-specific) — **qualifier**, MUST pass
2. Task-specific certifications (summarization, proofreading, rewrite, etc.)
3. Each has 2 attempts with varying pass rates (70%–90%)
4. Once all required certs are passed → production access

---

## 10. Quick Reference Checklist

Before submitting each task, ask yourself:

- [ ] Did I read the user's prompt carefully? Do I know what locale and language they are in?
- [ ] Is the response in the correct language? (not Wrong Language #7 — check for single-word intrusions)
- [ ] Is the information relevant to the target locale? (not Unlocalized Information #1)
- [ ] Is the response OVERLY focused on the locale? (not Overly-localized #2)
- [ ] Are spellings correct for my locale specifically? (remember the Purple Text Rule for #3)
- [ ] Is the response from the target locale's perspective? (not Non-local Perspective #4)
- [ ] Is the vocabulary appropriate for my locale? (not Vocabulary #5 — e.g., football vs. soccer)
- [ ] Are there any idioms or phrases that don't fit my locale? (not Phrase/Idiom #6)
- [ ] If an unfamiliar word appears, is it a loanword (acceptable) or wrong language (error)?
- [ ] Is the grammar appropriate for my specific locale variant? (not Grammar #8 — Purple Text Rule)
- [ ] Is the tone neutral and not stereotypical? (not Tone #9)
- [ ] Does the writing sound natural and fluent (not literally translated)? (not Awkward/Unnatural #10)
- [ ] Are quotation marks, dates, and punctuation correct for my locale? (not Formatting & Punctuation #11)
- [ ] Are units of measurement and currency appropriate? (not Units #12)
- [ ] Is there any culturally insensitive content? (not Other #13 — use sparingly and objectively)
- [ ] If I marked "Yes" — did I select ALL applicable error categories?
- [ ] Is my rationale written in ENGLISH, specific, and informative?

---

*End of Training Guide. For questions, refer to the guidelines shared via email or contact the delivery team.*
