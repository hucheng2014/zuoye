# Formality & Three-Level Error Framework

## Purpose
The formality of the input text determines which errors must be fixed, which are optional, and which must be preserved. This classification must be done BEFORE evaluating any response.

## Step 1: Classify Formality

### Formal
- Academic research papers, theses, dissertations
- Legal documents, contracts, official notices
- Government announcements, policy documents
- Business correspondence, corporate communications
- News reports, journalism
- Medical/scientific publications

### Other (Non-Formal)
- Casual conversation, daily chat
- SMS messages, instant messaging
- Social media posts, comments, forums
- Personal letters, informal emails
- Online literature, blog posts
- Any text with deliberate informal style markers (slang, emoji, abbreviations)

## Step 2: Apply Three-Level Error Framework

### Critical Errors -- Must fix in ALL contexts (Formal AND Other)
Errors that genuinely block comprehension, change intended meaning, create true ambiguity, or violate core grammar rules.

**Examples**:
- Typos/homophone errors that change meaning: `社会注意` -> `社会主义`, `探套` -> `探讨`
- Subject-verb agreement violations
- Severe word-order errors that make the sentence incomprehensible: `别用力过猛一上来就` -> `别一上来就用力过猛`
- Gender/pronoun agreement errors that create confusion
- Tense inconsistency that alters the narrative
- Comprehension-blocking misspellings
- Semantic contradictions: `我刚订好位子，但还没订到`
- Locale-specific character errors: simplified `几十` in zh-TW context (should be `幾十`)

### Minor Errors -- Must fix in Formal, optional in Other
Errors that are technically incorrect but do not block comprehension in informal settings.

**Examples**:
- Missing apostrophes in contractions
- Missing commas in direct address
- Comma splices
- Missing final periods or question marks
- Lowercase "i" (English)
- Sentence fragments (when deliberate in informal context)
- Minor capitalization irregularities
- Missing sentence-ending punctuation in casual chat

**Key Rule**: In **Other** context, if the model does NOT fix a Minor Error, this is acceptable and must NOT be penalized in Completeness. If the model DOES fix it, the fix is an unnecessary edit and Correctness must be `some_unnecessary`.

### Stylistic Choices -- PRESERVE in ALL contexts (Formal AND Other)
Intentional creative or expressive features that reflect the user's voice and style.

**Examples**:
- Elongated spelling for emphasis: `好啊！！！`, `真的嘛？？？`, `soooo`
- Emoji and emoticons
- Hashtags (#topic) and usernames (@user)
- Internet slang: `lol`, `btw`, `idk`
- SMS abbreviations in informal context: `u`, `r`
- Creative punctuation for emotional effect
- Deliberate ALL CAPS for emphasis
- Tone-specific fillers and particles

**Key Rule**: If the model standardizes, removes, or replaces any Stylistic Choice, this is an unnecessary edit and Correctness is penalized. For example, deleting trailing emoji or forcing a period after an emoji = unnecessary edit.
