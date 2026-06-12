# Writing Tools - Proofread V2 v.2026 Feb.24 English Tutorial Summary

> Source: controlled SharePoint PDF, `Writing Tools - Proofread V2 v.2026 Feb.24.pdf`  
> Document updated: March 9, 2026  
> Topic: evaluating the quality of Proofread outputs.

## 1. Purpose of the Guideline
The Proofread feature is designed to **correct all grammatical errors in the user’s input text while preserving the original tone, style, register, formality, expressivity, and formatting as much as possible**.

Evaluation focuses on two dimensions:

- **Correctness**: whether each edit in the response is necessary, correct, and aligned with the Minimal Edit Principle.
- **Completeness**: whether all errors in the input that require correction are detected and corrected.

Proofread is not a rewriting or style-improvement feature. If the input is already acceptable for its intended context, the model should leave it unchanged.

## 2. Major V2 Updates
This version was updated to reduce ambiguity in Proofread grading and to distinguish error types by severity and context.

Key updates:

- A new **Step 2: Classify the formality level of the Input Text** was added.
- Graders must understand three error types: **critical errors, minor errors, and stylistic choices**.
- The formality of the input determines whether a given error must be fixed, may optionally be fixed, or should be preserved.
- Step 3 now asks whether the input contains errors that hinder comprehension or readability and whether the assistant changed the input.
- Step 4 Correctness and Step 5 Completeness have updated follow-up questions and derived scoring flows.
- The Jan. 29 update added explicit handling for ambiguity and incomprehensible input.
- The Dec. 10 callout explains that if text appears truncated in the grading UI, graders should assume the omitted part was left unchanged. If the Proofread Copy made no actual change, grade it as identical to the input.

## 3. Overall Workflow
The evaluation workflow has six steps:

1. **Review the Original Input Text**: check for grammatical errors, ambiguity, and incomprehensibility.
2. **Classify Formality**: decide whether the input is formal or other.
3. **Make an Initial Assessment**: determine whether the input has errors requiring correction and whether the response changed the input.
4. **Evaluate Correctness**: judge whether the response’s edits are necessary and correct.
5. **Evaluate Completeness**: judge whether all required errors were found and corrected.
6. **Compare Responses in Pair**: compare outputs using the derived scores for each dimension and provide feedback.

## 4. Minimal Edit Principle
The central rule is the **Minimal Edit Principle**: proofreading edits must be strictly minimal and should address only grammar, punctuation, capitalization, spelling, or formatting errors as lightly as possible.

The response must preserve:

- **Semantic content**: no new content, removed nuance, shifted emphasis, or unnecessary synonym substitutions.
- **Tone, register, style, and formality**: do not formalize informal writing or casualize formal writing unless needed to correct a real error.
- **Pronoun referentiality**: preserve person, number, and gender features, except for necessary grammatical case corrections.
- **Proper noun referentiality**: do not replace or alter names, places, organizations, or brands, except for grammatical inflection such as possessives.
- **Expressivity, colloquialisms, and slang**: keep emojis, emoticons, repeated punctuation, elongated spelling, fillers, acronyms, internet slang, usernames, and hashtags.
- **Formatting**: preserve line breaks, indentation, bullet styles, paragraph structure, special symbols, numeric forms, and ALL CAPS.
- **Local punctuation and formatting**: respect locale-specific quotation, punctuation, date, number, and formatting conventions.

Any violation should be penalized under Correctness.

## 5. Handling Ambiguous or Informal Contexts
The guideline gives three principles:

1. **Add punctuation when contextually appropriate**: in formal or neutral writing, correct punctuation is expected. If formality is unclear, prioritize grammatical correctness and readability.
2. **Preserve colloquial or informal style**: for clearly informal text, do not normalize expressions such as “gonna,” do not add deliberately omitted subjects, and do not force hard stops after expressive endings such as emoji.
3. **Accept reasonable interpretations of unclear text**: when meaning is genuinely unclear, a plausible clarification is acceptable, but leaving the text unchanged is also acceptable. Do not require the model to invent an unlikely meaning.

## 6. Step 1: Review the Original Input
Before scoring the response, inspect the input:

- Does it contain an objective grammatical error?
- Is any part ambiguous because of missing or incorrect punctuation?
- Is the text too vague or incomprehensible to assess?

A grammatical error is an objective violation of foundational language rules, such as spelling, punctuation, subject-verb agreement, or sentence structure. Subjective style, tone, or naturalness concerns are not grammatical errors.

## 7. Step 2: Formality and Error Types
Classify the input as:

- **Formal**: government, legal, academic, or research contexts.
- **Other**: semi-formal, informal, colloquial, chat, SMS, or similar contexts.

Then apply the error-type framework:

- **Critical Errors**: must be fixed in both formal and informal contexts. These genuinely block comprehension, change intended meaning, create true ambiguity, or violate core grammar. Examples include subject-verb agreement errors, wrong word usage, severe homophone errors, gender/pronoun agreement errors, tense inconsistency, comprehension-blocking misspellings, and true pronoun ambiguity.
- **Minor Errors**: must be fixed in formal contexts, but are optional in informal or “other” contexts. Examples include missing apostrophes in contractions, missing commas in direct address, comma splices, missing final periods or question marks, lowercase “i,” sentence fragments, and some capitalization issues.
- **Stylistic Choices**: should be preserved. These include intentional misspellings or elongations, creative punctuation, slang, expressive fragments, and tone-driven choices.

For ambiguous cases, graders should look at the full text to decide whether a pattern is an anomaly or a consistent informal style.

## 8. Step 3: Initial Assessment
Step 3 asks two main questions:

- **Q1: Does the input text contain errors that hinder comprehension or readability, considering its intended formality level?**
  - No errors: the input is clear and readable for its formality level.
  - Yes: the input contains errors requiring correction.
  - Cannot assess: the text is so unclear, vague, incomplete, or contextless that its meaning cannot be determined.
- **Q2: Did the assistant make changes to the input?**
  - Yes: the response differs from the input.
  - No: the response is identical to the input.

If the response is identical to the input, the grader does not continue to the Correctness and Completeness steps; the system computes the relevant scores.

## 9. Step 4: Correctness
Correctness checks whether the response’s edits are **necessary and correct**.

The follow-up question depends on the initial assessment:

- If the input has no errors but the response makes edits, answer whether any edit altered the original meaning, tone, style, or register.
- If the input has errors and the response makes edits, answer whether all edits are necessary:
  - Yes, all edits are necessary.
  - Mixed, only some edits are necessary.
  - No, all edits are unnecessary.

Derived Correctness scores are shown as Excellent, Good, Fair, or Poor. Graders do not manually assign these scores, but they answer the follow-ups that determine them.

Incorrect-edit categories include punctuation, spacing, new meaning-altering errors, comprehension impairment, out-of-locale content, wrong article or preposition use, voice alteration, formality alteration, word choice alteration, changed code-switching level, register alteration, and other.

Unnecessary-edit categories include punctuation changes that do not improve syntax, expressivity, or meaning; optional capitalization; unnecessary spacing changes; subjective mechanical or phrasing changes; and incorrect handling of abbreviations.

## 10. Step 5: Completeness
Completeness is evaluated only when the input contains errors and the response made changes. The question is:

**How completely does the response catch all errors that require correction?**

The four ratings are:

- **Complete**: identifies all errors.
- **Nearly Complete**: misses only a small portion, fewer than 20%.
- **Partial**: misses a significant portion, 20% or more.
- **Incomplete**: misses most or all errors.

If the response is Nearly Complete, Partial, or Incomplete, categorize the missed or improperly corrected errors: incorrect abbreviation handling, awkward or unnatural edits, punctuation/formatting issues that do or do not impede comprehension, common grammatical mix-ups, spelling errors, incorrect word usage that changes meaning or causes grammar errors, or other.

Correctness and Completeness are separate: Correctness evaluates the edits the model made; Completeness evaluates whether the input’s required errors were found and fixed. New errors introduced by the response are penalized under Correctness.

## 11. Abbreviations, Slang, and Expressivity
The guideline strongly warns: **do not expand common abbreviations of longer words** unless the shorthand is clearly only a speed-writing shortcut and the context unambiguously requires expansion.

Generally preserve:

- internet slang such as `lol`;
- abbreviations such as `btw` and `idk`;
- expressive punctuation such as `?!`, `!!!`, and `???`;
- elongated spellings such as `soooo` and `yessss`;
- emojis, emoticons, hashtags, usernames, technical acronyms, and units.

If the response expands abbreviations, changes casing, removes expressive punctuation, or normalizes slang without necessity, penalize it under Correctness.

## 12. Pairwise Comparison
After evaluating each response, compare response pairs using the derived scores displayed for Correctness and Completeness. Add feedback for the engineering team when useful, then submit the task.

## 13. Informal Word List Appendix
The appendix provides lists of informal words, abbreviations, acronyms, slang, technical units, and expressions that should not be expanded or normalized. Use these lists as reference when deciding whether an abbreviation is intentional.

## 14. Japanese Guidelines
Japanese has special complexity in script, tone, and conjugation:

- **Script**: Hiragana, Katakana, and Kanji can each be acceptable. Correct a script only when the chosen script is clearly not the usual or grammatically appropriate form.
- **Tone**: politeness and honorific level are built into grammar. Do not change casual, polite, or honorific tone unless the input has a clear mismatch.
- **Conjugation**: correct obvious tense, politeness, or grammatical conjugation errors, but do not change a grammatically correct form merely because another form sounds more fluent.

Unnecessary script conversion, tone refinement, or conjugation refinement should be penalized under Correctness.

## 15. Arabic Guidelines
For Modern Standard Arabic and Arabic dialects, the Minimal Edit Principle applies:

- Preserve tone, style, register, and dialectal authenticity.
- If input is dialectal or mixes MSA and dialect, the output should preserve that register rather than converting it to MSA or another dialect.
- A register or formality shift is a Correctness violation.
- Dialectal text should follow common standardized native-speaker practices for that dialect.
- The response should match the input’s numeral system, whether Western Arabic numerals or Eastern Arabic numerals.
- Tanween and other diacritic practices should match the input; changing them unnecessarily should be penalized.

## 16. Hinglish Guidelines
Hinglish combines Romanized Hindi and English. The response should correct clear errors while preserving the input’s tone and level of code-switching.

Rules include:

- English words and sentences follow Indian English conventions.
- Hindi Latin words follow Hindi grammar, transliterated into Latin script.
- Multiple phonetic spellings can be valid; do not enforce one acceptable spelling over another.
- Do not introduce Devanagari unless the input contains it.
- Skip the task if the input is largely Devanagari Hindi and therefore not typical for the `hi_LATN` locale.
- Preserve social-formality markers such as `tu`, `tum`, and `aap`.
- Do not translate English phrases into Hindi or change the code-switching ratio.
- Do not assume or change gender. If the input is ambiguous and a neutral form is available, use the neutral form. Clear gender-agreement errors should be corrected.

## 17. Practical Grading Checklist
Use this order when evaluating:

1. Identify the input’s context and formality level.
2. Decide which input issues are critical, minor, or stylistic.
3. Check whether the response changed the input.
4. For every change, decide whether it was necessary.
5. For necessary changes, decide whether they were correct.
6. Check for unintended changes to meaning, tone, style, register, formatting, proper nouns, pronouns, abbreviations, punctuation, locale, or code-switching.
7. Check whether all required errors in the input were corrected.
8. Use the derived scores to compare response pairs.

The core rule of Proofread V2 is: **fix only what must be fixed, fix it correctly, do not miss required errors, and do not erase the user’s original voice.**
