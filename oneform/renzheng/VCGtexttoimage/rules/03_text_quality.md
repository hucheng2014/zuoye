# Text Quality — Complete Rules

## Two Sub-Dimensions
1. **Text Accuracy** — applies to ALL visible text
2. **Text Alignment** — applies ONLY to prompt-requested text

## Step 1: Is Text Present or Requested?

| Situation | Action |
|-----------|--------|
| Text visible in image OR prompt requested text | Evaluate both Accuracy and Alignment |
| No text in image AND prompt did not request text | Skip (mark N/A or "No") |

## Text Accuracy (ALL visible text)

### What Counts as Text
- Words, letters, numbers that form readable content
- Text on signs, labels, clothing, products, papers, screens

### What Does NOT Count as Text
- Random symbols on products (e.g., squiggles, pseudo-characters)
- Scribble without discernible letters
- Background text too small/distant/obstructed to read naturally

### Accuracy Ratings

| Rating | Criteria |
|--------|----------|
| **High** | Correct spelling; proper capitalization; clear, stable, unbroken characters |
| **Moderate** | Minor spelling or capitalization issues; slightly soft but still readable; some borderline unclear text |
| **Low** | Major spelling errors; severely distorted/broken/incomplete characters; meaningless text; unreadable text |
| **Can't Tell** | Text was requested but not present in image |

### Text Types

| Type | Definition | Evaluated? |
|------|-----------|-----------|
| Primary Text | Explicitly requested by prompt | Yes — Accuracy + Alignment |
| Additional Text | Not requested but clearly visible | Yes — Accuracy only |
| Background Text | Distant/small/obstructed, not expected to be readable | No — do not penalize |

## Text Alignment (ONLY prompt-requested text)

### What to Check
- Placement: correct location/object (on the sign, shirt, card)?
- Formatting: font style, size, color, direction, centering?
- Integration: naturally integrated into scene?

### Alignment Ratings

| Rating | Criteria |
|--------|----------|
| **Highly Aligned** | Correct placement, formatting, style, naturally integrated; all constraints met |
| **Moderately Aligned** | Some requirements met; minor placement/style issues; intent recognizable |
| **Not Aligned** | Text missing; wrong location/object; completely wrong style; floating overlay; most constraints not met |
| **N/A** | Prompt did not request text |

### Multi-Constraint Rule
If prompt specifies position, font, color, direction, size → image must meet **major constraints** for "Highly Aligned". Only some met → "Moderately Aligned".

## Critical Decision Rules

| Situation | Rating |
|-----------|--------|
| "SIILENCE" (misspelled) | Low Accuracy (not moderate) |
| Text readable but spelling wrong | Low or Moderate Accuracy |
| Spelling correct, capitalization wrong | Moderate Accuracy |
| Text requested but not in image | Can't Tell + Alignment issue |
| Text on wrong object | Not Aligned |
| Random symbols, not letters | NOT text — do not evaluate |
| Scribble without letters | NOT text — do not evaluate |
| Background text too small to read | Do NOT penalize |

## Key Distinction from Other Dimensions

| Issue | Correct Dimension |
|-------|------------------|
| Spelling error | Text Quality (Accuracy) |
| Text in wrong location | Text Quality (Alignment) |
| Text broken/distorted letters | Text Quality (Accuracy) |
| Text not requested but appears | Text Quality (Accuracy only) |
| Text style wrong | Text Quality (Alignment) |

**Note:** In Base Creation, Text Quality is INDEPENDENT. Do NOT evaluate text under Structural Integrity.
