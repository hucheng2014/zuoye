# Comprehensiveness

## Purpose
Evaluate whether the poll covers ALL distinct options mentioned in the conversation, in the correct order.

## Options
- `comprehensive` — All options present in correct order
- `not_comprehensive` — Missing options, wrong order, or includes rejected options

## Comprehensive Standards

A poll is comprehensive when:
1. It includes **all distinct options** explicitly mentioned by participants
2. Options appear in **first-appearance order** (matching when each was first mentioned in conversation)
3. No duplicate options

## Not Comprehensive — Common Causes

### Missing Options
- Conversation mentions pizza, burgers, and ramen, but poll only has pizza and burgers -> missing ramen

### Wrong Order
- Conversation first mentions burgers, then pizza, but poll lists pizza first -> wrong order

### Duplicate Options
- Same option appears twice in the poll

### Including Already-Rejected Options
- A participant suggests sushi, another says "No way, I'm allergic to fish", group moves on
- Poll should NOT include sushi -> including it = not_comprehensive
- Correctly excluding it = comprehensive

## CRITICAL: Distinction from Groundedness

This is the most important boundary to understand:

| Scenario | Comprehensiveness | Groundedness |
|----------|------------------|--------------|
| Missing a mentioned option | not_comprehensive | truthful (remaining options are real) |
| Extra fabricated option added | comprehensive (all real ones present) | not_truthful |
| Both missing AND fabricated | not_comprehensive | not_truthful |

**Rule of thumb:**
- **Omission** = Comprehensiveness problem
- **Fabrication** = Groundedness problem

### Example
Conversation mentions: pizza, burgers, ramen
- Poll has: pizza, ramen -> **Grounded** (both exist in conversation) but **Not Comprehensive** (missing burgers)
- Poll has: pizza, burgers, ramen, perogies -> **Comprehensive** (all mentioned options present) but **Not Grounded** (perogies fabricated)

## Merged Options Edge Case
When options are merged (e.g., "Pizza and Burgers" as one option):
- The two options are not presented as independent choices
- Comprehensiveness is debatable -- they "appear" but cannot be voted on separately
- Consider whether the merger prevents participants from expressing individual preferences
