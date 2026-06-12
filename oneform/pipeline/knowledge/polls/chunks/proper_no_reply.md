# Proper No Reply

## Purpose
Determine whether the conversation warrants generating a poll, BEFORE evaluating poll quality.

## Options
- `no_reply` — No poll is appropriate
- `yes_reply` — Poll is appropriate
- `consensus_reply` — Poll appropriate because participants are explicitly trying to reach consensus

## When a Poll IS Appropriate (yes_reply / consensus_reply)

A poll is appropriate when ALL of:
1. At least one participant wants to collect opinions about a **collective activity, event, or decision**
2. Participants express **different preferences** that need to be resolved
3. The group is trying to **reach consensus** on a shared choice

Examples:
- "Should we order food?" -> one says pizza, another says burgers -> **yes_reply** (collective decision with diverging preferences)
- Planning a group movie night with different film suggestions -> **yes_reply**
- "Where should we go for the team outing?" with multiple suggestions -> **consensus_reply**

## When a Poll is NOT Appropriate (no_reply)

### Shared Preference / Consensus Already Reached
- Everyone agrees on the same thing: "Let's all go to the beach" -> "Sounds great!" -> no decision to make
- Action already taken: "I already ordered both pizza and burgers" -> too late for a poll

### Seeking Advice, Not Organizing a Vote
- "What's a good restaurant near downtown?" -> requesting recommendations, not organizing a group decision
- "Which laptop do you recommend?" -> personal advice, not collective choice
- "Has anyone been to Boston? What should I see?" -> asking for travel tips

### Personal Preference Discussion Without Collective Goal
- People sharing which movies they like without planning to watch one together
- Discussing favorite foods without planning a group meal
- Expressing opinions on topics without needing a group decision

### Topic Not Suitable for Voting
- Complex personal decisions (career choices, relationship advice)
- Factual questions with definitive answers
- Emotional support conversations

## Empty Response Rule
If `no_reply` and response is empty -> this is CORRECT behavior. Only fill Proper No Reply, no other dimensions need evaluation. Do NOT penalize the empty response in any way.

## Non-Empty Response When No Poll Appropriate
If `no_reply` but a poll was generated -> still evaluate all other dimensions independently. But note: Following Instructions = not_following, Satisfaction = not_satisfying.
