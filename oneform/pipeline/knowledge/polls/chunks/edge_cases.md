# Edge Cases & FAQ

## Case 1: Empty Response for No-Poll Scenarios

**Scenario:** Proper No Reply = no_reply, and the model response is empty.

**Rule:** This is CORRECT behavior. The model correctly identified that no poll should be generated.

- Only fill Proper No Reply = `no_reply`
- Other dimensions do NOT need evaluation
- Do NOT mark empty response as low quality
- Do NOT penalize any dimension for the emptiness
- Submit with only the Proper No Reply field filled

## Case 2: Generated Poll When No Poll Appropriate

**Scenario:** You determine no poll should exist, but the model generated one anyway.

**Rule:** Continue evaluating all dimensions independently despite the fundamental error.

- Proper No Reply = `no_reply`
- Following Instructions = `not_following_instructions` (shouldn't have generated)
- Composition / Comprehensiveness / Groundedness = evaluate the poll's internal quality independently
- Satisfaction = `not_satisfying` (mandatory -- the poll shouldn't exist)
- Do NOT stop evaluating just because the poll shouldn't exist

## Case 3: Format/Punctuation Flexibility

**Scenario:** The poll doesn't follow the example format (e.g., missing `Title:` / `Options:` labels, different punctuation style).

**Rule:** Do NOT penalize for formatting differences.

- The poll does not need to match any specific template
- Don't penalize for missing colons, dashes, bullet points, or label prefixes
- Don't penalize for capitalization or punctuation style differences
- What matters: can you clearly identify the title and options?
- If format makes title/options unidentifiable -> then it may affect Following or Composition

## Case 4: Merged Options ("Pizza and Burgers" Example)

**Scenario:** Two distinct options are merged into one entry, often with an empty option slot.

```
Title: Food Options
Options:
- Pizza and Burgers
- [empty]
```

**Dimension-by-dimension analysis:**

| Dimension | Verdict | Reasoning |
|-----------|---------|-----------|
| Following Instructions | following | Has title + option set (structure exists) |
| Groundedness | truthful | Pizza and Burgers both come from conversation |
| Composition | bad | Options merged unnaturally, empty slot present |
| Comprehensiveness | debatable | Options appear but can't be voted on separately; not presented in independent first-appearance order |

**Key takeaway:** This case perfectly illustrates dimension independence. The response can pass Following and Groundedness while failing Composition.

## Case 5: Already-Rejected Options

**Scenario:** An option was mentioned but then explicitly rejected or vetoed.

**Rule:**
- Rejected options should NOT be included in the poll
- Including a rejected option = `not_comprehensive` (it shouldn't be there)
- Correctly excluding a rejected option = `comprehensive`
- Example: someone suggests sushi, another replies "Absolutely not, I'm allergic" -> sushi should not be a poll option

## Case 6: Typos in Conversation

**Scenario:** Conversation contains obvious typos (e.g., "fight to Italy" meaning "flight to Italy").

**Rule:** The poll should correct inferable typos.
- Not correcting = bad Composition
- The poll is meant to be a clean, usable voting tool
