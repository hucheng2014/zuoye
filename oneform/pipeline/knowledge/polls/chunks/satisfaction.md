# Satisfaction

## Purpose
Holistic quality assessment integrating all other dimensions.

## Options (4 levels)
- `highly_satisfying`
- `satisfying`
- `slightly_satisfying`
- `not_satisfying`

## Highly Satisfying
ALL of the following must be true:
- Poll existence is appropriate (yes_reply/consensus_reply confirmed)
- Title is relevant and accurately expresses the discussion topic
- Options are unique, complete, in first-appearance order, and all grounded in conversation
- Title and options are written naturally and concisely (good Composition)
- Poll would genuinely help participants communicate and reach consensus
- No safety, localization, or other serious issues

## Satisfying
- Response is overall helpful
- Only minor text issues (slight typo, minor phrasing preference)
- All other aspects are basically correct

## Slightly Satisfying
- Response is partially helpful and not harmful
- Multiple major issues present, such as:
  - Bad Composition (question title, long options)
  - Ungrounded title or options
  - Missing or duplicate options
  - Obvious localization problems
  - Combination of several moderate problems

## Not Satisfying
- Poll is very inappropriate or unhelpful
- Severe issues including:
  - Harmful content
  - Misleading title or options
  - Severe writing problems
  - Inappropriate tone
  - Severe localization problems

### CRITICAL RULE
**If Proper No Reply = no_reply but a poll was generated -> Satisfaction MUST be `not_satisfying`.**

This is an absolute rule, not a guideline. The poll's existence itself is wrong, making the entire response unsatisfying regardless of how well the poll is written internally.

## Relationship to Other Dimensions
Satisfaction is the final integrative assessment. While it considers all other dimensions, it is NOT a simple sum. A single critical failure (e.g., harmful content, or generating an unwanted poll) can drive Satisfaction to not_satisfying even if other dimensions are fine.

Conversely, minor issues in multiple dimensions might only result in slightly_satisfying if the overall poll is still somewhat useful.
