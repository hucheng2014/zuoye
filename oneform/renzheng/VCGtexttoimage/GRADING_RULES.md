# VCG Base Creation — Grading Decision Handbook

> Compact reference for automated grading. Covers all 6 dimensions + SBS comparison + flags.

---

## SCAN ORDER (mandatory sequence)

1. Structural Integrity → 2. Visual Quality → 3. Text Quality → 4. Input/Output Alignment → 5. Style Alignment → 6. Diversity → 7. Flags

---

## 1. STRUCTURAL INTEGRITY

**What to check:** anatomy, hands, fingers, face, eyes, limbs, object structure, merged/floating/disconnected parts, unintended artifacts.

**For stylized art:** only penalize when structure breaks the style's internal logic, NOT real-world realism. A three-headed dog is correct if the prompt requested it.

### Severity Scale:

| Rating | Definition | Examples |
|--------|-----------|----------|
| **Severe** | Immediately apparent; breaks basic form | Distorted face, extra/missing fingers, merged humans/animals, missing limbs, unrecognizable subject, melted hands, duplicated facial features |
| **Noticeable** | Visible without zooming; breaks flow but image remains interpretable | Twisted fingers, eye asymmetry, floating objects, two steering wheels, unrealistic object positioning, facial feature issues (eyes/nose/mouth/ears — even if subtle, NOW upgraded to Noticeable) |
| **Minor** | Only found on close inspection | Slight proportion issues, minor background distortions, small decorative element flaws, vase handle slightly detached |
| **No issues** | No structural defects found | — |

### Critical Rules:
- Incorrect finger count → **always Severe**
- Face/eye/nose/mouth/ear issues → **at minimum Noticeable** (upgraded from Minor per latest criteria)
- Multiple defects → rate by the **highest severity** present
- Main subject defects are rated more harshly than background defects

---

## 2. VISUAL QUALITY

**What to check:** exposure, blur, stretch/squash, rotation/skew, pixelation, compression artifacts.

### Decision:

| Issue | Select |
|-------|--------|
| Blown-out whites / crushed blacks (not prompt-requested) | Extreme contrast |
| Whole image or main subject blurry (not bokeh/DoF) | Blurry |
| Unnaturally elongated/compressed objects | Stretched/squashed/cropped |
| Unnatural rotation or warped perspective | Rotated/skewed |
| Severe pixelation, color banding, artifacts | Other (comment) |
| None of the above | None of the above |

### DO NOT penalize:
- Intentional bokeh / depth-of-field
- High-contrast backlighting / silhouettes requested by prompt
- Intentional artistic blur

### Blur rule:
- Mark blurry ONLY if the **entire image** or **main subject** is blurry
- Background-only blur with sharp subject = NOT a defect
- Face distortion = Structural Integrity, NOT Visual Quality

---

## 3. TEXT QUALITY

**Two sub-dimensions:** Text Accuracy + Text Alignment

### Step 1: Is text present or requested?
- **Yes** → evaluate both accuracy and alignment
- **No** (no text in image AND prompt didn't request text) → skip

### Text Accuracy (applies to ALL visible text):

| Rating | Criteria |
|--------|----------|
| **High** | Correct spelling, proper capitalization, clear readable characters |
| **Moderate** | Minor spelling/capitalization issues; slightly soft but readable |
| **Low** | Major spelling errors, severely distorted/broken/unreadable characters, meaningless text |
| **Can't Tell** | Text was requested but not present in image |

### Text Alignment (applies ONLY to prompt-requested text):

| Rating | Criteria |
|--------|----------|
| **Highly Aligned** | Correct placement, formatting, style, naturally integrated |
| **Moderately Aligned** | Some requirements met, minor placement/style issues |
| **Not Aligned** | Text missing, wrong location, wrong object, completely wrong style |
| **N/A** | Prompt did not request text |

### Critical Rules:
- Random symbols on products ≠ text
- Scribble without discernible letters ≠ text
- Background text too small/distant to read → do NOT penalize
- "SIILENCE" type errors → Low accuracy (not moderate)
- Text Quality is INDEPENDENT from Structural Integrity in Base Creation

---

## 4. INPUT/OUTPUT ALIGNMENT

**What to check:** all prompt elements — objects, attributes, actions, spatial relationships, mood/atmosphere, quantities.

### Rating Scale:

| Rating | Criteria |
|--------|----------|
| **Yes** | All key elements present, accurate, correct relationships, no major unrequested elements |
| **Captures most but not all** | Most elements present, minor omissions or deviations |
| **No — major misalignment** | Main subject wrong/missing, multiple key elements absent, wrong spatial relationships |

### Decision Rules:
- Missing ONE non-central element → "Captures most but not all"
- Primary object entirely absent or wrong → "No / Not aligned"
- Missing relationship (e.g., "bends toward window" not shown) → "Captures most but not all"
- Attribute missing but main object correct (e.g., dumbbells present but not rusty) → "Captures most but not all"
- Main object replaced by entirely different object → "Not aligned"

### DO NOT evaluate here:
- Text quality (separate dimension)
- Style match (separate dimension)
- Structural defects (separate dimension)

---

## 5. STYLE ALIGNMENT

**Default style:** If target style is empty AND user didn't request a style → default = **Photorealism**

**User prompt style overrides task target style.**

### For Photorealism:

| Rating | Criteria |
|--------|----------|
| **Very realistic** | Looks like a real camera photo — realistic texture, lighting, shadow, material, perspective |
| **Somewhat realistic** | Has photographic qualities but visible AI/non-photo signs; overly smooth surfaces |
| **Not realistic** | Clearly artificial, rendered, illustrated, game-like, painted |

**Photorealism cues:** texture detail, lighting/shadow behavior, material surfaces, perspective, depth of field, color tone. Do NOT judge by "feeling" — use objective visual evidence.

### For Non-Photorealistic Styles:

| Rating | Criteria |
|--------|----------|
| **Matches Perfectly** | Target style fully and consistently represented |
| **Partially Matches** | Some style features present but uneven/incomplete |
| **Does Not Match** | Completely different or unrelated style |

If not full match, select issue: Blurry (style unreadable) | Wrong style | Inconsistently applied | Other

### Key Style Rules:
- **Genmoji/Emoji:** Rounded, warm, expressive, readable at small size. Background MUST be pure white/transparent. NOT illustration, NOT Chibi, NOT 3D art.
- **Low Poly:** Must show clear triangular/quadrilateral facets. Simplified ≠ Low Poly.
- **Illustration:** Clear linework, flat color fills, simplified detail, bold lines. NOT photorealistic.
- **Sketch:** Hand-drawn look, colored-pencil strokes, natural unfinished edges, paper feel.
- **Animation:** Warm, dimensional, story-driven, rounded characters with 3D depth.

### DO NOT penalize here:
- Structural integrity issues
- Prompt content mismatches
- Text errors

---

## 6. DIVERSITY

**Only evaluate if people are visible. Base answers ONLY on visible appearance.**

### People Count:
None | 1 | 2–3 | More than 3

Count: adults, children, partial bodies, people in reflections.
Do NOT count: mannequins, statues, dolls, robots, unclear shapes.

### Apparent Ethnicity (only if 2+ people):
- All White/European
- All same non-White group
- Visible mixture
- Can't be judged

### Apparent Gender (only if 2+ people):
- All male-presenting
- All female-presenting
- Visible mixture
- Can't be determined

### Critical Rule:
If even ONE person's face cannot be reliably assessed → select "Can't be judged/determined" for the whole group.

Do NOT label specific ethnicities. Do NOT guess identity.

---

## 7. FLAGS

| Flag | When to use |
|------|-------------|
| **Did Not Load** | Image blank, broken, cannot display. NOT for blurry/low-quality images |
| **Safety flags** | Violence, sexual content, offensive cultural representation, harmful stereotypes |
| **Trademark** | Recognizable logos, brand names, watermarks, artist signatures |

Do NOT flag neutral content without justification.

---

## 8. SBS (SIDE-BY-SIDE) COMPARISON

### Overall Quality:
Based on dimension scores already assigned. Choose the image with **fewer errors**, NOT the prettier one.

**Checklist:**
1. Which misses fewer prompt elements?
2. Which has fewer structural issues?
3. Which has better visual quality?
4. Which matches style better?
5. Are PR scores consistent with dimension-level assessments?

### Aesthetic Quality:
Based on visual appeal — composition, lighting, color, clarity, polish. Separate from technical correctness.

### Scale:
- **Better** — Clear, significant difference
- **Slightly Better** — Moderate but meaningful difference
- **Same** — No meaningful difference

---

## COMMON MISTAKES TO AVOID

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| Extra fingers → Minor | Extra fingers → **Severe** |
| Eye/face issues → Minor | Eye/face issues → **Noticeable** (minimum) |
| Missing elements but image looks good → Yes | Missing elements → **Captures most / Not aligned** |
| Smooth AI look → Very realistic | Smooth AI look → **Somewhat / Not realistic** |
| Prettier image wins comparison | Image with **fewer errors** wins |
| Text tag marked when no text requested | Mark **N/A** when no text requested |
| Bokeh penalized as blur | Bokeh = intentional, **not a defect** |
| Illustration accepted as Genmoji | Different styles → **Does Not Match** |
| Personal impression = photorealism | Must use **objective visual cues** |
