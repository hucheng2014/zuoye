# Special Rules & Exceptions

## Rule 1: Do NOT Penalize for Reviews, Price, or Description Quality

The relevance rating measures the relationship between the query and the app's purpose. External quality signals are irrelevant.

- An app with 1-star reviews but perfect query match = still **Excellent**
- An expensive app that matches the query = still rate on relevance, not price
- An app with a poorly written description but clear functionality match = rate on functionality, not description quality
- An app with no screenshots or incomplete store listing = rate on what the app does, not how it is presented

**Rationale**: We rate ad relevance (does this app match what the user searched for?), not ad quality (is this a good app?).

## Rule 2: Unavailable in Locale -> Cap at Acceptable

If the advertised app is not available in the user's App Store region:

- Even if the app is a perfect match for the query, cap rating at **Acceptable**
- The user cannot download or use the app, so the ad has limited practical value
- If the app is partially available (e.g., free version available but premium locked), still cap at **Acceptable**

Examples:
- Query: "BBC iPlayer" in US market -> App: "BBC iPlayer" (UK only) = **Acceptable**
- Query: "Hulu" in European market -> App: "Hulu" (US/Japan only) = **Acceptable**

## Rule 3: Developer Match -> Floor at Acceptable

If the advertised app is from the same developer as the app in the query:

- The rating is at minimum **Acceptable**, never Bad
- Developer relationship establishes a baseline connection
- The user has demonstrated interest in this developer's ecosystem

Escalation:
- Same developer + same domain = **Excellent** (e.g., Google Maps -> Google Earth)
- Same developer + related domain = **Good** (e.g., Google Maps -> Google Calendar, travel planning overlap)
- Same developer + unrelated domain = **Acceptable** (e.g., Google Maps -> Google Translate, minimal functional overlap)

## Rule 4: Direct Competitors -> Excellent

If the advertised app directly competes with the searched app:

- Same core functionality
- Same target audience
- Same market category
- Rate **Excellent** regardless of market share or brand recognition

Examples:
- Uber vs Lyft = **Excellent** (both ride-hailing)
- Spotify vs Apple Music = **Excellent** (both music streaming)
- Notion vs Obsidian = **Excellent** (both note/knowledge management)
- DoorDash vs Uber Eats = **Excellent** (both food delivery)

## Rule 5: Context & Locale Knowledge

Always consider the locale and context before rating:

- Research unfamiliar abbreviations or brand names
- Consider what a term means in the user's specific market/country
- App Store content varies by region -- what is popular in one market may be unknown in another
- Local services, government apps, and regional brands require research
- Never assume a Western/English-centric interpretation when the query is from a different locale

See also: `chunks/locale_context.md` for detailed examples.
