# Pairwise Comparison

## Structure
Three pairs for three responses: **AvsB**, **AvsC**, **BvsC**.

## Operators
- `A>B` -- A is slightly better than B
- `A>>B` -- A is better than B
- `A>>>B` -- A is much better than B
- `A=B` -- About the same (no meaningful quality difference)

Reverse: `B>A`, `B>>A`, `B>>>A` when B is preferred.

## Tab Letter Order Rule (CRITICAL)
The value notation always puts the **left letter of the Tab name first**:
- AvsB tab: use `A>B` or `B>A` or `A=B` (never `B=A`)
- AvsC tab: use `A>C` or `C>A` or `A=C`
- BvsC tab: use `B>C` or `C>B` or `B=C`

## Extreme Rule: Equal Quality = About the Same
**Two responses do NOT need to be identical (not word-for-word) to be rated equal.** If they differ in specific word choices, sentence structures, or minor stylistic preferences, but their Correctness and Completeness scores are the same, they MUST be judged as **About the same**.

Do NOT force differentiation when objective quality is equal.

## Decision Framework

### Step 1: Compare Correctness
- `all_necessary` > `some_unnecessary` > `all_unnecessary`
- `all_correct` > `some_incorrect`
- If one response has `all_necessary` and another has `some_unnecessary`, the first is better

### Step 2: Compare Completeness
- `complete` > `nearly_complete` > `partial_complete` > `incomplete`
- If one response is `complete` and another is `nearly_complete`, the first is slightly better (`>`)
- If one is `complete` and another is `incomplete`, the first is much better (`>>>`)

### Step 3: Determine Operator Strength
- Same Correctness + same Completeness = `=` (About the same)
- One dimension differs by 1 level = `>` (slightly better)
- One dimension differs by 2+ levels = `>>` (better)
- Multiple dimensions differ significantly = `>>>` (much better)
- alteredMeaning=yes is a significant penalty

### Step 4: Verify Consistency
The pairwise comparison MUST be consistent with individual dimension scores:
- Do NOT prefer a response you scored lower on Correctness/Completeness
- Do NOT call two responses "About the same" if their individual scores differ
- If you find inconsistency, re-examine the individual scores before finalizing

## Observation Writing
After determining all three pairwise verdicts, write a short English observation (1-3 sentences) that:
- States which response is most preferred and why
- References the key Correctness/Completeness differences
- Must match the observation in answers.json exactly
