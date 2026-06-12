# Example: No Poll Appropriate + Empty Response (Correct Behavior)

## Conversation

```
Alice: Hey, does anyone know a good Italian restaurant near downtown?
Bob: I really like Salenas on 5th street, their pasta is amazing.
Carol: Oh yeah, I've been there! Also try Dogtown Bistro, they have great wood-fired pizza.
Alice: Thanks guys, I'll check both out this weekend!
```

## Model Response
(empty)

## Analysis

### Why No Poll is Appropriate
- Alice is **seeking personal recommendations**, not organizing a group dinner
- Bob and Carol are providing **advice/suggestions** to help Alice individually
- There is **no collective decision** -- Alice will choose on her own
- Nobody is trying to organize "let's all go to dinner together"
- This is a recommendation request, not a group consensus scenario

### Correct Scoring

```json
{
  "proper_no_reply": "no_reply",
  "observation": "No poll is appropriate. Alice is asking for restaurant recommendations for her personal use, not organizing a group activity. The empty response correctly abstains from generating an unnecessary poll."
}
```

### Key Points
1. Only `proper_no_reply` and `observation` are filled
2. No other dimensions are evaluated (they would not appear in the form)
3. The empty response is **not penalized** -- it is the correct behavior
4. Do NOT mark this as low quality or unsatisfying
5. Common mistake: seeing multiple restaurant names and thinking a poll is needed. The critical question is whether there's a **collective decision** to make, not whether options exist.
