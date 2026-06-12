# Composition

## Purpose
Evaluate the writing quality of the poll title and options.

## Options
- `good` — Well-written title and options
- `bad` — Poorly written title or options

## Good Composition Standards

### Title Requirements
- Must be a **natural phrase**, NOT a full question or complete sentence
- Good: `Food Choice`, `Movie Night`, `Team Outing Location`
- Good (from options): `Comedy Show or Movie` (short, natural, accurate)
- Bad: `Which Type of Food Should We Order?` (question)
- Bad: `Movie Should We Watch Tonight` (awkward phrasing)

### Option Requirements
- Concise and clear, no extra explanations attached
- Free of grammar and spelling errors
- Semantically consistent with each other (same category/type)
- Each option is a standalone choice

### Typo Handling
If conversation contains typos with clear intended meaning, the poll SHOULD correct them:
- Conversation: "fight to Italy" (obviously "flight") -> Option should be "Flight to Italy"
- Not correcting inferable typos = Bad Composition

## Bad Composition — Common Causes

### Title Problems
- Title written as a full question with question mark
- Title is an awkward/unnatural sentence fragment
- Title misrepresents the conversation topic

### Option Problems
- Options too long (copying full sentences from conversation)
- Options semantically incomplete or containing irrelevant explanations
- Example of bad option: `the equalizer denzel washington is awesome` (opinion mixed into option)
- Options merged unnaturally: `Pizza and Burgers` as a single option when they should be separate

### Merged Options Pattern
When two distinct options are merged into one (e.g., "Pizza and Burgers" as one option with an empty second option slot):
- This is a **Composition** problem (unnatural presentation)
- Does NOT automatically fail Following Instructions (structure exists)
- Does NOT fail Groundedness (content came from conversation)
- May affect Comprehensiveness (options not presented independently)

## Format/Punctuation Flexibility
Do NOT penalize for formatting differences. The poll does not need to follow any specific `Title: / Options: -` template. What matters is the QUALITY of the title and options, not the visual layout. If title and options are clearly identifiable, format variations are acceptable.
