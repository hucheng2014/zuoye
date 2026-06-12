# VCG Base Creation & Edit Model Workflow Info English Detailed Summary

Source: [vcg_browser_sources/text/01_VCG Base Creation & Edit Model info.txt](vcg_browser_sources/text/01_VCG%20Base%20Creation%20%26%20Edit%20Model%20info.txt:1)

## 1. Document Purpose

This file is a supplemental workflow reminder for the VCG Base Creation and Edit Model workflows. It is not a complete scoring manual. Its main purpose is to highlight critical calibration points before evaluators begin official grading. The central message is that annotators must not carry over old Image Evaluation, ADM, or other previous workflow rules into this project. The current newly provided guidelines must be treated as the only valid reference for these two workflows.

## 2. General Work Requirements

- Watch the provided recordings before starting the guides or doing evaluations.
- Treat Base Creation and Edit Model as two separate workflows with different rules.
- Use the newly provided workflow-specific guidelines only.
- Do not mix in past Image Evaluation, ADM, or unrelated project standards.
- Do not rush through images or make assumptions based on first impressions.
- Zoom into images when needed and evaluate each dimension independently.

## 3. Key Rules for Base Creation

### 3.1 Blur and Visual Quality

- Mark an image as blurry only when the whole image, or the main assessable content, is blurry.
- Do not penalize normal background blur, depth-of-field effects, or bokeh as image blur when the subject itself is clear.
- Keep alignment and visual quality separate. Whether the image contains the requested content belongs to Input/Output Alignment. Whether the image is clear, distorted, or technically flawed belongs to Visual Quality or Structural Integrity.

### 3.2 Text Quality Is an Independent Dimension

- In Base Creation, Text Quality is a separate scoring dimension.
- Do not evaluate text quality under Structural Integrity in this workflow.
- If text appears in the image and should be readable but cannot be read, mark it as Low Quality, regardless of whether the prompt requested the text.
- The option Can't Tell should be used only when the prompt requested text but no text is present in the image, so the text quality cannot be evaluated.
- Spelling, capitalization, readability, broken characters, pseudo-text, and corrupted lettering must all be reflected in Text Quality.

### 3.3 Low Poly Style

- Low Poly output must show clear polygonal structure.
- The subject should display obvious triangular or quadrilateral facets, low-poly geometry, and segmented shading.
- A simplified, cartoon-like, or low-detail image is not automatically Low Poly.

### 3.4 Photorealism Style

- Photorealism means the image should look as if it was captured by a real camera.
- Evaluators should rely on objective photographic cues: skin and material texture, lighting, shadow behavior, perspective, depth of field, color tone, and surface detail.
- Do not judge photorealism based only on whether the image looks appealing or whether it vaguely feels realistic.

### 3.5 Known Guideline Page Issues

- Page 102 says Egyptian style, but the example images are Persian paintings.
- Page 103 says Benin Bronze, but those pictures are also Persian paintings.
- These issues have already been reported to the client. Evaluators should not let the page-label errors confuse style judgments.

### 3.6 Diversity Evaluation Notes

- Apparent ethnicity and gender are not evaluated for a single-person image.
- For group images, if even one person's face is not visible, is blocked, is too small, is too blurry, or cannot be judged reliably, both ethnicity and gender should be marked as can't determine.
- Example: if an image shows five people, four of whom can be assessed, but the fifth person's face cannot be seen or judged, the whole group should not be forced into a guessed category. Choose can't determine.

### 3.7 Structural Integrity Requires Close Inspection

- Click and enlarge images when evaluating.
- For people and animals, carefully check faces, facial features, eye direction, number and shape of fingers, limb proportion, limb count, and joint connections.
- Clear face deformation is a Severe issue.
- Most obvious structural problems should not be downgraded to Minor. The actual severity criteria must be applied strictly.

### 3.8 Alignment Must Cover All Prompt Requirements

- Input/Output Alignment must be assessed against every object, action, attribute, relationship, and scene requirement in the prompt.
- If the prompt asks for a scene in a gym, evaluators must confirm that the scene actually reads as a gym.
- If only part of the requested content appears, the score should be downgraded to captures most but not all.
- If the main object is wrong or missing, the alignment penalty should be more severe.

## 4. Key Rules for Edit Model

### 4.1 Text Quality Belongs Under Structural Integrity

- Unlike Base Creation, text quality in Edit Model is part of Structural Integrity.
- A spelling error in a word image may count as a Noticeable issue.
- Small lettering defects may be Minor if the overall structure is good and the text remains understandable and clear.

### 4.2 Missing Text and Page Issues in the Guide

- Page 37 has missing text and should read: reflecting in the output.
- Page 64 has missing text and should read: thus not a total failure.
- Pages 103 and 105 contain duplicate content, which the client already knows.
- Page 105 should list four reasons that may be selected for Fair or Poor images, such as blurry and different output style.
- Page 121 is actually about comments, not Usability. Page 122 contains the Usability content.

### 4.3 Dimensions May Overlap, but Still Need Correct Assignment

- Some visual quality issues may also affect Structural Integrity, such as impossible scene logic, unreasonable spatial layout, or physically inconsistent objects.
- Even when dimensions overlap, evaluators should decide which dimension is most directly responsible according to the project guide.

### 4.4 Edit Model Image Comparison Workflow

- Evaluate each image separately.
- Assess the Left image first, then the Right image.
- Do not merge judgments for the two images.
- Judge each dimension separately, especially Structural Integrity, unedited portions, and Character Consistency.
- Continue to inspect people and animals strictly, including faces, eyes, fingers, limb proportions, and limb counts.

### 4.5 Prompt Action Requirements Matter

- In Edit Model, pay close attention to whether the prompt asks to change, remove, add, or perform another specific edit action.
- Whether the requested edit action was correctly performed affects Instructions and Alignment.
- Do not judge only whether the final image looks good. Check whether the correct object was edited, whether areas that should remain unchanged were preserved, and whether all prompt elements were satisfied.

## 5. Special Error Example Highlighted by the Document

For example prompts such as:

- a girl and a boy sitting on a life ring
- two kids in life jackets

The document says to ignore the rating suggestions originally shown in the example. The suggested Minor issues and Highly aligned ratings are incorrect.

Correct interpretation:

- Alignment should be downgraded because the requested content is not fully satisfied.
- Structural Integrity should be penalized more strongly because the structure issues are more serious than Minor.

## 6. Practical Checklist

1. Confirm whether the current task belongs to Base Creation or Edit Model.
2. Use the current new guide only; do not use old project rules.
3. Zoom in and inspect subjects, hands, faces, eyes, animals, and background objects.
4. In Base Creation, score Text Quality independently. In Edit Model, evaluate text quality under Structural Integrity.
5. Judge Photorealism using real-camera visual evidence.
6. Require clear polygonal facets for Low Poly style.
7. Check every prompt object, action, attribute, quantity, scene, and relationship for Alignment.
8. For group diversity evaluation, rely only on visible evidence. If one person cannot be judged reliably, choose can't determine.
9. Evaluate Left and Right images separately; do not combine judgments.
10. Do not downgrade obvious structural errors to Minor.
