# TRYRATING_GUIDE.md
# TryRating Broad Match — Full Decision Guide (Enhanced)

## Goal
Compare advertiser keyword intent with expansion/query intent and rate exactly one of:
- Good
- Acceptable
- Bad

Choose the closest category and write a concise comment explaining the match or mismatch.

## Core Principle
Judge intent, not just:
- shared words
- app category
- brand owner
- broad genre
- same category

## Decision Order
1. Normalize spelling, spacing, pluralization, word order, abbreviations, old app names, transliterations, and translations.
2. If both sides preserve the same specific intent after normalization, rate Good.
3. If they look different but share a meaningful app intent through competition, same functionality, or brand-feature/generic-function relationship, rate Acceptable.
4. If intent or function differs, even within the same broad genre, same brand family, shared word, or same category, rate Bad.
5. Be careful with directionality:
   - broad-to-specific can be acceptable only when the broad term clearly covers the specific app's central functionality.
   - specific-to-broader often loses intent.

## Research Workflow
Use the minimum research needed to resolve intent.

### Use App Store research for:
- branded app terms
- app ecosystem intent
- old app names
- app-specific product comparisons

### Use web search for:
- non-branded terms
- foreign-language terms
- annual events
- features
- ambiguous phrases

### Research rules
- Ignore ads in search results.
- Compare organic App Store/web results and app descriptions.
- If a term is not in the market language, translate it and mention the translation in the comment.
- Use research to resolve intent, not to justify a guess.
- When keyword or expansion seems functional (not navigational), App Store results may not fully reflect possible intent.

## Categories

### 1. Good
Use Good when the keyword and expansion look similar and preserve the same specific intent (normalized equivalent terms).

Good categories:
- spelling correction
- spacing differences
- reordering
- transliteration
- singular/plural
- abbreviation
- same meaning with added or removed words
- former app name
- translation

Examples:
- tiktok vs tik tok
- instagram vs ig
- utube vs youtube
- racing game vs racing games
- Douyin vs 抖音
- Twitter vs X

Comment template:
- Rated Good - <category>. Both terms preserve the same intent for <intent>.

### 2. Acceptable
Use Acceptable when terms look different but share a relevant app intent or functionality (not just same category).

Acceptable categories:
- direct competitors
- brand terms (not directly competing) offering same functionality or features
- brand term offering same functionality as non-brand term or vice versa
- non-brand terms with different wording but same/similar intent

Examples:
- LinkedIn vs Indeed
- Disney vs Hulu
- UNO vs Monopoly
- multiplayer vs Fortnite
- scanner pro vs scanner app
- plant identifier vs flower identifier
- fitness vs workout

Directional example:
- learning games for kids to toddler games can be acceptable because kids clearly covers toddlers.
- reverse direction may be Bad if the specific term becomes broader than the target intent.

Comment template:
- Rated Acceptable - <category>. Both terms share the intent of <shared intent>.

### 3. Bad
Use Bad when keyword and expansion do not share the same intent or functionality (same category is not enough).

Bad cases include:
- unrelated brands
- same brand with different product intent
- same broad genre but different user goal
- generic app/download/free terms expanded to a specific app
- specific-to-broad mismatches
- same category but different function

Examples:
- Adidas vs ESPN
- video editor vs collage maker
- Google Maps vs Google Translator
- Amazon Fresh grocery vs Amazon Alexa
- shooting games vs toddler games
- App vs Netflix
- Free apps for iPhone vs Instagram
- Download app vs Snapchat

Comment template:
- Rated Bad - <category>. Keyword intent is <keyword intent>, expansion intent is <expansion intent>; they do not share the same user goal.

## Intent Classification Checklist
Before rating, identify whether each side is:
- branded
- non-branded
- functional
- navigational
- a feature
- a product
- a foreign-language term

Then ask:
- Are these the same intent after normalization?
- Do they solve the same user problem?
- Is one term a broad umbrella that clearly includes the other?
- Does the expansion change the user goal?
- Is this just a brand/category overlap without shared intent?

## Translation Rule
If a term is not in the market language:
- translate it
- mention the translation in the comment
- rate based on intent after translation

Template:
- Used translation: <term> means <meaning>. Both terms <share/do not share> the intent of <intent>.

## Comment Rules
- Keep comments short (1-2 sentences).
- Stay factual.
- Tie the comment to the selected category.
- Mention research only when it materially supports the decision.
- Do not write uncertainty in the final answer.
- Do not write a long explanation.
- Do not reuse the same generic comment across different questions.
- Do not use vague comments like “Both terms share related app intents.”

## Common Pitfalls
- Same brand does not mean same intent.
- Same app category does not mean same intent.
- Shared generic words do not imply a match.
- Broad term to specific term is not automatically Good.
- Specific term to broader term often becomes Bad.
- Do not overrate based on surface similarity.
- Same broad genre but different user goals is Bad.
- Same category but different function is Bad.
- “Related” is not enough for Acceptable; there must be a real shared app intent or functionality.

## Practical Decision Path
1. Normalize both terms.
2. Identify the user goal on each side.
3. Compare goal, not wording.
4. Check whether one side clearly covers the other.
5. If same goal and similar-looking, Good.
6. If related but different yet still sharing meaningful app functionality, Acceptable.
7. If different goal, Bad.

## Final Check
Before submitting:
- exactly one rating chosen
- comment matches the rating
- comment matches the selected category/reason
- comment is concise
- intent is the basis of the decision
- no unnecessary filler
- no generic copy-paste wording
