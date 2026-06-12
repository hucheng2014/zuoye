# Groundedness

## Purpose
Evaluate whether every factual detail, date, time, number, location, and name in the draft can be verified from the task context (User Prompt, Previous Mail, Additional Personal Info, User Profile).

## 3-Level Scale

### Grounded (Fully Faithful)
All facts in the draft are verifiable from the task context. No invented details.

Special cases that are always Grounded:
- Daily professional pleasantries (e.g. "Have a nice day") = Grounded
- Names found in ANY task field = Grounded (see Name Grounding Rule below)

### Partially Grounded (Minor Invented Details)
The draft's core business logic is entirely correct, but it adds small, unverifiable details.

Case 1 -- Quantity fabrication:
- Prompt: "Yes, there are new projects"
- Draft: "Yes, there is 1 new project" (the "1" is invented)
- Verdict: **Partially Grounded** (core correct, but "1" has no basis)

Case 2 -- Progress fabrication:
- Context: parties still discussing intent
- Draft claims: "I am currently finishing a new series specifically for the personal exhibition"
- Verdict: **Partially Grounded** (fabricated progress detail)

Case 3 -- Intent assertion:
- Context: preliminary discussion about contract renewal
- Draft asserts: "We wish to renew the service agreement"
- Verdict: **Partially Grounded** (asserting intent beyond what context supports)

### Not Grounded (Severe Hallucination)
The draft introduces fabricated facts that fundamentally change the core meaning of the email, or invents interactions/events that never occurred.

Case 1 -- Fabricated reasons:
- Previous Mail: asking whether to renew a contract
- Draft: "Due to our schedule being fully booked with exhibitions, we cannot participate"
- Verdict: **Not Grounded** (fabricated specific reason that changes the decision rationale)

Case 2 -- Invented interactions:
- Draft: "Thank you for the clear guidance you gave me previously"
- Context: no such guidance was ever given
- Verdict: **Not Grounded** (fabricated prior interaction)

## Name Grounding Rule (ABSOLUTE)
**Names that appear in ANY field of the task are always Grounded.** This includes:
- User Prompt
- Previous Mail
- Additional Personal Info
- User Profile

Even if a name appears in one field but conflicts with another field, it is still Grounded in the Groundedness dimension. Name conflicts/errors must be evaluated in Instruction Adherence & Contextual Fit or Personalization, NEVER in Groundedness.

## Additional Info Rule (MANDATORY PRE-CHECK)
Before calling anything a hallucination, you MUST 100% check ALL content in the Additional Personal Info field. Many details that appear fabricated at first glance (specific dates, interview times, schedule details) are actually supported by data in this field.

Failure to check Additional Info is the #1 cause of false "Not Grounded" ratings.

## Independence Note
Groundedness is independent from other dimensions. A draft that is Not Grounded may still score well on Personalization, and vice versa. Do not let Groundedness findings contaminate other dimension scores.
