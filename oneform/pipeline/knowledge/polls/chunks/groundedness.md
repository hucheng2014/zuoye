# Groundedness

## Purpose
Evaluate whether the poll title and all options are grounded in (derived from) the actual conversation.

## Options
- `truthful` — Title and all options come from the conversation
- `not_truthful` — Title or options contain fabricated/unrelated content

## Truthful (Grounded) Standards

A poll is grounded when:
1. **Title** is relevant to the conversation topic (doesn't need to be a direct quote, but must relate to the actual discussion)
2. **All options** were explicitly mentioned by participants in the conversation
3. No hallucinated or fabricated content

## Not Truthful — Common Causes

### Fabricated Options
- Adding options that no participant mentioned
- Example: conversation discusses pizza and burgers, but poll includes "perogies" which nobody mentioned

### Unrelated Title
- Title has nothing to do with the conversation topic
- Title references a different discussion or context

### Background Info Misused as Options
- Taking general background information from the conversation and presenting it as poll options
- Example: someone mentions they visited Italy last year (background context), and this becomes a poll option for "next vacation destination" even though nobody suggested it

## CRITICAL: Distinction from Comprehensiveness

| What happened | Groundedness | Comprehensiveness |
|---------------|-------------|-------------------|
| All options come from conversation, but some mentioned options are missing | truthful | not_comprehensive |
| All mentioned options present, plus an extra fabricated one | not_truthful | comprehensive |
| Some options missing AND some fabricated | not_truthful | not_comprehensive |

**Key principle:** Groundedness checks "is everything in the poll real?" while Comprehensiveness checks "is everything from the conversation in the poll?"

### Example
Conversation mentions: pizza, burgers, ramen
- Poll: pizza, ramen -> **truthful** (both real), **not_comprehensive** (burgers missing)
- Poll: pizza, burgers, ramen, perogies -> **not_truthful** (perogies fake), **comprehensive** (all real ones present)

## Independence Note
A poll with fabricated options may still be Following Instructions (has title + >=2 options). Hallucination is penalized ONLY in Groundedness, not auto-propagated to Following Instructions.
