# JSON Answer Format

## Complete Structure

```json
{
  "formality": "formal | other",
  "q1": "no_grammar_errors | has_grammar_errors | vague_intent",
  "responses": {
    "A": { /* per-response fields */ },
    "B": { /* per-response fields */ },
    "C": { /* per-response fields */ }
  },
  "pairwise": {
    "AvsB": "A>B | A>>B | A>>>B | B>A | B>>A | B>>>A | A=B",
    "AvsC": "A>C | A>>C | A>>>C | C>A | C>>A | C>>>A | A=C",
    "BvsC": "B>C | B>>C | B>>>C | C>B | C>>B | C>>>B | B=C"
  },
  "observation": "English 1-3 sentences explaining preference."
}
```

## Per-Response Fields (Conditional)

### When Q1=no_grammar_errors + Q2=has_edits
```json
{
  "q2": "has_edits",
  "alteredMeaning": "yes | no"
}
```

### When Q1=no_grammar_errors + Q2=no_edits
```json
{
  "q2": "no_edits"
}
```

### When Q1=has_grammar_errors + Q2=no_edits
```json
{
  "q2": "no_edits"
}
```

### When Q1=has_grammar_errors + Q2=has_edits (most common)
```json
{
  "q2": "has_edits",
  "correctness": "all_necessary | some_unnecessary | all_unnecessary",
  "editsCorrect": "all_correct | some_incorrect",
  "completeness": "complete | nearly_complete | partial_complete | incomplete"
}
```

#### Optional arrays (conditional):
```json
{
  "correctnessErrors": ["..."],
  "unnecessaryEdits": ["..."],
  "missedErrors": ["..."]
}
```

## Field Conditional Rules

| Condition | Field | Required |
|-----------|-------|----------|
| Q1=no_errors + Q2=has_edits | `alteredMeaning` | Yes |
| Q1=has_errors + Q2=has_edits | `correctness` | Yes |
| Q1=has_errors + Q2=has_edits | `editsCorrect` | Yes |
| Q1=has_errors + Q2=has_edits | `completeness` | Yes |
| `editsCorrect` = `some_incorrect` | `correctnessErrors` | Yes |
| `correctness` = `some_unnecessary` or `all_unnecessary` | `unnecessaryEdits` | Yes |
| `completeness` != `complete` | `missedErrors` | Yes |

## Enum Values Reference

### correctnessErrors (edit was wrong)
`punctuation`, `spacing`, `new_errors`, `impede_comprehension`, `out_of_locale`, `wrong_article`, `voice_alteration`, `formality_alteration`, `word_choice_alteration`, `code_switch`, `register_alteration`, `other`

### unnecessaryEdits (edit was not needed)
`punctuation`, `capitalization`, `spacing`, `mechanical`, `abbreviations`

### missedErrors (error in input was not fixed)
`abbreviations`, `awkward_edits`, `mild_punctuation_formatting`, `severe_punctuation_formatting`, `grammatical_mixups`, `spelling_errors`, `poor_word_usage`, `other`

## Full Example

```json
{
  "formality": "other",
  "q1": "has_grammar_errors",
  "responses": {
    "A": {
      "q2": "has_edits",
      "correctness": "all_necessary",
      "editsCorrect": "all_correct",
      "completeness": "complete"
    },
    "B": {
      "q2": "has_edits",
      "correctness": "some_unnecessary",
      "editsCorrect": "all_correct",
      "unnecessaryEdits": ["punctuation", "mechanical"],
      "completeness": "complete"
    },
    "C": {
      "q2": "has_edits",
      "correctness": "some_unnecessary",
      "editsCorrect": "some_incorrect",
      "correctnessErrors": ["new_errors"],
      "unnecessaryEdits": ["punctuation"],
      "completeness": "nearly_complete",
      "missedErrors": ["spelling_errors"]
    }
  },
  "pairwise": {
    "AvsB": "A>B",
    "AvsC": "A>>>C",
    "BvsC": "B>C"
  },
  "observation": "Response A corrected the critical typo with no unnecessary changes. Response B added unnecessary punctuation edits. Response C introduced a new error and missed a spelling correction."
}
```

## Pairwise Value Format
- Left letter is always the Tab-left letter: AvsB -> `A>B` or `B>A` or `A=B`
- Equal is always written as `X=Y` where X is the left letter: `A=B`, `A=C`, `B=C`
- Never write `B=A` or `C=A` or `C=B`
