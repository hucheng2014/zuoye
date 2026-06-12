# Style Alignment — Complete Rules

## Default Rule
If target style is empty AND user did not request a style → **Default = Photorealism**

## Priority Rule
**User prompt style request OVERRIDES task target style.**

## Two Style Categories

### A. Photorealism
**Question:** Does the image look like it was captured by a real camera?

| Rating | Criteria |
|--------|----------|
| **Very realistic** | Almost indistinguishable from real photo; realistic texture, lighting, shadow, material, perspective |
| **Somewhat realistic** | Has photographic qualities but visible AI/non-photo signs; overly smooth surfaces |
| **Not realistic** | Clearly artificial, rendered, illustrated, game-like, painted, synthetic |

**Photorealism Cues (objective evidence):**
- Texture detail (skin, fabric, materials)
- Lighting and shadow behavior
- Material surfaces
- Perspective accuracy
- Depth of field consistency
- Color tone and surface detail

**NOT evidence:** personal feeling, "looks good"

### B. Non-Photorealistic Styles
**Question:** Does the image consistently embody the target style's visual characteristics?

| Rating | Criteria |
|--------|----------|
| **Matches Perfectly** | Target style fully and consistently represented; no obvious style mixing |
| **Partially Matches** | Some style features present but uneven, incomplete, or localized |
| **Does Not Match** | Barely represents target style; completely different/unrelated style |

**If not full match, select issue:**
- Blurry (style unreadable)
- Wrong style
- Inconsistently applied
- Other (comment required)

## Key Style Definitions

### Genmoji / Emoji
- Rounded, warm, expressive, readable at small size
- Background MUST be pure white or fully transparent
- NO color casts, gradients, shadows, lighting in background
- Container (if used) follows emoji conventions (rounded-square)
- Characters soft and rounded, NOT photorealistic or complex illustration
- **NOT:** ordinary illustration, Chibi, generic 3D art

### Low Poly
- MUST show clear triangular or quadrilateral facets
- Low-poly geometry, segmented shading
- Simplified ≠ Low Poly (must have actual polygon structure)

### Illustration
- Clear linework, flat color fills
- Simplified detail, bold lines
- Background simple and abstract
- NOT photorealistic

### Sketch
- Hand-drawn look, colored-pencil strokes
- Natural unfinished edges
- Paper feel, slight line wobble, pressure variation

### Animation
- Warm, dimensional, story-driven
- Rounded characters with 3D depth
- Warm, vibrant, cinematic colors
- Background and subject share style

## DO NOT Penalize Here

| Issue | Correct Dimension |
|-------|------------------|
| Structural defects | Structural Integrity |
| Missing prompt elements | Alignment |
| Text errors | Text Quality |
| Blur (unless style unreadable) | Visual Quality |

## Common Mistakes

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| Smooth AI look = Very realistic | Smooth surfaces = Somewhat/Not realistic |
| Illustration accepted as Genmoji | Different style → Does Not Match |
| Personal impression = photorealism | Must use OBJECTIVE visual cues |
| Structural issues penalized here | Structural → Structural Integrity only |
