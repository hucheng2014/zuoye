# Common Errors (May 22 Feedback RCA)

## Purpose
Root cause analysis of the most frequent rating deviations identified in the official WT Mail Smart Reply (MSR) Feedback & Calibration report (May 22, 2026). Use this as a checklist to avoid the same mistakes.

## Error Category 1: Personalization Miscalibration
**Most prevalent deviation dimension.**

### Root Cause
Raters apply subjective judgment and ignore the explicit guideline definition of "Contextually Adapted."

### Specific Errors
- **Contextually Adapted -> Generic**: Seeing any deviation from profile and calling it Generic, when the deviation is a natural context-driven adaptation (e.g. lacks_formatting profile but business email -> paragraphs added)
- **Contextually Adapted -> Mismatch**: Treating context-appropriate style shifts as contradictions of the profile
- **Ignoring Excessive Padding**: Not penalizing drafts stuffed with filler phrases that inflate length beyond the sender's typical brevity

### Prevention
Always ask: "Is this style change justified by the email context and relationship?" If yes -> Contextually Adapted, not Generic/Mismatch.

## Error Category 2: Groundedness Over/Under-Penalization

### Under-Penalization (Missing Real Hallucinations)
- Accepting fabricated quantities (e.g. "1 project" when prompt just says "new projects")
- Accepting fabricated progress/intent assertions
- Not noticing invented interaction history

### Over-Penalization (False Hallucination Flags)
- **#1 cause**: Failing to check Additional Personal Info field before ruling "Not Grounded"
- Marking interview times/schedule details as hallucinated when they exist in Additional Info
- Penalizing names in Groundedness when names should only be evaluated in Contextual Fit

### Prevention
Mandatory pre-check: read ALL Additional Personal Info content before scoring Groundedness. Apply Name Grounding Rule.

## Error Category 3: Localization Misses

### Missed Localization Errors
- Not catching da_DK/nb_NO comma violations (greeting/sign-off commas)
- Not catching zh_TW full-width punctuation violations
- Not catching nb_NO name comma placement errors

### False Localization Flags
- Marking spelling errors as Localization Issue (spelling != localization)
- Marking grammar errors as Localization Issue (grammar != localization)
- Over-penalizing zh_HK minor formatting (which should be tolerated)

### Prevention
Check locale-specific punctuation rules systematically. Remember: only format/punctuation violations count as Localization, not spelling/grammar.

## Error Category 4: Instruction Adherence Confusion

### Root Cause
Raters default to "Followed and Fit" without carefully reading Previous Mail for secondary social points.

### Specific Errors
- Ignoring secondary topic omission (e.g. Previous Mail thanks for recipe tips, draft ignores it)
- Ignoring wrong recipient name and giving full marks
- Conflating minor zh_HK formatting with instruction non-compliance

### Prevention
Read Previous Mail carefully for ALL secondary questions/thanks/social points. Check recipient name correctness.

## Error Category 5: Pairwise Cascading

### Root Cause
Individual dimension scores contain errors, which then cascade into an incorrect pairwise comparison.

### Common Pattern
1. Groundedness is mis-scored (either too harsh or too lenient)
2. This makes one response look worse/better than it actually is
3. Pairwise preference follows the wrong Groundedness assessment
4. Final verdict is inconsistent with what correct individual scores would produce

### Prevention
After completing all individual scores, review them for internal consistency before writing the pairwise comparison. If pairwise preference contradicts any individual dimension score, re-examine both.
