# Correctness (Q3)

## Purpose
Evaluate whether the response's edits are necessary and correct. Correctness focuses ONLY on edits the model actually made, not on errors it missed (that is Completeness).

## Two Scoring Paths

### Path A: Input has NO errors (Q1=no_grammar_errors) + Response has edits (Q2=has_edits)
**alteredMeaning**: did the edits alter original meaning, tone, style, or register?
- `"no"`: edits are cosmetic and do not change meaning (e.g. removing trailing period, minor spacing)
- `"yes"`: edits changed the substance -- synonym substitution, sentence restructuring, formality shift, word choice alteration

Note: removing a final period or question mark alone usually does NOT count as altering meaning. But replacing specific vocabulary, reordering clauses, or shifting sentence fluidity = altered meaning = `"yes"`.

### Path B: Input HAS errors (Q1=has_grammar_errors) + Response has edits (Q2=has_edits)

#### correctness (edit necessity)
- **`all_necessary`**: every single edit addresses an objective error and nothing more. No subjective polishing, no unnecessary changes. Must pass Minimal Edit Principle in the input's formality context.
- **`some_unnecessary`**: at least ONE edit is unnecessary. Even a single unnecessary punctuation change in informal context triggers this. Always ask: "Was this edit required to fix an objective error?" If no -> some_unnecessary.
- **`all_unnecessary`**: every edit the model made was unnecessary. No actual error correction happened.

#### editsCorrect (technical correctness of edits)
- **`all_correct`**: all edits made are technically right (correct spelling, grammar, locale)
- **`some_incorrect`**: at least one edit introduced a new error or is factually wrong

#### correctnessErrors (only when editsCorrect = some_incorrect)
Array of error types. Values: `punctuation`, `spacing`, `new_errors`, `impede_comprehension`, `out_of_locale`, `wrong_article`, `voice_alteration`, `formality_alteration`, `word_choice_alteration`, `code_switch`, `register_alteration`, `other`

#### unnecessaryEdits (only when correctness = some_unnecessary or all_unnecessary)
Array of unnecessary edit types. Values: `punctuation`, `capitalization`, `spacing`, `mechanical`, `abbreviations`

## Non-Formal Tolerance Rule (CRITICAL)
In **Other** (informal) context:
- Missing punctuation, irregular capitalization, missing final periods, extra/missing spaces are ACCEPTABLE in the input
- If the model "fixes" these without changing meaning -> those fixes are **unnecessary edits**
- Correctness MUST be `some_unnecessary`, with corresponding `unnecessaryEdits` categories checked

## Examples
- Model adds missing comma in informal chat -> `some_unnecessary`, `unnecessaryEdits: ["punctuation"]`
- Model fixes typo `探套`->`探讨` and also replaces `问题`->`提问` -> `some_unnecessary`, `unnecessaryEdits: ["mechanical"]` (the synonym swap is unnecessary)
- Model fixes all errors perfectly with no extra changes -> `all_necessary`
- Model introduces new typo while fixing another -> `editsCorrect: "some_incorrect"`, `correctnessErrors: ["new_errors"]`
