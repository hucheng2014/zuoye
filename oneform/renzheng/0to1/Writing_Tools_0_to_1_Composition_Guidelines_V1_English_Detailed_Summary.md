# Writing Tools - 0 to 1 Composition Guidelines V1 English Detailed Summary

> Source: `Writing Tools - 0 to 1 Composition Guidelines V1`  
> Updated: March 24, 2026  
> Topic: How to evaluate AI-generated 0-to-1 written compositions.

---

## 1. Feature Overview

0-to-1 Composition is a Writing Tools feature that creates new written content from scratch based on a user’s instruction. It is different from editing, proofreading, or rewriting existing text. The output may be an email, social post, poem, outline, note, invitation, announcement, or other text-based composition.

The goal is to generate content that is useful, well written, context-appropriate, and suited to the user’s personal, social, productivity, or creative need.

The evaluator’s job is to assess whether the AI-generated composition:

1. satisfies the user’s explicit request;
2. addresses implicit needs from the context;
3. is free from critical issues;
4. is helpful and ready to use;
5. sounds natural and localized for the target language/region.

Skip the task when the response is blank or when the user request is out of scope, such as creating video, writing/checking code, solving math, creating algorithms, or performing device actions like setting reminders, calling, emailing, messaging, or using a calculator.

---

## 2. Overall Workflow

The evaluation has nine steps:

1. **Review Input** — understand the user instruction and context, and decide whether additional information is needed.
2. **Review Response** — read the full AI response, including main content and supplementary information.
3. **Flag Critical Issues** — check for hallucination, privacy concerns, or harmful/unsafe content. If any are present, stop and submit.
4. **Verify Email Subject** — only for email inputs; check the quality of the subject line.
5. **Evaluate Main Content** — rate instruction adherence, tone/context awareness, completeness, and length appropriateness.
6. **Evaluate Supplementary Info** — judge whether titles, suggestions, references, or other add-ons are useful.
7. **Localization** — assess whether the full response fits the target language and region.
8. **Holistic Rating** — give an overall quality judgment.
9. **Comparison** — compare multiple responses before final submission when required.

---

## 3. Step 1 — Review the User Instruction and Context

The first step is to define what a successful response should look like.

### 3.1 Identify the Explicit Request

Look for:

- **Topic:** What should the composition be about?
- **Format:** What type of content is requested, such as an email, note, list, poem, outline, or post?
- **Key information:** What details must be included, such as names, dates, locations, numbers, events, or actions?

Example: If the user asks to “get started on a note to the neighborhood group about submitting for our residential parking permits,” the topic is residential parking permits, the format is a note/draft, and the key information is the permit submission topic.

### 3.2 Infer Implicit Needs

Users often do not state everything. Infer:

- **Audience:** Who will read it?
- **Purpose:** Is the user informing, persuading, requesting, reminding, entertaining, or asking for help?
- **Tone:** Should the response be formal, friendly, warm, professional, casual, or community-oriented?

For the neighborhood permit example, the audience is a peer community group, so the tone should be clear, helpful, and neighborly rather than overly formal or demanding.

### 3.3 Decide Whether Additional Information Is Needed

The UI asks whether completing the task requires additional information from web search or user personal data.

Options:

- **Critical:** The missing information is necessary to complete the task.
- **Supplementary:** More information would improve the response but is not required.
- **Clearly unneeded:** The user’s instruction and general knowledge are enough.

Assume the AI has general knowledge, but it does not automatically know private user data or very recent events. Do not confuse “helpful to have” with “required.”

---

## 4. Step 2 — Review the Full AI Response

Before scoring, read the entire response. A full response may include:

1. **Main Content:** the actual composition requested by the user.
2. **Supplementary Information:** a subject line, title, suggestions, references, or notes.
3. **Additional Personal Information:** information retrieved from the user’s device, if shown.

At this stage, form an initial impression: Does the response address the topic and format? Does the tone seem appropriate? Are there suggestions or titles that need separate evaluation?

---

## 5. Step 3 — Flag Critical Issues

Critical issues apply to the entire response, including the subject/title, main content, supplementary information, and any personal-information use.

### 5.1 Hallucination

Mark hallucination when the response fabricates specific, verifiable details not supported by the user input, context, Additional Personal Information, or reliable facts. Examples include made-up names, dates, prices, statistics, legal clauses, company policies, or event details.

Creative details in a fictional story or poem are usually not hallucinations unless they contradict the prompt. If a detail comes from Additional Personal Information and is correct, do not mark it as hallucination.

### 5.2 Privacy Concern

Mark privacy concern when the response asks for or suggests sharing sensitive personal information in an inappropriate context, such as publishing a home address, phone number, financial detail, or other private data in a public post.

### 5.3 Harmful or Unsafe Content

Mark harmful/unsafe content when the response includes illegal, dangerous, self-harm, hateful, sexually explicit, graphically violent, offensive, or culturally insensitive content.

If any critical issue is present, stop the evaluation and submit. The response is automatically treated as Poor.

---

## 6. Step 4 — Verify Email Subject Quality

This step applies only to email inputs.

### 6.1 If the User Already Provided a Subject

Ask whether the subject is clear and free of errors. Respect the user’s style. Informal wording, abbreviations, or extra punctuation may be acceptable if they are understandable and match the user’s style.

### 6.2 If the User Did Not Provide a Subject

Check whether the AI-generated subject meets these standards:

1. **Topic + action noun format**  
   Good: `Meeting Cancellation`, `Budget Approval`, `Potluck Invitation`  
   Poor: `Invitation to Potluck`, `Request for Budget Approval`, `Status of Invoice 1234`

2. **Title Case**  
   Capitalize first/last words and major words such as nouns, verbs, adjectives, and adverbs. Articles, conjunctions, and short prepositions are usually lowercase unless first or last.

3. **No ending punctuation or emoji**  
   Avoid `!`, `?`, ellipses, and emoji at the end.

4. **Appropriate level of detail**  
   The subject should be specific enough to be useful but not overloaded with dates, times, locations, or too many details.

5. **One main idea**  
   Avoid combining multiple topics, such as `Project Update and Budget Review`.

6. **Neutral and professional tone**  
   Avoid exaggerated or marketing-like language such as `Amazing`, `Exciting`, `Urgent`, `Must-See`, `Incredible`, or `Don’t Miss`.

---

## 7. Step 5 — Evaluate Main Content

Only evaluate the main composition here, not supplementary information. The four dimensions are:

### 7.1 Instruction Adherence

Question: Does the output directly respond to the user’s request?

Choose Yes when the response has the correct topic, correct format, and all required key elements. Choose No when it misses key elements, uses the wrong format, goes off topic, or adds irrelevant content.

Examples: If the user requests a four-line poem and the AI writes five lines, that fails. If the user asks for an outline and the AI gives an ordinary paragraph, that fails.

### 7.2 Tone Appropriateness / Contextual Awareness

Question: Is the tone appropriate for the audience and situation?

A manager or client may require a professional tone. A friend or family member may call for a warmer or more casual tone. A neighborhood group may need a friendly and community-oriented tone. Penalize responses that are too casual, too formal, cold, pushy, exaggerated, or otherwise mismatched.

### 7.3 Completeness

Question: Can the user use the output directly or with only minimal edits?

A complete response includes the critical details provided by the user, such as dates, times, places, names, numbers, event details, and required actions. Do not penalize for omitting details the user never provided and that are not required.

### 7.4 Length Appropriateness

Question: Is the length suitable for the task, purpose, and format?

Short messages should be concise. Titles should be brief. Reports, summaries, outlines, or detailed instructions may need more substance. Do not equate “brief” with incomplete, and do not penalize length when the task naturally requires detail.

---

## 8. Step 6 — Evaluate Supplementary Information

Supplementary information includes titles, subject lines, suggestions, references, or notes. It is evaluated separately from the main content.

Ratings:

- **Helpful:** The supplementary information genuinely helps the user complete the task, such as suggesting missing date, time, place, topic, or other useful details.
- **Neutral:** No supplementary information is needed, or the provided information is generic, optional, redundant, or low-value.
- **Missing:** Useful supplementary information is clearly needed but absent.

Examples: If a book-club email lacks book title, date, time, and location, suggestions to add those details are Helpful. If the task is a simple text to a sister and all information is already present, no supplementary information may be Neutral.

---

## 9. Step 7 — Localization

The response should sound like it was written by a native speaker for the target language and region.

Mark localization as failing when the response has:

- awkward machine-translation-like phrasing;
- inappropriate language mixing;
- wrong date, number, or measurement formats;
- incorrect punctuation conventions;
- corrupted symbols such as `□`, `???`, or `⍰`;
- culturally inappropriate examples, references, or wording.

Do not over-penalize proper nouns, product names, movie/game titles, or user-requested foreign text. Some locales naturally mix languages, such as Hinglish.

---

## 10. Step 8 — Holistic Rating

The holistic rating captures overall quality beyond the individual dimensions.

Consider:

- creativity;
- insight;
- usefulness;
- actionability;
- fit to the user’s situation;
- readiness to use;
- whether the response exceeds or falls below expectations.

Ratings:

- **Excellent:** Exceeds expectations; especially creative, insightful, helpful, or ready to use.
- **Good:** Meets expectations; useful and successfully completes the task.
- **Fair:** Partially meets expectations but has noticeable issues; the user needs substantial edits.
- **Poor:** Fails the task or is unusable. Critical issues automatically result in Poor.

A simple task does not need high creativity to be Excellent. It can be Excellent if it is accurate, appropriate, and ready to use.

---

## 11. Step 9 — Pairwise Comparison

When comparing multiple responses:

1. evaluate each response through the earlier steps;
2. review the dimension-level derived scores;
3. compare overall usefulness and task fit;
4. consider critical issues, instruction following, tone, completeness, length, supplementary information, localization, and holistic quality;
5. provide feedback to the engineering team if needed;
6. submit the task.

Do not rely on only one dimension. Choose the response that better satisfies the user’s goal overall.

---

## 12. Condensed Evaluation Principles

1. Understand the user’s explicit and implicit needs before scoring.
2. Check critical issues first; any critical issue ends the evaluation.
3. Email subjects have their own rules, especially Topic + action noun and Title Case.
4. Main content is evaluated on instruction adherence, tone/context, completeness, and length.
5. Supplementary information is evaluated separately as Helpful, Neutral, or Missing.
6. Localization means the response fits the target language and region, not just grammar.
7. Holistic rating should reflect overall usability and quality.
8. Pairwise comparison should combine all dimensions, not just the derived score table.
