# Following Instructions

## Purpose
Evaluate whether the assistant followed the task instruction: generate a valid poll when appropriate, or produce empty response when not.

## Options
- `following_instructions` — Correctly followed instructions
- `not_following_instructions` — Did not follow instructions

## Following Instructions (Pass)

A response passes if ONE of:
1. **Poll appropriate + valid poll generated**: response has a clear title AND >=2 unique options
2. **No poll appropriate + empty response**: correctly abstained from generating

## Not Following Instructions (Fail)

A response fails if ANY of:
- Should NOT have a poll but generated one anyway
- Should have a poll but produced empty or no poll
- Poll is missing a title
- Poll has fewer than 2 options
- Poll has duplicate options (same option appearing twice)

## CRITICAL: Independence from Other Dimensions

This is the most common scoring mistake. Following Instructions is ONLY about:
- Whether a poll was generated when it should/shouldn't have been
- Whether the poll has the minimum required structure (title + >=2 unique options)

### What does NOT cause Not Following:

| Scenario | Following Instructions | Affected Dimension |
|----------|----------------------|-------------------|
| Hallucinated/fabricated options | Still Following (has title + >=2 options) | Groundedness |
| Missing some conversation options | Still Following (has title + >=2 options) | Comprehensiveness |
| Bad title (question instead of phrase) | Still Following (title exists) | Composition |
| Merged options + empty option slot | Still Following (has title + options set) | Composition |
| Options in wrong order | Still Following (structure intact) | Comprehensiveness |
| Ungrounded title | Still Following (title exists) | Groundedness |

### What DOES cause Not Following:

- No title at all
- Only 1 option (or 0 options)
- Exact duplicate options ("Pizza" appearing twice)
- Generated poll when no poll was appropriate
- No poll when poll was appropriate

## Engineering Clarification (from FAQ)
The official FAQ explicitly states: "Do not establish an automatic connection of 'option not grounded, therefore Not Following.' The guide does not write this automatic derivation, so scoring cannot work this way." Each dimension uses its own criteria independently.
