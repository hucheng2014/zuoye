# Common Errors (May 22 Feedback RCA)

## Purpose
Root cause analysis of the most frequent rating deviations identified in the official WT Proofread V2 Feedback & Calibration report (May 22, 2026). Use as a checklist to avoid the same mistakes.

## Error Category 1: Completeness Misses (Blindly Trusting Model)

### Root Cause
Raters assume the model has caught most errors and do not independently verify by reading the input text thoroughly.

### Specific Errors
- Marking `complete` when the model missed 1-2 errors that the rater did not notice
- Not detecting semantic contradictions in input (e.g. `订好位子，但还没订到`)
- Not recognizing hidden preposition misuse in Cantonese (e.g. `喺` vs `係`)
- Overlooking locale-specific errors (e.g. `。。。` not corrected to `……`)

### Prevention
**ALWAYS read the input text word-by-word BEFORE evaluating any response.** Build your own error list independently. Count total errors. Then check each response against your list. Never trust the model's output as ground truth.

## Error Category 2: Correctness Misconceptions (Formality Confusion)

### Root Cause
Raters do not properly apply the Minimal Edit Principle within the correct formality context. Two failure modes:

### Failure Mode A: Over-Penalizing (flagging valid fixes as unnecessary)
- In **Formal** context: model fixes a missing comma -> rater wrongly calls it unnecessary
- Model corrects word order (`别用力过猛一上来就` -> `别一上来就用力过猛`) -> rater wrongly calls it paraphrasing

### Failure Mode B: Under-Penalizing (missing unnecessary edits)
- In **Other** (informal) context: model adds missing periods, normalizes spacing -> rater accepts as necessary
- Model expands SMS abbreviation (`u` -> `you`) in casual chat -> rater does not flag
- Model removes emoji or normalizes `!!!` to `!` -> rater does not notice

### Prevention
Always anchor to formality FIRST. In Formal: minor fixes are necessary. In Other: same minor fixes become unnecessary edits. The SAME edit can be necessary or unnecessary depending entirely on formality classification.

## Error Category 3: Pairwise Forcing Differentiation

### Root Cause
Raters feel compelled to pick a "winner" even when two responses have identical Correctness and Completeness scores.

### Specific Errors
- Two responses both scored `all_necessary` + `complete` but rater picks one as "slightly better" based on subjective wording preference
- Two responses both scored `some_unnecessary` + `nearly_complete` but rater differentiates based on which unnecessary edit "feels" less bad
- Responses have genuinely different quality but rater marks `About the same` because both "seem OK"

### Prevention
**Mechanically compare the dimension scores.** If Correctness level and Completeness level are both identical -> `About the same`, period. If they differ on any dimension -> prefer the one with higher scores.

## Error Category 4: Q2 Micro-Change Blindness

### Root Cause
Raters visually scan responses and miss extremely subtle character-level differences.

### Specific Errors
- Missing that `API回應` changed to `API 回應` (space added)
- Missing that `「redis"` changed to `「redis」` (quotation mark paired)
- Missing full-width/half-width punctuation switch
- Missing simplified/traditional character conversion in a single word

### Prevention
**Character-level diff comparison is mandatory.** Do not rely on visual scanning. Any difference, no matter how small, means Q2 = has_edits.

## Severity Calibration Quick Reference

| Miss Rate | Completeness | Example |
|-----------|-------------|---------|
| 0% | complete | 0 of N errors missed |
| <20% | nearly_complete | 1 of 6+ errors missed |
| 20%-50% | partial_complete | 1 of 3-5 errors missed |
| >=50% | incomplete | 2+ of 4 errors missed |

| Unnecessary Edit Count | Correctness |
|----------------------|-------------|
| 0 unnecessary | all_necessary |
| 1+ unnecessary | some_unnecessary |
| ALL unnecessary | all_unnecessary |
