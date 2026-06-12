# Dimension Independence Law

## The Most Critical Rule
**Each of the 8 dimensions MUST be judged independently.** Never let a failure in one dimension automatically cause a failure in another. This is the single most common scoring mistake.

## Prohibited Auto-Connections

### Hallucinated Options -> NOT auto-fail Following
- A poll has fabricated options that weren't in the conversation
- It still has a title + >=2 unique options -> **Following: pass**
- Fabrication is penalized ONLY in **Groundedness** (not_truthful)
- The FAQ explicitly states: "Do not establish 'option not grounded, therefore Not Following' automatic connections"

### Missing Options -> NOT auto-fail Following
- A poll omits some options mentioned in conversation
- It still has a title + >=2 unique options -> **Following: pass**
- Omission is penalized ONLY in **Comprehensiveness** (not_comprehensive)

### Bad Composition -> NOT auto-fail Following
- Title is a question instead of a phrase, options are too long
- But title exists and >=2 options exist -> **Following: pass**
- Quality issues belong in **Composition** (bad)

### Merged Options + Empty Slot -> NOT auto-fail Following
- "Pizza and Burgers" as one option with an empty second slot
- Structure: has title + has option set -> **Following: pass**
- Merger is a **Composition** problem (bad)
- May also be debatable under **Comprehensiveness**

### No Poll Appropriate + Generated Poll -> Special Handling
- Following: not_following (shouldn't have generated)
- Satisfaction: MUST be not_satisfying
- BUT: Composition, Comprehensiveness, Groundedness -> still evaluate independently based on the poll's internal quality
- Do NOT stop evaluating other dimensions just because Proper No Reply is wrong

## Correct Cross-Dimension Patterns

| Scenario | Following | Composition | Comprehensiveness | Groundedness |
|----------|-----------|-------------|-------------------|--------------|
| Good poll, all correct | following | good | comprehensive | truthful |
| Fabricated option added | following | good | comprehensive | not_truthful |
| Missing an option | following | good | not_comprehensive | truthful |
| Title is a question | following | bad | (independent) | (independent) |
| Merged options | following | bad | debatable | truthful |
| No poll needed + generated | not_following | (evaluate independently) | (evaluate independently) | (evaluate independently) |

## Practical Checklist
Before submitting, verify:
1. Did I judge each dimension using ONLY its own criteria?
2. Did I avoid "cascading" a failure from one dimension to another?
3. For Following, did I only check structure (title + >=2 unique options)?
4. Did I keep Groundedness and Comprehensiveness cleanly separated?
