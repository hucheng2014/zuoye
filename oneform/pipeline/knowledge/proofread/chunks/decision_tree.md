# Q1-Q2-Q3-Q4 Decision Tree

## Purpose
Defines the exact branching logic for each response (A, B, C). The path through the tree determines which fields appear in the JSON answer.

## Q1: Does the input have errors? (applies to ALL responses equally)
- **`no_grammar_errors`**: input is clear and readable for its formality level. No objective grammar/spelling errors.
  - Do NOT mistake informal style for errors (e.g. missing final period in chat is NOT an error in Other context)
- **`has_grammar_errors`**: input contains objective errors requiring correction (typos, grammar violations, severe punctuation issues)
- **`vague_intent`**: text is so unclear/garbled it cannot be assessed (extremely rare)

## Q2: Did the response change the input? (per response)
- **`has_edits`**: response differs from input in ANY way -- even one space, one punctuation mark, one character change
  - Use character-level diff comparison; do NOT rely on visual scanning
  - Full-width vs half-width change = has_edits
  - Added/removed space between CJK and Latin = has_edits
- **`no_edits`**: response is identical to input (exact repeat)
  - If UI truncation makes response appear shorter, assume omitted parts are unchanged

## Branch Map

### Branch 1: Q1=no_grammar_errors + Q2=no_edits
- Result: Exact repeat of correct text. Perfect behavior.
- JSON fields: `q2` only. No Q3/Q4 needed.

### Branch 2: Q1=no_grammar_errors + Q2=has_edits
- Triggers: `alteredMeaning` question
- `alteredMeaning: "no"` -- edits are cosmetic, did not change meaning/tone/style
- `alteredMeaning: "yes"` -- edits changed substance (synonym swap, restructuring, formality shift)
- JSON fields: `q2`, `alteredMeaning`. No correctness/completeness.

### Branch 3: Q1=has_grammar_errors + Q2=no_edits
- Result: Model did nothing despite errors existing. Completeness is automatically `incomplete`.
- JSON fields: `q2` only. System auto-scores.

### Branch 4: Q1=has_grammar_errors + Q2=has_edits (MOST COMMON)
- Triggers BOTH Correctness (Q3) and Completeness (Q4)
- JSON fields: `q2`, `correctness`, `editsCorrect`, `completeness`
- Conditional arrays:
  - `correctnessErrors[]` -- only when `editsCorrect = "some_incorrect"`
  - `unnecessaryEdits[]` -- only when `correctness = "some_unnecessary"` or `"all_unnecessary"`
  - `missedErrors[]` -- only when `completeness != "complete"`

## Conditional Field Summary Table

| Condition | Field | Required? |
|-----------|-------|-----------|
| Q1=no_errors + Q2=has_edits | `alteredMeaning` | Yes |
| Q1=has_errors + Q2=has_edits | `correctness` | Yes |
| Q1=has_errors + Q2=has_edits | `editsCorrect` | Yes |
| Q1=has_errors + Q2=has_edits | `completeness` | Yes |
| editsCorrect = some_incorrect | `correctnessErrors[]` | Yes |
| correctness = some_unnecessary / all_unnecessary | `unnecessaryEdits[]` | Yes |
| completeness != complete | `missedErrors[]` | Yes |

## IMPORTANT
- Q1 is shared across all three responses (same input for A, B, C)
- Q2, Q3, Q4 are evaluated independently per response
- Do not let one response's scoring influence another's
