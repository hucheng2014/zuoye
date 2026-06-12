# Lighthouse_TA Intelligent Polls_Questions English Summary

> Source: `Lighthouse_TA Intelligent Polls_Questions.pdf`  
> Topic: FAQ clarifications for Intelligent Polls evaluation.

## 1. Document Purpose

This Questions document supplements the main guideline. It clarifies four common edge cases:

1. Whether to penalize any dimension when no poll is appropriate and the response is empty.
2. How to evaluate Comprehensiveness when no poll is appropriate but the model still generates a poll.
3. Whether Following Instructions is automatically affected by Comprehensiveness or Groundedness.
4. Whether the poll must exactly follow the format and punctuation shown in examples.

## 2. No Poll Is Appropriate + Empty Response

If `No poll is appropriate` is selected and the model response is empty, the model behaved correctly.

Key points:

- Do not penalize any dimension just because the response is empty.
- The empty response is expected and correct.
- This should not be treated as a poor result in the backend.
- This matches the main guideline: when no poll should exist, generating no poll is correct.

## 3. No Poll Is Appropriate + Non-Empty Poll

If no poll is appropriate but the model still generates a poll, graders should still evaluate the generated poll as well as possible, especially for Comprehensiveness.

Engineering clarification:

- Follow the Comprehensiveness guideline and decide whether the generated poll covers the identifiable explicit options.
- This may feel odd because the poll itself is inappropriate, but the dimensions should still be assessed independently where possible.
- Following Instructions, Composition, and Groundedness should also be judged by their own definitions.
- Under the main guideline, generating a poll when no poll should exist makes Satisfaction highly negative, but it does not automatically make every sub-dimension fail.

Practical interpretation:

- First record that generating a poll was the wrong behavior.
- Then evaluate whether that poll is well-written, grounded, and comprehensive internally.
- Do not stop evaluating all dimensions solely because Proper No Reply was wrong, unless the task UI specifically ends the flow.

## 4. Independence of Following Instructions

The question raised a concern that because the main guideline mentions omissions or repeated options under Not Following, Comprehensiveness or Groundedness might automatically determine Following Instructions.

Engineering clarification:

- Do not infer that an ungrounded option automatically makes the response Not Following.
- That connection is not stated in the guideline.
- A poll can be instruction-following by having a title and 2 or more options, while still having an ungrounded title or option.
- Evaluate each dimension independently and avoid letting one dimension influence another.

Practical rule:

- Groundedness checks whether the title and options are supported by the conversation.
- Comprehensiveness checks whether all explicit options are included in order.
- Following Instructions checks the generate/no-generate decision and basic poll structure according to its own definition.
- Use Not Following when there is an explicit Following Instructions issue, such as no title, not enough options, duplicated options, or clear structural failure.
- Do not mark Not Following solely because an option is hallucinated; penalize that under Groundedness.

## 5. Format and Punctuation Do Not Need to Match Examples

The examples often use a format like:

```text
Title:
XXX
Options:
- XXX
- XXX
```

Engineering clarification:

- The poll does not need to exactly follow that format.
- If punctuation is not specified in the guideline, do not penalize merely because punctuation differs.
- The poll must still have an explicit title and an explicit set of options.
- The quality of the title and options is what matters.

Practical rule:

- Do not penalize just because `Title:`, `Options:`, bullet style, colon use, capitalization, or punctuation differ from examples.
- If the title and options are clearly identifiable, formatting differences are usually not an issue.
- If formatting makes the title or options unclear, it may affect Following Instructions or Composition.

## 6. Practical Takeaways

1. First decide whether a poll should exist.
2. An empty response is correct when no poll is appropriate.
3. If an inappropriate poll is generated, still evaluate the poll’s internal quality where possible.
4. Keep Groundedness, Comprehensiveness, and Following Instructions separate.
5. Title and options must be explicit, but exact example formatting is not required.
