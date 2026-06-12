# Proofread V2 (Chinese) -- Compact Scoring Rules

## IRON LAW: Minimal Edit Principle
Correct ONLY objective grammar/spelling/punctuation errors. Preserve tone, style, formality, expressivity, proper nouns, abbreviations, formatting, locale conventions. Any synonym substitution, sentence restructuring, or tone shift without objective error = unnecessary edit.

## V2 Core: Only 2 Derived Dimensions
System computes scores from Y/N answers. Grader answers Q1-Q4; system derives Correctness + Completeness.

## Formality Classification (MUST do first)
- **Formal**: academic, legal, government, business, news
- **Other**: chat, SMS, social media, informal conversation

## Three-Level Error Framework
- **Critical Errors**: must fix in ALL contexts (blocks comprehension, changes meaning, core grammar)
- **Minor Errors**: must fix Formal, optional in Other (missing apostrophes, comma splices, missing periods, lowercase "i")
- **Stylistic Choices**: PRESERVE always (emoji, repeated punctuation, elongated spelling, slang, hashtags)

## Q1: Input has errors?
- `no_grammar_errors`: text is acceptable for its formality level
- `has_grammar_errors`: objective spelling/grammar errors exist
- `vague_intent`: incomprehensible (rare)

## Q2: Response changed input?
- `has_edits`: ANY difference (even one space/punctuation change) = Yes
- `no_edits`: exact repeat = No

## Q3: Correctness (evaluates edits made)
- **If Q1=no_errors + Q2=has_edits**: `alteredMeaning` yes/no (did edits change meaning/tone/style?)
- **If Q1=has_errors + Q2=has_edits**:
  - `correctness`: `all_necessary` | `some_unnecessary` | `all_unnecessary`
  - `editsCorrect`: `all_correct` | `some_incorrect`
  - ONE unnecessary edit (even just punctuation in informal) -> `some_unnecessary`
  - Non-formal tolerance: punctuation/spacing/capitalization changes that don't alter meaning in Other context = unnecessary edits
  - SMS abbreviations (u, r, lol, btw) in informal = PRESERVE, expanding them = unnecessary

## Q4: Completeness (evaluates errors missed)
- `complete`: 0% missed
- `nearly_complete`: <20% missed (e.g. 1 of 6+ errors)
- `partial_complete`: 20-50% missed (e.g. 1 of 3-5 errors)
- `incomplete`: >=50% missed

## Pairwise: AvsB, AvsC, BvsC
- Operators: `>` slightly better, `>>` better, `>>>` much better, `=` about the same
- **Extreme Rule**: identical Correctness + Completeness scores = "About the same" even if wording differs
- Tab letter order: left letter first in notation (e.g. `A>B` not `B<A`)
