# VCG Creation RCA Apr09'26 English Detailed Summary

Source: [vcg_browser_sources/text/04_VCG Creation RCA Apr09'26 v1.2.txt](vcg_browser_sources/text/04_VCG%20Creation%20RCA%20Apr09%2726%20v1.2.txt:1)

## 1. Document Purpose

This document is the Apr09'26 feedback and root-cause analysis for VCG Base Creation. It identifies concentrated errors in Structural Integrity, Style Match, Contains All Requests, and text-related scoring. It also provides severity calibration, penalty calibration, Genmoji style calibration, and image-comparison improvement guidance.

Core conclusion: the team's biggest problems are under-penalization, inconsistent guideline interpretation, incomplete prompt checking, and A/B comparisons that fail to choose the image with fewer errors.

## 2. Error Concentration Areas

High-error dimensions include:

1. Structural Integrity: high, with 5+ errors.
2. Style Match: high, with 5+ errors.
3. Contains All Requests: high, with 4 to 5 errors.
4. Text-related errors: significant, with 5 errors.

The team struggles most with:

- Understanding what the image should look like structurally.
- Interpreting styles incorrectly, especially Genmoji and Chibi.
- Fully checking all prompt requirements.

## 3. Error Breakdown

### 3.1 Under-Penalization Is the Main Problem

Repeated patterns include:

- Issues that should be Major or Severe are marked as Minor.
- Missing elements are not penalized enough.
- Structural problems are downplayed.
- Extra fingers and distorted limbs are marked as Minor.
- Missing key prompt elements are still rated as captures most.

Trend: the team is generally too lenient and conservative in grading.

### 3.2 Frequent Guideline Misunderstanding

Recurring root-cause tags include:

- GL Misunderstanding.
- Misread Context.
- Missed Key Information.

These especially affect:

- Style Match.
- Text inclusion.
- A/B comparisons.

The document emphasizes that this is not simply a skill problem. It is also a guideline clarity, interpretation, and calibration problem.

### 3.3 Text Handling Is Inconsistent

Common problems include:

- Required text is missing but not caught.
- Text is present in the image but judged incorrectly.
- Spelling and capitalization errors are ignored or misgraded.
- Example: SIILENCE is not penalized correctly.
- Text requested by the prompt is marked as not needed, or text is evaluated when it should not be.

Trend: the team lacks a consistent framework for text evaluation.

### 3.4 A/B Judgment Errors

- Cases such as A slightly better versus B perfect are misjudged.
- Context is ignored during comparison.
- The wrong winner is selected even when one image has clear defects.

Trend: relative evaluation is weak, not only single-image absolute scoring.

## 4. Root-Cause Analysis

The RCA summarizes the causes as follows:

1. Annotators do not have clear boundaries for Minor, Noticeable, and Severe, so they default to safer low penalties.
2. Image inspection is random and lacks a fixed scan process.
3. Style understanding is shallow: annotators know the style name but do not verify actual visual features.
4. Prompts are read only partially, causing missed objects, actions, text, styles, and other constraints.

## 5. Improvement Plan

### 5.1 Strict Image Scan Order

Each evaluation should follow this sequence:

1. Structural Integrity: fingers, hands, faces, and anatomy.
2. Prompt coverage: missing elements, actions, relationships, and attributes.
3. Style match: whether the image truly follows the target style.
4. Text accuracy: content, spelling, capitalization, placement, and readability.
5. Visual quality: sharpness, blur, stretching, and technical defects.
6. Improve the zooming workflow, especially for small text.
7. Improve accuracy when checking generated text.

### 5.2 Severity Calibration

#### Noticeable Upgrade Rule

Problems involving eyes, nose, mouth, ears, and other facial features may now be upgraded to Noticeable even if they are not immediately obvious at first glance.

Examples:

- A judge's left eye is not sufficiently rounded at the bottom: Noticeable.
- A swimmer's foot defect is visible when zoomed in: Noticeable.
- An abnormal thumb and slightly deformed eyes: Noticeable.
- Minor distortions in buildings, tower ornaments, or background statues may remain Minor if they are not obvious at first glance.

#### Noticeable: Visible but Not Totally Destructive

- A barbell plate is positioned unrealistically and appears to float, disrupting the scene.
- A vehicle has two steering wheels, which is unrealistic.
- The connection between truffles and a stick is unclear, making the object hard to recognize.

#### Severe: Breaks Realism or Intent

Severe means the issue damages the basic structure, realism, or prompt intent.

Examples:

- A woman's fingers are severely deformed.
- A dinosaur head is fused with root-like or bone-like structures; a person's hand is missing; the held object is unclear.
- A baby's face has duplicated facial features and is severely distorted overall.
- A person's head is elongated, the hand is melted with no clear fingers, and the lip area is abnormal.
- A swimmer has no facial features, extremely tiny hands, abnormal feet, and a distorted second arm.
- A face and hand are clearly twisted, and a carrot is disproportionately large.

## 6. Penalty Calibration

### 6.1 Incorrect Finger Count

- Incorrect finger count is Severe Structural Integrity.
- Extra or missing fingers must be penalized and should not be downgraded to Minor.
- This issue affects Structural Integrity and should not be transferred arbitrarily to other dimensions.

### 6.2 Missing Partial Elements

Missing color, action, atmosphere, objects, or relationships usually affects Input/Output Alignment.

Examples:

- The prompt asks for I Ustand neon light made entirely of spaghetti, but the output places spaghetti separately and does not form the neon letters. This should be captures most but not all.
- The prompt asks for wilted flowers bending toward a cracked window in a storm, but the relationship between flower and window is not expressed. This should be captures most but not all.

### 6.3 Wrong or Missing Main Object

- If the prompt asks for rusty dumbbells but the output contains no dumbbells and instead shows a completely different rusty object, the rating should be Not aligned.
- If the output contains normal dumbbells but they are not rusty, captures most but not all may be appropriate because the main object exists but an attribute is missing.

### 6.4 Blur Belongs to Visual Quality

- Lack of clarity in the main object or important area should downgrade Visual Quality.
- Obvious blur in the bottom of the image or on the subject should be penalized.
- If the face is deformed, that is a Structural Integrity issue, not a Visual Quality issue.

## 7. Genmoji Calibration

The document calls for specific calibration on Genmoji:

- Genmoji refers to AI emoji that users can generate instantly on their devices.
- Annotators should refer to demo examples or conduct research to understand Genmoji style, color, and smooth visual characteristics.
- Genmoji is not ordinary illustration, Chibi, or generic 3D art.
- If the image shows a completely different or unrelated style, mark Does Not Match.
- If either image is ordinary illustration rather than emoji style, it should also be marked Does Not Match.

When judging Genmoji, check:

- Whether it resembles native emoji.
- Whether it is rounded, simple, and readable at small size.
- Whether the background follows the required constraints.
- Whether the character expression is clear.
- Whether it avoids overly complex, realistic, or illustration-like backgrounds.

## 8. Image Comparison Understanding

The core principle for A/B comparison is to choose the less wrong image, not the better-looking image.

Comparison checklist:

1. Which image misses fewer prompt elements?
2. Which image has fewer structural problems?
3. Which image is closer to the required style?
4. Which image has fewer text errors?
5. Which image has better Visual Quality?
6. Is the final choice consistent with the previous dimension scores?

If an image is prettier but misses a key prompt element or has more serious structural errors, it should not win Overall Quality.

## 9. Most Important Execution Rules

- Check structure first, then prompt, then style, text, and visual quality.
- Zoom in to inspect hands, faces, facial features, fingers, and limbs.
- Do not mark obvious structural errors as Minor.
- Missing text, misspellings, capitalization errors, and pseudo-text must be reflected in the score.
- Style Match must be judged by actual visual features, especially for Genmoji.
- A missing primary object should be strongly penalized as Not aligned.
- In comparisons, choose the image with fewer errors, not the image that is more visually attractive.
