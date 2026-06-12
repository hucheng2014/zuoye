# Pairwise Comparison

## Purpose
Perform the final Side-by-Side (SBS) preference ranking between Response A and Response B. The pairwise verdict MUST be strongly consistent with all individual dimension scores to prevent cascading errors.

## 4-Level Priority Framework

Evaluate in this strict priority order. Higher-priority factors override lower ones.

### Priority 1: Instruction Adherence (Highest)
Prefer the draft that perfectly follows ALL core AND secondary details from the User Prompt and Previous Mail.

- One draft is "Followed and Fit" and the other is "Partially" or "Not Followed" -> strongly prefer the one that followed
- Both "Followed and Fit" -> move to Priority 2
- Both "Partially" -> compare which one missed less, then move to Priority 2

### Priority 2: Groundedness
Penalize drafts with factual fabrication.

- "Grounded" > "Partially Grounded" > "Not Grounded"
- A "Not Grounded" draft with severe hallucination that changes core meaning should be strongly disfavored
- A "Partially Grounded" draft with only minor invented details is better than "Not Grounded" but worse than "Grounded"

### Priority 3: Locale Compliance + Style Fidelity
When instruction adherence and groundedness are equal, compare locale and personalization quality.

- Draft that matches locale punctuation rules > draft with localization issues
- "Personalized" or "Contextually Adapted" > "Generic" > "Mismatch"
- Better tone/empathy alignment in context-appropriate situations

### Priority 4: Equal Quality Rule (CRITICAL)
**Two responses do NOT need to be identical to be rated equal.** If they differ in specific word choices, sentence structures, or minor stylistic preferences, but their objective scores across all prior dimensions are the same, they MUST be judged as **A=B (About the same)**.

Do NOT prefer one response over another based purely on subjective taste when dimension scores match.

## Cascading Error Prevention

The pairwise comparison is the final check that must align with all individual scores. Common cascading errors to watch for:

1. **Groundedness cascade**: Rating a draft "Not Grounded" in the individual assessment but then preferring it in pairwise because it "sounds better" -> WRONG
2. **Instruction cascade**: Rating both drafts "Followed and Fit" individually but then preferring one for "better following instructions" in pairwise -> inconsistent, should be equal on this factor
3. **Personalization cascade**: Rating one draft "Generic" individually but then calling pairwise "About the same" when the other is "Personalized" -> inconsistent

## Observation Writing
After determining the pairwise preference, write a short English observation (2-4 sentences) that:
- Points out the key differences between the two responses
- Justifies the preference based on the priority framework
- References specific dimension scores that drove the decision
