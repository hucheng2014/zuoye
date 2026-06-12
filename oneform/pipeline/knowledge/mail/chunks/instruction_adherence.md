# Instruction Adherence & Contextual Fit

## Purpose
Evaluate whether the draft completely follows the User Prompt instructions and fits the context established by the Previous Mail (the incoming email being replied to).

## 3 States

### Followed and Fit
The draft fully addresses all elements from the User Prompt and aligns naturally with the Previous Mail context.

Minor formatting or stylistic quirks are tolerated here, as long as core meaning and formality level match. Specifically:
- zh_HK: missing space after greeting comma, sign-off and name on same line = still Followed and Fit
- Minor line break differences from typical format = still Followed and Fit

### Partially Followed and Fit
The draft addresses the main instruction but has one of these specific issues:

**Situation 1 -- Name errors:**
The draft uses the wrong recipient name (e.g. writes "William" instead of "Mikail Can"), BUT the wrong name can be traced to a real name in the User Profile or other task fields. The name is real (so Groundedness is unaffected), but it is directed at the wrong person.

**Situation 2 -- Secondary detail omission:**
The draft completes the primary instruction from the User Prompt, but completely omits a secondary social point or secondary request from the Previous Mail.

Case study:
- Previous Mail: asks about meeting time AND thanks the user for last week's "berry puree recipe tips (barpur)"
- User Prompt: instructs to reply about the meeting time
- Draft: perfectly addresses meeting time, but completely ignores the berry puree thanks
- Verdict: **Partially Followed and Fit** (secondary social point omitted)

The key test: did the Previous Mail contain a secondary topic/thanks/question that the draft completely ignored? If yes, it is Partially regardless of how well the primary instruction was handled.

**Situation 3 -- Slight formality mismatch:**
The draft's core meaning is correct, but its formality level has a slight mismatch with the expected register for this context (e.g. slightly too casual for a business context, or slightly too formal for a close friend).

### Not Followed or Misfit
The draft severely deviates from the topic, violates the core instruction, or has a formality level completely misaligned with the context.

Examples:
- Prompt says "decline the invitation" but draft accepts it
- Previous Mail is about a business proposal but draft discusses personal matters
- Formal business context but draft uses heavy slang and abbreviations

## Common Pitfalls
1. Rating "Followed and Fit" while ignoring secondary detail omissions (must check Previous Mail thoroughly for secondary points)
2. Conflating name errors with Groundedness failures (name errors go HERE, not in Groundedness)
3. Over-penalizing minor zh_HK formatting issues that should remain "Followed and Fit"
