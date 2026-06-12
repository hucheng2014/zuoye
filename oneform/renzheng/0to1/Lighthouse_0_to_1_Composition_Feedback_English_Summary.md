# Lighthouse 0 to 1 Composition Feedback — English Summary

> Source: `Lighthouse_0 to 1 Composition Feedback.pdf`  
> Topic: Certification / workflow feedback for 0-to-1 Composition, focused on the dimensions analysts most often misjudge.

---

## 1. Before Starting

The document reminds analysts to watch the webinar for the new workflow before making their first attempt. Many judgments depend on consistent understanding of the rubric.

---

## 2. Necessity for Additional Information

Additional information is necessary only when it is required to complete the task. This may include:

- the user’s personal information;
- key context details;
- facts that require web search or fact-checking.

Before answering the first question, carefully read the user instruction and any context. In many cases, extra information would be helpful but is not mandatory.

### Examples

- `Thank him for reaching out and propose a new meeting time`  
  The AI needs the user’s available times to propose a new meeting time, so personal information is necessary.

- `Tell Ian I’ll check the price for the laptop for Rohan`  
  This is a straightforward reply. No additional information is needed.

- `Ask John to let me know his availability`  
  The user is only asking John to provide availability. The AI does not need the user’s own schedule.

Bottom line: **Critical information means information required to complete the task, not merely information that would make the response better.**

---

## 3. Critical Issues / Hallucination

Do not mark a response as hallucination if the information is correctly extracted from **Additional Personal Information**.

When judging hallucination, consider:

- the user input;
- any context;
- Additional Personal Information;
- general knowledge or web search when needed.

Mark Hallucination when the response fabricates specific unsupported information such as:

- names;
- places;
- prices;
- numbers;
- dates;
- facts;
- company-specific processes or policies.

Do not over-mark hallucination for generic phrasing. For example, a phrase like `office celebration for the hard work` is usually not a fabricated specific fact in this task context.

The feedback notes that only one task in the certification had a truly hallucinated response, and many graders missed it. Be especially alert to unsupported specific details.

---

## 4. Email Subject Evaluation

Email subject evaluation is a “select all that apply” step. If a criterion is not met, leave that option unselected.

Common missed issues:

- incorrect Topic + action noun structure, such as `Request to Meet` instead of `Meeting Request`;
- more than one topic in the subject;
- capitalizing conjunctions, articles, or prepositions that should be lowercase when not first or last;
- failing to capitalize first/last words, nouns, verbs, adverbs, or adjectives in Title Case;
- being too verbose or detailed instead of general;
- using subjective, exaggerated, or marketing-like language.

Bottom line: **Each checkbox corresponds to a concrete criterion. Do not select everything just because the subject is understandable.**

---

## 5. Instruction Following, Tone, Completeness, and Length

Most tasks are straightforward on these dimensions, but analysts should still watch for rare issues.

### Instruction Following

The response must:

- include the key points requested by the user;
- stay relevant to the instruction;
- use the expected format, such as a list, bullet points, email, or title.

### Markdown Format

The output is Markdown:

- bold text should appear as `**text**`;
- a header/title should appear as `# text`.

### Tone

Tone must fit the audience and context. Most tasks are semi-formal, but some are more casual or more formal. Do not judge only naturalness; judge situational appropriateness.

### Completeness

Completeness depends on critical details required by the user or supplied in context:

- If the user provided a date, time, location, name, or event and the response omits it, that may fail Completeness.
- If the detail was never provided or required, do not penalize the response for not including it.

### Length

Length should match the task:

- Do not penalize a response for being long when the instruction requires substantial content.
- If the user asks for something simple, short, or concise but the response adds unnecessary detail, downgrade it.

---

## 6. Helpful Suggestions

Suggestions are meant to supplement the composition, not to be automatically treated as helpful.

Mark **Helpful** when the suggestion:

- provides useful ideas for the composition;
- adds helpful missing context such as time, date, place, or topic;
- makes the response more complete or actionable.

Mark **Neutral** when the suggestion:

- asks the user to perform unrelated device actions, such as setting reminders or calling someone;
- repeats information already provided;
- is related but generic or low-value.

Mark **Missing** when useful context suggestions, such as time/date/place, are clearly needed but absent.

Bottom line: **Not every suggestion is Helpful. It must meaningfully support the composition.**

---

## 7. Overall Rating

Use the tool’s suggested overall rating as a reference, but apply your own judgment based on task difficulty and usability.

Important reminders:

- Some instructions are simple and require only minimal composition input.
- A short or simple response can still be Excellent if it accurately, appropriately, and directly satisfies the task.
- Do not downgrade just because the response is not highly creative when the task does not call for creativity.

---

## 8. Quick Checklist

1. Critical additional information must be required to complete the task.
2. Correctly used Additional Personal Information is not hallucination.
3. Hallucination mainly involves unsupported specific facts: names, prices, numbers, dates, places, or company-specific details.
4. Evaluate email subjects criterion by criterion: Topic + action noun, Title Case, one topic, concision, and neutrality.
5. Instruction following includes both key content and required format.
6. Tone must fit audience and context.
7. Completeness only penalizes missing critical details that were provided or required.
8. Length should fit the task, not an arbitrary preference.
9. Suggestions are Helpful only when they genuinely supplement the composition.
10. Simple tasks can still receive Excellent if the response is accurate and ready to use.
