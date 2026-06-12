# Input/Output Alignment — Complete Rules

## Purpose
Assess how well the generated image matches the content described in the prompt.

## What to Check
Decompose prompt into elements, then verify each in the image:

| Element Type | Examples |
|-------------|----------|
| Objects | People, animals, items, locations, entities |
| Attributes | Color, material, shape, quantity, age, pose, clothing |
| Actions | What subjects are doing |
| Spatial relationships | Beside, above, below, facing, holding, interacting with |
| Mood/atmosphere | Calm, horror, joy, epic, mysterious |
| Style requirements | (handled in Style Alignment) |
| Text requirements | (handled in Text Quality) |

## Four-Step Process
1. Identify ALL key elements in prompt
2. Compare each element against the image
3. Note missing elements and major unrequested extra elements
4. Choose rating based on standard

## Rating Scale

| Rating | Criteria | Examples |
|--------|----------|----------|
| **Yes** | All key elements present, accurate, correct relationships, no major unrequested elements | Every object, attribute, action, mood matches |
| **Captures most but not all** | Most elements present, minor omissions or deviations | Missing one non-central element; relationship not fully expressed |
| **No — major misalignment** | Main subject wrong/missing; multiple key elements absent; wrong relationships | "Dumbbells" shows different object entirely; key scene element missing |

## Decision Rules by Missing Element Type

### Missing ONE Non-Central Element
→ **Captures most but not all**

Examples:
- Prompt: "Vector illustration of two people throwing bagels to seagulls on a ferry"
- Image: Ferry, people, seagulls present, but no throwing action visible
- Rating: Captures most but not all

### Missing Relationship/Positioning
→ **Captures most but not all**

Examples:
- Prompt: "A wilted flower bends towards a cracked window during a storm"
- Image: Flower, cracked window, storm all present, but flower not bending toward window
- Rating: Captures most but not all

### Primary Object Wrong or Missing
→ **No — Not aligned**

Examples:
- Prompt: "Rusty dumbbells"
- Image: Shows rusty object but NOT dumbbells (different object entirely)
- Rating: Not aligned

- Prompt: "Golden episcopal rings"
- Image: Shows wedding rings (wrong type)
- Rating: Not aligned

### Attribute Missing But Main Object Present
→ **Captures most but not all**

Example:
- Prompt: "Rusty dumbbells"
- Image: Shows regular dumbbells (not rusty)
- Rating: Captures most but not all (main object correct, attribute missing)

### Scene/Setting Partially Matches
→ **Captures most but not all**

Example:
- Prompt: "Scene in a gym"
- Image: Setting doesn't clearly read as gym
- Rating: Downgrade accordingly

## Extra Element Rule

| Extra Element Type | Effect on Rating |
|-------------------|------------------|
| Small, minor, unobtrusive | No impact |
| Major, occupies important space, unreasonable | Lower alignment |

## What NOT to Evaluate Here

| Issue | Correct Dimension |
|-------|------------------|
| Text spelling/quality | Text Quality |
| Structural defects | Structural Integrity |
| Style mismatch | Style Alignment |
| Blur/visual quality | Visual Quality |

## Common Mistakes

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| Image looks good overall → "Yes" | Missing element → downgrade |
| Structural issues penalized here | Structural → Structural Integrity only |
| Text errors counted here | Text → Text Quality only |
| Style wrong counted here | Style → Style Alignment only |
