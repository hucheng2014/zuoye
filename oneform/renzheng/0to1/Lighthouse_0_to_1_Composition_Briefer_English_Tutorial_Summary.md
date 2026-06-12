# Lighthouse 0 to 1 Composition Briefer — English Tutorial Summary

> Source: `Lighthouse_0 to 1 Composition Briefer.pdf`  
> Topic: Clarifications for judging additional-information necessity, email subjects, and supplementary suggestions in 0-to-1 Composition tasks.

---

## 1. Necessity of Additional Information

When deciding whether additional information is needed, judge from:

- the user instruction;
- the user-provided context;
- what is required to complete the writing task.

Do not mix the user instruction/context with the **Additional Personal Information** shown in the response section.

Key principles:

1. The user instruction may be missing critical details, so the task may still require additional information.
2. Those critical details may appear in Additional Personal Information and may be used in the final response.
3. Keep two questions separate:
   - Does the instruction itself require more information to complete the task?
   - Did the model correctly use available personal information in the response?
4. Suggested information from the model does not automatically mean the instruction needs more information. Suggestions may simply be complementary.

Bottom line: **Necessity depends on whether the user request lacks essential details, not on whether the model suggests extra information.**

---

## 2. Additional Personal Information and Hallucination

Additional Personal Information comes from the user’s device and is meant to help produce a better response.

If the response uses information from that section and the information is correct, do not penalize it as hallucination.

Remember:

- Do not mark hallucination just because the fact was not in the user’s instruction text.
- If the fact is supported by Additional Personal Information, it has a source.
- True hallucination means fabricating unsupported specific facts such as names, dates, places, prices, or numbers.

---

## 3. Email Subject Evaluation

Email subjects should be checked against each criterion. If the subject fails a criterion, leave that option unselected.

Common failure points:

- overly subjective or exaggerated language;
- verbosity or excessive detail;
- not following Title Case;
- covering more than one topic;
- incorrectly capitalizing articles, conjunctions, or prepositions that should be lowercase unless they are the first or last word.

Do not mark every option just because the subject is understandable. Each checkbox must match a specific standard.

---

## 4. Supplementary Information / Suggestions

A suggestion is Helpful only when it genuinely supports the composition.

Mark **Helpful** when the suggestion:

- is directly related to the composition;
- adds useful missing information;
- makes the main content more complete, actionable, or context-appropriate.

Mark **Neutral** when the suggestion:

- is about device actions, such as setting reminders or calling someone, rather than the composition itself;
- repeats information already provided;
- is relevant but low-value or optional;
- may already be covered by the existing context.

Do not assume every suggestion is automatically Helpful. It must add value to the writing task.

---

## 5. Practical Checklist

1. Judge additional-information need from the user instruction and context first.
2. Correct use of Additional Personal Information is not hallucination.
3. Model suggestions do not automatically imply that the missing information is critical.
4. Evaluate email subjects criterion by criterion: subjectivity, length, Title Case, one topic, and capitalization rules.
5. Suggestions are Helpful only when they supplement the composition itself; device actions or redundant suggestions are usually Neutral.
