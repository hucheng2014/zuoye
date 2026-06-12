# Completeness (Q4)

## Purpose
Evaluate whether the response caught and corrected ALL objective errors in the input that require correction under the current formality level. Completeness is separate from Correctness: it measures what the model MISSED, not what it did wrong.

## Prerequisite
Completeness is only evaluated when Q1=has_grammar_errors AND Q2=has_edits. If Q2=no_edits (exact repeat with errors present), Completeness is automatically `incomplete`.

## Four Ratings by Miss Rate

### complete (0% missed)
All objective errors in the input were found and corrected. Nothing was overlooked.

### nearly_complete (<20% missed)
Only a tiny fraction of errors were missed.
- Quantified: when input has 6, 7, 8, or more errors, model missed only 1
- Example: 6 errors total, 5 fixed, 1 missed -> miss rate = 1/6 = 16.7% -> nearly_complete

### partial_complete (20%-50% missed)
A significant portion of errors were missed.
- Quantified: when input has 3, 4, or 5 errors, model missed 1; or when input has many errors and model missed several
- Example: 4 errors total, 3 fixed, 1 missed -> miss rate = 1/4 = 25% -> partial_complete
- Example: 10 errors total, 7 fixed, 3 missed -> miss rate = 3/10 = 30% -> partial_complete

### incomplete (>=50% missed)
Model missed half or more of the errors, or made no effective corrections at all.
- Example: 4 errors total, 1 fixed, 3 missed -> miss rate = 75% -> incomplete

## How to Calculate Miss Rate
1. **Before** evaluating any response, read the input text thoroughly and independently list ALL objective errors
2. Do NOT trust the model -- list errors yourself by reading the input word by word
3. Count total errors that must be fixed under current formality
4. For each response, count how many of those errors remain uncorrected
5. Miss rate = uncorrected errors / total errors

## missedErrors (required when completeness != complete)
Array of missed error categories. Values:
- `abbreviations` -- incorrect abbreviation handling left unfixed
- `awkward_edits` -- awkward/unnatural phrasing or semantic contradiction left unfixed
- `mild_punctuation_formatting` -- minor punctuation/formatting issues that do not impede comprehension
- `severe_punctuation_formatting` -- punctuation/formatting issues that impede comprehension
- `grammatical_mixups` -- common grammatical errors left unfixed
- `spelling_errors` -- spelling/typo errors left unfixed
- `poor_word_usage` -- wrong word usage left unfixed (e.g. `喺` vs `係` in zh-HK)
- `other` -- other types not covered above

## Formality Impact on Error Counting
In **Other** (informal) context, Minor Errors (missing periods, lowercase "i", comma splices) do NOT count as errors requiring correction. Only Critical Errors count toward the total. This means the same input may have different total error counts depending on formality classification.
