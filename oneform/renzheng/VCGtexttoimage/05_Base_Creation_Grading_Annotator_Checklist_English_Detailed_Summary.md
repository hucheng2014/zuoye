# Base Creation Grading Annotator Checklist — English Detailed Summary

**Source:** SharePoint — VCG Guidelines / VCG Base Creation / Feedback / Base Creation Grading Annotator Checklist.pdf

---

## Overview

This document is a structured checklist for annotators grading VCG Base Creation outputs. It covers **6 evaluation dimensions**, each with specific yes/no diagnostic questions and rating scales. The annotator works through each dimension sequentially, identifies issues, and assigns ratings accordingly.

---

## 1. Structural Integrity

**Purpose:** Detect anatomical, structural, or compositional errors in the generated image.

### Diagnostic Questions:
1. Does the subject have an incorrect number of parts for its type? (e.g., humans: 1 eye, 1 hand, 3 legs; animals: unexpected limbs; objects: unexpected components)
2. Are the proportions and arrangement of parts anatomically or structurally implausible given the prompt?
3. Are there any missing or extra body parts or object components not justified by the prompt?
4. Are there any parts that appear merged, fused, floating, or disconnected from the body/object?
5. Are there any visible distortions — twisted, melted, or malformed elements?
6. Are there any unintended artifacts — objects in the scene that do not logically belong?
7. If the image is highly stylized (cartoon, anime, abstract), are structural issues present relative to the internal logic of that style — not real-world realism?

### Rating Scale:
- **a) Severe** — Major distortions, unrecognizable, merging humans/animals/objects, missing body parts, extra/missing fingers, etc.
- **b) Noticeable** — Clearly impactful issues, twisted fingers, issues with eyes, misshapen object, etc.
- **c) Minor** — Slight issues only noticed after detailed inspection, person's gaze, minor distortions, artifacts, minor background issues.
- **d) No issues** — If all questions are answered as "no", mark no issues.

### Key Note:
> Evaluate each element against the prompt — not general real-world standards. A three-headed dog is structurally correct if the prompt requested it. For stylized art, only penalize when structure breaks the internal logic of the style.

---

## 2. Visual Quality

**Purpose:** Identify technical visual flaws unrelated to content or structure.

### Diagnostic Questions:
1. Is the image suffering from extreme overexposure (blown-out whites) or underexposure (crushed blacks) not specified by the prompt?
2. Is the image blurry across the whole image or major portions of it — not an intentional bokeh or depth-of-field effect?
3. Does the image appear stretched or squashed? Are objects unnaturally elongated or compressed, indicating a distorted aspect ratio?
4. Is the image rotated or skewed in an unnatural way (e.g., portrait turned on its side, warped perspective not justified by the prompt)?
5. Are there other technical visual flaws not covered above (e.g., severe pixelation, color banding, visible compression artifacts)?

### Rating Options:
If YES to any above — select the matching issue:
- Extreme contrast
- Blurry
- Stretched/squashed/cropped
- Rotated/skewed
- Other (leave comment)

If none apply → select "None of the above".

### Key Note:
> Do not penalize intentional stylistic choices: bokeh/depth-of-field, high-contrast backlighting/silhouettes, intentional blur, or other effects explicitly or implicitly requested by the prompt.

---

## 3. Text Quality

**Purpose:** Evaluate the accuracy and rendering quality of any text present in or requested by the prompt.

### Diagnostic Questions:
1. Does the image contain any text (on signs, labels, clothing, etc.), OR did the prompt explicitly request text?
2. If text is present: Is the text correctly spelled, with proper capitalization?
3. If text is present: Are all characters readable and cleanly rendered — no distorted, broken, or smudged letterforms?
4. If text was requested: Does the text appear in the correct location/object (e.g., on the sign, shirt, card) as specified by the prompt?
5. If text was requested: Does the formatting/style match the prompt's intent (e.g., handwritten, bold, centered, a specific font style)?

### Rating Steps:
- **Step 1 (Q1):** Is text present or requested? Yes / No.
- **Step 2:** If No on Q2 or Q3 → Rate Text Accuracy as **Moderate | Low**.
- **Step 3:** If No on Q4 or Q5 → Rate Text Alignment: **Moderately Aligned | Not Aligned**.

### Key Note:
> Do not penalize text that is naturally soft or unreadable due to distance, perspective, or lighting within the scene — this is contextually appropriate. Text accuracy applies to ALL visible text in the image, not just text the prompt requested. Random symbols on a product are not considered text. Scribble on a paper that does not have discernible letters is not considered text.

---

## 4. Input/Output Alignment

**Purpose:** Assess how well the generated image matches the content described in the prompt.

### Diagnostic Questions:
1. Are all key objects/subjects from the prompt present in the image?
2. Do the colors, shapes, textures, and details of depicted objects match what the prompt described?
3. Does the spatial arrangement and positioning of objects match the prompt (e.g., "cat under the tree", "in front of", "on top of")?
4. Does the overall mood or atmosphere match what the prompt described (e.g., peaceful, eerie, festive)?
5. Are there any major elements in the image that were NOT mentioned in the prompt and are not reasonably implied by it?
6. For ambiguous prompts: does the image make a reasonable and coherent creative interpretation without adding unrelated content?

### Rating Scale:
- **Yes** — All elements present, accurate, no redundant content.
- **Partial** — Most requirements met, minor omissions.
- **Captures most but not all** — Image loosely reflects the prompt.
- **No — major misalignment** — Many missing/extra elements.

### Key Note:
> Do NOT evaluate text quality here — that is assessed separately. Focus only on visual elements. For ambiguous prompts, creative interpretations are acceptable as long as they do not add content with no logical connection to the prompt.

---

## 5. Style Alignment

**Purpose:** Determine whether the image matches the requested artistic style or photorealism.

### Diagnostic Questions:
1. Does the prompt request a specific artistic style (e.g., watercolor, anime, cartoon, low poly, pixel art, ukiyo-e) or photorealism?
2. For photorealistic prompts: Does the image appear to have been captured by a real camera? Does it have realistic lighting, textures, materials, and perspective?
3. For non-photorealistic style prompts: Does the image consistently embody the key visual characteristics of the requested style (color palette, linework, texture, brushwork)?
4. Is the style applied consistently across the entire image, or only to certain parts?
5. If the style does not fully match: Is it because the image is blurry (making style assessment impossible), rendered in a different style, or inconsistently applied?

### Rating Options:
- **For photorealistic:** Very realistic | Somewhat realistic | Not realistic.
- **For non-photorealistic:** Matches Perfectly | Partially Matches | Does Not Match.
  - If not a full match, select applicable issue(s): Blurry (style unreadable) | Wrong style | Inconsistently applied | Other (comment required).

### Key Notes:
> Evaluate ONLY the style. Do not penalize for structural integrity issues or prompt content mismatches here — those are separate dimensions. For photorealistic assessment, focus on texture, color, lighting, and surface appearance, not on structural correctness.

> **User prompt style request overrides target style from the task.** If target style is empty, and user has not requested a specific style, the default style is Photorealism.

---

## 6. Diversity

**Purpose:** Assess visible demographic diversity among people depicted in the image.

### Diagnostic Questions:
1. How many visible people appear in the image? (Count adults, children, partial bodies — do not count mannequins, statues, robots, or unclear shapes)
2. If 2 or more people are visible: Do they appear to come from different ethnic/racial backgrounds, or do they all appear to belong to the same group?
3. If 2 or more people are visible: Is there a visible mixture of male-presenting and female-presenting individuals?

### Rating Options:
- **People count:** None | 1 | 2–3 | More than 3.
- **Apparent ethnicity:** All White/European | All same non-White group | Visible mixture | Can't be judged.
- **Apparent gender presentation:** All male-presenting | All female-presenting | Visible mixture | Can't be determined.

### Key Note:
> Base your answers only on what is visible in the image. Do not infer or guess identity. Do not label specific ethnicities (e.g., "Korean", "Brazilian"). Use only the provided category options. "Can't be judged/determined" is appropriate when faces are obscured, not visible, distorted, silhouetted, or too small to assess reliably.

---

## Summary of Evaluation Flow

| # | Dimension | Key Focus | Output |
|---|-----------|-----------|--------|
| 1 | Structural Integrity | Body parts, proportions, artifacts | Severe / Noticeable / Minor / No issues |
| 2 | Visual Quality | Exposure, blur, distortion, rotation | Issue type selection or "None" |
| 3 | Text Quality | Spelling, rendering, placement | Accuracy + Alignment ratings |
| 4 | Input/Output Alignment | Content match to prompt | Yes / Partial / Most / No |
| 5 | Style Alignment | Artistic style or photorealism | Match level + issue type |
| 6 | Diversity | People count, ethnicity, gender | Category selections |
