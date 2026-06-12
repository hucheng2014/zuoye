# Search Ads Relevance -- Compact Scoring Rules

## Single Dimension: Relevance (4 Levels)

### Excellent
Strong relationship between query and advertised app. User most likely to be interested.
- Exact or near-exact name match
- Same developer
- Direct competitor to the searched app
- Core functionality match (query seeks X, app does X)

### Good
Some relation, user quite likely interested but other results more compelling.
- Close but not exact functionality (query: photo editor, app: collage maker)
- Accessory or add-on to the queried app
- Same ecosystem, narrower or wider scope

### Acceptable
Slight relation, user would not be surprised to see it but unlikely to be interested.
- Same broad category but different specific needs
- Same developer but different theme/purpose
- App not available in the user's locale

### Bad
No meaningful relation. User would be surprised to see this ad. **REQUIRES comment.**
- No logical link between query and app
- Surface-level word overlap but entirely different context
- Different domain, audience, and purpose

## Critical Rules

1. **Do NOT penalize** for low review scores, high prices, or poor app descriptions
2. **Unavailable in locale** -> cap at Acceptable (never Excellent/Good)
3. **Developer match** -> floor at Acceptable (never Bad)
4. **Direct competitors** -> Excellent
5. **Games**: evaluate on play style + theme + audience (not just "both are games")
6. **Context/locale matters**: research abbreviations, local brands, service codes
7. **All Bad ratings MUST have explanatory comments**
8. **Comment structure**: query intent -> app function -> relationship -> rating justification
9. **Pre-submission**: all 5 items rated, all commented, no mixing query/app across items
