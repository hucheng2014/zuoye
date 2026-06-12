# Visual Quality — Complete Rules

## Purpose
Identify technical visual flaws unrelated to content or structure.

## What to Check
- Contrast (too low = flat; too high = blown highlights)
- Exposure (overexposure, underexposure, unreasonable lighting)
- Sharpness and blur
- Stretching, compression, proportion distortion
- Rotation, skew, abnormal cropping
- Rendering artifacts (noise, blockiness, broken edges, excessive smoothing)

## Diagnostic Questions
1. Extreme overexposure (blown-out whites) or underexposure (crushed blacks) not specified by prompt?
2. Whole image or major portions blurry — not intentional bokeh/DoF?
3. Image stretched or squashed? Objects unnaturally elongated/compressed?
4. Image rotated or skewed unnaturally (portrait on side, warped perspective)?
5. Other technical flaws (pixelation, color banding, compression artifacts)?

## Rating Options

| Select | When |
|--------|------|
| **Extreme contrast** | Blown-out whites or crushed blacks not requested |
| **Blurry** | Whole image or main subject out of focus (not bokeh) |
| **Stretched/squashed/cropped** | Unnatural elongation, compression, or cutoff |
| **Rotated/skewed** | Unnatural orientation or warped perspective |
| **Other** | Pixelation, color banding, compression artifacts (leave comment) |
| **None of the above** | No technical visual flaws |

## DO NOT Penalize (Intentional Effects)

| Effect | Status |
|--------|--------|
| Bokeh / depth of field | NOT a defect |
| High-contrast backlighting / silhouettes | NOT a defect if requested |
| Intentional artistic blur | NOT a defect if requested |
| Style-appropriate grain/texture | NOT a defect |

## Critical Decision Rules

| Situation | Rating |
|-----------|--------|
| Entire image blurry | Blurry |
| Main subject blurry, background clear | Blurry |
| Background blurry, subject sharp | NOT a defect (bokeh) |
| Main subject out of focus | Blurry (downgrade Visual Quality) |
| Face deformed | Structural Integrity (NOT Visual Quality) |
| Image cut off, subject incomplete | Stretched/squashed/cropped |
| Proportions wrong | Structural Integrity (NOT Visual Quality) |

## Blur-Specific Rules

- Mark blurry ONLY if **entire image** or **main subject/primary subject area** is blurry
- Background-only blur with sharp subject = NOT a defect
- If no single subject, overall scenic view should not be broadly unclear
- Face distortions → Structural Integrity, NOT Visual Quality
- Cat partially blurry (back part) → downgrade Visual Quality if it's a main subject

## Common Mistakes

| ❌ Wrong | ✅ Correct |
|----------|-----------|
| Bokeh marked as blurry | Bokeh = intentional, NOT a defect |
| Blurry marked when only background soft | Main subject sharp = NOT blurry |
| Face distortion in Visual Quality | Face distortion → Structural Integrity |
