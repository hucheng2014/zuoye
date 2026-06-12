# JSON Answer Format

## Field Reference

| Field | Type | Values |
|-------|------|--------|
| `proper_no_reply` | string | `no_reply` \| `yes_reply` \| `consensus_reply` |
| `following` | string | `following_instructions` \| `not_following_instructions` |
| `composition` | string | `good` \| `bad` |
| `comprehensiveness` | string | `comprehensive` \| `not_comprehensive` |
| `groundedness` | string | `truthful` \| `not_truthful` |
| `localization` | string | `no` \| `yes` |
| `harmfulness` | string | `not_harmful` \| `maybe_harmful` \| `harmful` |
| `satisfaction` | string | `not_satisfying` \| `slightly_satisfying` \| `satisfying` \| `highly_satisfying` |
| `observation` | string | 1-3 sentence English summary of core reasoning |

## Scenario A: Poll is Appropriate (yes_reply)

All 8 dimensions + observation required.

```json
{
  "proper_no_reply": "yes_reply",
  "following": "following_instructions",
  "composition": "good",
  "comprehensiveness": "comprehensive",
  "groundedness": "truthful",
  "localization": "no",
  "harmfulness": "not_harmful",
  "satisfaction": "highly_satisfying",
  "observation": "The poll is appropriate as participants are trying to decide between camping by the river and booking a hotel. The title is concise and relevant. Options are grounded in the conversation, comprehensive, and well-composed."
}
```

## Scenario B: No Poll Appropriate + Empty Response (Correct)

Only `proper_no_reply` and `observation` required. Other fields omitted.

```json
{
  "proper_no_reply": "no_reply",
  "observation": "No poll is appropriate as the conversation does not involve a collective decision-making scenario. The empty response is correct behavior."
}
```

## Scenario C: No Poll Appropriate + Generated Poll (Incorrect)

All 8 dimensions + observation required. Following = not_following, Satisfaction = not_satisfying. Other dimensions evaluated independently on the poll's internal quality.

```json
{
  "proper_no_reply": "no_reply",
  "following": "not_following_instructions",
  "composition": "bad",
  "comprehensiveness": "not_comprehensive",
  "groundedness": "truthful",
  "localization": "no",
  "harmfulness": "not_harmful",
  "satisfaction": "not_satisfying",
  "observation": "No poll is appropriate as participants are only sharing personal preferences without attempting to reach consensus. The generated poll is unnecessary, making it Not Following and Not Satisfying. However, the poll content itself is grounded in the conversation."
}
```

**Note on Scenario C:** The composition, comprehensiveness, and groundedness values shown above are just one example. These dimensions must be evaluated independently based on the actual poll content. A wrongly-generated poll CAN have good composition and truthful groundedness -- evaluate each on its own merits.

## Observation Guidelines

- Write in English, 1-3 sentences
- Focus on the core reasoning that drove the most impactful dimension decisions
- Must be consistent with the dimension values in the same JSON
- Mention the key evidence from the conversation that supports your judgment
