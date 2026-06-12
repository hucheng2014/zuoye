# VCG Image Editing and Generation Model Evaluation Guidelines Summary

> [!NOTE]
> This document is a comprehensive, high-fidelity **English Tutorial and Operational Manual** compiled from the official VCG Evaluation Guidelines (v.26.1.16-2), Workflow Information clarifications, and the April 16 quality feedback reports. It serves as a definitive reference for calibration team reviewers and annotators.

---

## 1. Evaluation Workflow & Core Methodology

### 1.1 Fundamental Principles
*   **Adhere to Dedicated Guidelines**: Evaluators must use the latest provided guides as the **only** references for the two workflows (Base Creation and Edit Model). Never mix or overlap evaluations with previous Image Evaluation or ADM guidelines.
*   **Thorough Examination via Zooming**: Avoid rushing or relying on general visual impressions. Evaluators must **click on all images and press the "+" key to expand them** for detailed analysis, paying close attention to anatomical proportions, text sharpness, and pixel-level consistency.
*   **Evaluate Images Separately**: For each task, evaluate the Left and Right images **individually per dimension** (evaluate Left first, then Right). Do not combine or conflate evaluations.

### 1.2 Structured Evaluation Scan Order
Before assigning any rating to a generated output image, the evaluator must follow this fixed **Triage Scan Sequence**:
1.  **Follow Edit Instructions**: Check **every single** action verb (add, remove, change, modify, etc.) and noun details requested in the Prompt against the output image.
2.  **Structural Integrity**: Inspect human/animal anatomy, physical layout plausibility, and text distortion or spelling errors.
3.  **Style Alignment**: Verify the output visually against target style definitions (e.g., polygon facets for Low Poly, color science for Vintage Film), rather than just matching style names.
4.  **Preservation of Unedited Areas**: Confirm that areas untouched by the edit instructions match the original input image pixel-for-pixel.
5.  **Integration & Visual Quality**: Assess the transition smoothness, contrast, blurriness, and lighting, factoring in prompt constraints (e.g., requested darkness).

---

## 2. Base Creation Workflow: Dedicated Rules

In the **Base Creation** (image generation) workflow, four critical rules distinguish it from standard image editing:
1.  **Blurry Image Rating**: An image should be marked as "Blurry" **only if the entire image is blurry**. Do not penalize if only the background is blurred (e.g., standard aesthetic shallow depth-of-field or bokeh).
2.  **Text Quality Separation**: Text Quality is a **standalone dimension**. Never evaluate text quality issues under the Structural Integrity (SI) dimension.
3.  **Illegible Text Grading**: If there is text in the image that is unreadable, garbled, or distorted, it must be marked as **Low Quality** (regardless of whether text was requested in the prompt). The option "Can't tell" should only be selected if the text was explicitly requested by the prompt but is completely absent from the image.
4.  **Ethnicity & Gender Group Logic**:
    *   If there is a **single person** in the image, Apparent Ethnicity and Gender **will not be evaluated**.
    *   For **groups**, if even one person's face is hidden, obscured, or turned away, select **"Can't determine"** for both Ethnicity and Gender for the entire group. (e.g., in a group of 5 people, if 2 are clearly male, 2 female, but 1 is obscured, the rating must be "Can't determine").
5.  **"Low Poly" Style Criteria**: The subject must exhibit clear, sharp polygonal facets (mostly triangles and quadrilaterals) with flat shading to be considered a match.
6.  **"Photorealism" Style Criteria**: The output must look exactly as if it was captured by a physical camera sensor with realistic depth, texture, highlights, and shadow gradients.

---

## 3. Edit Model Workflow: Dedicated Rules

In the **Edit Model** (image editing) workflow, the guidelines change significantly:
1.  **Text Quality Under Structural Integrity (SI)**: Unlike Base Creation, text quality in the Edit Model **is evaluated as part of Structural Integrity**.
    *   A spelling mistake in a single-word edit/text image warrants a **Noticeable** severity rating.
    *   Minor artifacts in letters (e.g., small pixel smudges on the word 'joy') are graded as **Minor**, as long as the overall structure is correct and the text is clear.
2.  **Dimension Boundary Clarifications**:
    *   **Unedited Portion Consistency**: The scope is strictly limited to regions of the image that were **not targeted** by the edit instructions.
    *   **Style Alignment**: Focuses on validating the artistic style of the final output, not just recognizing the style name.
    *   **Integration & Visual Quality**: Aesthetics explicitly requested in the prompt (e.g., "make the image gloomier, foggiest, and darker") are **not quality issues** and must not be penalized.

---

## 4. Seven Grading Dimensions & Severity Calibration Scales

### Dimension 1: Edit Instruction Following
Measures whether the model attempted and functionalized the requested change. **Focuses purely on functionality (did it do it?), not on execution quality.**

#### Rating Scale:
*   **Highly Aligned (The edited image follows the instructions closely)**
    *   The model applied the requested change in the correct area and reflects the exact intent of the prompt.
    *   All requested components (additions, removals, replacements) are correct with no semantic misunderstandings, missing text, or wrong elements.
*   **Somewhat Aligned (The edited image somewhat follows the instructions...)**
    *   The model attempted the change, but it is incomplete, partially applied, or has minor detail deviations.
    *   *Examples*: A prompt requests "Make the cactus arms smaller" but the arms remain unchanged; or "Change to pixel art, make panther happy, and add a bird" but the background is only partially pixelated.
*   **Not Aligned (The edited image does not follow the edit instructions...)**
    *   The requested edit was not done at all; the wrong object was modified; severe semantic misunderstanding occurred; or required text is completely missing.

---

### Dimension 2: Structural Integrity
Assesses the anatomical correctness and physical plausibility of subjects and objects in the image. **Rate structural integrity relative to the prompt’s fictional rules** (e.g., a five-legged table is structurally sound if the prompt requested it).

#### Triage Method for Edge Cases:
1.  **Check for Severe**: Is the flaw large enough to destroy the subject's basic form (e.g., a face with scrambled features, missing limbs)? If yes, select **Not Accurate**.
2.  **Check for Noticeable**: Are there obvious distortions that stand out instantly without looking closer (e.g., mismatched eyes, twisted joints)? If yes, select **Somewhat Accurate**.
3.  **Check for Minor**: Do small anomalies require a close look to spot (e.g., slightly off proportions, minor text smudges)? If yes, select **Mostly Accurate**.

#### Rating Scale:
*   **Highly Accurate (The details of the structure are highly accurate and plausible)**: The output is a complete success with zero anatomical issues or spelling mistakes.
*   **Mostly Accurate (Mostly accurate with minor unimpactful distortions)**: Appears fine at first glance. Close inspection reveals minor anomalies (e.g., a rabbit's eye slightly sticking out, or slight limb proportion shifts).
*   **Somewhat Accurate (Somewhat present with noticeable distortions or inaccuracies)**: Displays noticeable deviations that impact realism.
    *   *Examples*: Unevenly spaced/asymmetric eyes on a central face; a broken architectural line on a primary building; or a spelling mistake on a single word edit (e.g., "Alien" spelled as "Alein" on a sweatband).
*   **Not Accurate (Highly inaccurate with major and distracting distortions)**: A complete failure where anatomy collapses (jumbled human faces, extra or missing limbs, impossible physical joint bends, or gibberish text).
    *   *Examples*: A giraffe's neck fusing into a tree trunk; a person riding a horse where the human face is completely melted; or a dugong with completely deformed appendages. **Severe facial distortions must always be graded as Not Accurate.**

---

### Dimension 3: Preservation of Unedited Areas
Evaluates whether regions of the image that were not supposed to be edited remain visually identical to the original input.

#### Rating Scale:
*   **Highly Consistent**: The unedited portion is virtually identical to the original image in colors, lighting, textures, and coordinates.
*   **Mostly Consistent**: Mostly identical, with minor shifts in lighting or color upon close inspection that do not distract.
*   **Not Consistent**: Significant, unrequested modifications (e.g., background structures altered, background people removed/deformed).
*   **No Unedited Portion**: The prompt requested a **full-image transformation** (e.g., viewpoint changes, global restyling like "make it a watercolor painting"). Evaluators **must not** penalize background deviations under this scenario and should select this option.

---

### Dimension 4: Integration & Visual Quality
Measures how well the edited elements integrate into the scene, ensuring the transition is natural and free from technical rendering flaws.

#### Rating Scale:
*   **Great (Natural transition, seamless integration)**: Smooth blend with realistic lighting, shadows, reflections, and color harmony. No noticeable seams.
*   **Fair (Somewhat smooth with minor artifacts)**: Believable edit but contains minor artifacts, slight texture softness, or a mild color temperature mismatch.
*   **Poor (Rough transition, major artifacts)**: Severe rendering glitches.
    *   **Ten Visual Quality Defect Types**:
        1.  *Over/Underexposure*: Blown-out highlights or crushed shadows.
        2.  *Blurry*: Softness and loss of focus on edited subjects.
        3.  *Stretched/Squashed*: Distorted aspect ratios.
        4.  *Rotated/Skewed*: Unnatural perspective warping.
        5.  *Over-Smoothing*: Airbrushed, plastic-like texture with zero fine detail.
        6.  *Unnatural composition/proportion*: Unrealistic relative scaling of added elements.
        7.  *Unnatural lighting/poor color harmony*: Incorrect shadow casting directions or light source temperature clash.
        8.  *Unnatural texture/material*: Metal looking like rubber or skin looking like wax.
        9.  *Implausible scene layout*: Floating objects or incorrect physical overlap (clipping).
        10. *Harsh transition/obvious seam*: Jagged cut-out borders, looking "pasted on."

---

### Dimension 5: Style Alignment
Assesses how perfectly the output image embodies the target artistic style requested in the prompt.

#### Prompt-Override Style Rules:
1.  **Style Shifts**: If the task details list an Input Style and a different Output Style, evaluate whether the transition was successfully rendered.
2.  **Implicit Consistency**: If no style change is requested in the prompt, the model **must maintain the original style of the input**.
3.  **Prompt Dominance**: If the text prompt explicitly requests a specific style, **this overrides the Output Style field listed in the system interface**. (e.g., system lists Photorealistic, but prompt asks for "8-bit pixel art"; an 8-bit output is a success, and a photorealistic output is a Poor match).

#### Key Styles and Visual Criteria:
1.  **Surrealism**: Dream-like, illogical juxtaposed objects, melting textures, and floating components in vast landscapes.
2.  **Retro Illustration / Vintage Postcard**: Mid-20th-century advertisement aesthetic, halftone dot patterns, limited warm color palettes, bold linework, and distressed paper textures.
3.  **Abstract**: Focuses strictly on geometric color fields, overlapping shapes, dynamic lines, and textured, non-representational compositions.
4.  **Risograph**: Tactile newsprint textures, limited layered spot colors, and slight misregistration (misalignment of color layers).
5.  **Ukiyo-e**: Flat or flattened perspectives, bold calligraphic black outlines, flat areas of color, and traditional landscape/folklore subjects.
6.  **Pixelation & 8-Bit**: Square blocky pixels, very low resolution, sharp primary colors, and no anti-aliasing.
7.  **Low Poly**: Geometric mesh of visible facets (triangles/quadrilaterals), flat/simple shading, and minimalist fine details.
8.  **Art Nouveau**: Sinuous, asymmetrical curves, whiplash flowing lines, floral/natural motifs, and highly ornamental frames.
9.  **Oil Painting**: Simulates physical paint layers, visible brushwork ridges, thick impasto textures, deep chiaroscuro lighting, and canvas aging.
10. **Pop Art**: Screen-printing aesthetic, bold saturated colors, thick black outlines, Ben-Day dot shading, and repetitive consumerist subjects.
11. **3D Claymation**: Tactile plasticine details, visible fingerprints, soft studio lighting, and miniature set scale with shallow depth of field.
12. **Y2K Aesthetic**: Futuristic yet retro metallic, iridescent translucent finishes, cyber-inspired details, lens flares, and glossy aqua elements.
13. **Chinese Painting (Guohua)**：Calligraphic brushstrokes, black ink wash density gradients, prominent negative space, and red artist seals on silk textures.
14. **Madhubani Painting**: Dense, double-outlined geometric patterns, flat vibrant pigments, frontal eyes on profile faces, and zero empty space.
15. **Persian Miniature Painting**: Bird's-eye view, vertical layering, lapis lazuli blues, malachite greens, gold leaf highlights, and intricate manuscript floral margins.
16. **Ancient Egyptian Art**: Highly structured registers (rows), composite view (head in profile, eyes and torso frontal), flat earth tones, and hierarchical sizing.
17. **Benin Bronzes**: High-weight cast bronze or brass, intricate surface carving patterns, front-facing regal postures, and a dignified ceremonial mood.
18. **Vintage Film**: Simulated 35mm film grain, warm pastel color science, lifted milky blacks, lens flare, soft optical vignette borders.
19. **Tintype**: Wet-plate collodion artifacts, monochromatic sepia-silver tone, clouding chemicals, scratches, and a stoic subject gaze.
20. **Classic 90s Anime Film**: Hand-drawn look with clean cel-shaded character flat fills set against lush, highly detailed watercolor background textures.

---

### Dimension 6: Character Consistency
Measures how accurately the edited image preserves the identity, breed, or physical characteristics of the main subject(s).

#### Rating Scale:
*   **Highly Consistent**: Core traits (facial structure, fur pattern, unique markings, clothing style, colors) are perfectly preserved.
*   **Somewhat Consistent**: The general identity is recognizable, but minor face changes, accessories, or animal breed markings deviate.
*   **Not Consistent**: The subject appears as a completely different individual, species, or object category.
*   **Changed According to Prompt**: Select this if the identity alteration was explicitly requested (e.g., "Make the boy an adult" or "Turn the cat into a robot"). **Do not penalize the model under this option.**

---

### Dimension 7: Overall Usability
A holistic final evaluation of whether the edited image is ready for immediate deployment.

#### Rating Scale:
*   **Yes**: The edited content is exceptionally accurate, visually integrated, and completely free of artifacts. No further edits needed.
*   **Yes, with minor edits**: High-quality edit, but requires tiny, non-critical corrections (e.g., a tiny seam blend or minor color brush-up) that are extremely easy to fix.
*   **No**: The instructions were ignored, the subject is deformed, text is gibberish, or unedited areas are ruined.

---

## 5. Severity Calibration & Crucial Corrective Guidelines

### 5.1 Correcting Under-penalization trends (Critical Calibration Rule)
*   **The Issue**: Annotators frequently rate structural collapses (melted faces, anatomical floating, impossible limb angles) as "Mostly Accurate" or "Somewhat Accurate" out of leniency.
*   **Calibration Target**:
    *   **Mostly Accurate**: Reserved ONLY for tiny, microscopic detail issues (e.g., a rabbit's eye outline having a single pixel-level asymmetry).
    *   **Somewhat Accurate**: Non-critical but obvious structural anomalies.
    *   **Not Accurate**: **Any distinct face distortion, floating object, impossible anatomy, or garbled text must be penalized strictly as Not Accurate (Severe).**

### 5.2 Complete Prompt Verification
Evaluators must not judge based on a quick "overall visual impression." You must verify every word, count, and style requested in the text instruction before assigning a score.

### 5.3 Correct Grading of Highly Preserved Areas
Do not over-penalize. If the model perfectly preserved the original unedited area with zero changes, it must be rated **Highly Consistent** without downrating.

---

## 6. Side-by-Side (SxS) Rating Criteria

Rank the Left and Right output images against each other in accordance with their single-side dimension ratings:
*   **Much Better**: A massive quality gap exists between the two images (e.g., Left has no distortions, while Right has severe limb mutations).
*   **Slightly Better**: Both images are close in overall quality, but one has minor improvements in shadow realism, transition sharpness, or text legibility.
*   **Same**: There is no discernible difference. Both images equally succeed or fail to meet the grading criteria.
