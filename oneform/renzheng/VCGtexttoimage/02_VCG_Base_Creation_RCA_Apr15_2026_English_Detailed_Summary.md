# VCG Base Creation RCA Apr15'26 English Detailed Summary

Source: [vcg_browser_sources/text/02_VCG Base Creation — RCA Apr15'26 v1.2.txt](vcg_browser_sources/text/02_VCG%20Base%20Creation%20%E2%80%94%20RCA%20Apr15%2726%20v1.2.txt:1)

## 1. Document Purpose

This document is the Apr15'26 feedback and root-cause analysis for VCG Base Creation. It summarizes the dimensions with the highest annotation error concentration, the dominant error patterns, the likely root causes, and the proposed calibration actions. The overall conclusion is that the team often notices problems but does not penalize them strongly enough, and that annotators are not consistently using a structured process to check the prompt and the image.

## 2. Highest-Error Dimensions

Errors are concentrated in the following dimensions:

1. Structural Integrity: very high across all locales.
2. Contains All Requests: high.
3. Style Match: high.
4. Text Included or Requested: high.
5. Captured by Camera: medium-high.
6. Visual Quality: medium.

This means the problem is not limited to one dimension. It spans structure, prompt coverage, style recognition, text handling, photographic realism, and technical visual quality.

## 3. Main Error Patterns

### 3.1 Under-Penalization Is the Dominant Problem

Annotators often recognize that something is wrong but apply a penalty that is too lenient.

Common examples include:

- Extra fingers, malformed limbs, and other structural distortions are marked as Minor instead of Severe.
- Missing prompt elements are graded as captures most instead of being downgraded more strongly or marked not aligned.
- Text spelling errors, artifacts, and pseudo-text are identified but not reflected in the final Text score.
- Style mismatches are acknowledged but still receive ratings that are too generous.

Trend: annotators default to conservative grading and avoid strict penalties, producing a systematic under-penalization pattern.

### 3.2 Frequent Guideline Misunderstanding

Common misunderstandings include:

- Severity thresholds for Minor, Noticeable, and Severe are applied inconsistently across locales.
- Style categories such as Genmoji and Illustration are confused with photorealism or generic AI aesthetics.
- Photorealism is judged by personal impression rather than objective visual cues such as texture, lighting, material, and perspective.
- Flag criteria for trademarked or protected content are overlooked.
- The 2b Text tag is marked even when no text was requested; in those cases N/A should apply.

Trend: the team has a clear guideline-understanding and calibration gap.

### 3.3 Unstable Scoring Across Similar Cases

The same kind of issue may be over-penalized in one case and under-penalized in another.

Examples:

- Structural Integrity: severely flawed images pass, while clean images are penalized.
- Visual Quality: blurry subjects are missed, while clear images are downgraded.
- Captured by Camera: obvious AI-generated images pass as realistic, while genuine photos are downgraded.
- Flags: neutral content is flagged without sufficient justification.

Trend: the team lacks shared calibration anchors, so evaluations vary by individual preference.

### 3.4 Incomplete Prompt Reading

Annotators often react to the overall visual impression first instead of systematically decomposing the prompt.

Common issues:

- Quantities, object attributes, and spatial relationships are missed.
- Partial fulfillment is accepted when the image is broadly close.
- Text requirements are not checked word by word against the output.

Trend: first visual impression often overrides structured prompt verification.

### 3.5 Shallow Style Recognition

- Annotators recognize the style name but do not verify whether the image actually contains the required visual features.
- Mixed styles or partial style mismatches are not penalized consistently.
- Illustration is sometimes accepted as Genmoji, and Photorealism is confused with Style Match.

Trend: the team needs more concrete style references, external research, and example-based calibration.

### 3.6 A/B and Preference Ranking Errors

- In comparisons, annotators sometimes choose the better-looking image rather than the image with fewer errors.
- Preference Ranking conflicts with the dimension-level ratings in the same task.
- Annotators are more comfortable evaluating single images than making calibrated relative comparisons.

Correct approach: use the dimension-level ratings as the basis and choose the less wrong image, not simply the image that is more visually attractive.

## 4. Root-Cause Summary

The RCA identifies five major causes:

1. Annotators are unclear about the boundaries between Minor, Noticeable, and Severe, so they default to conservative low penalties.
2. Annotators inspect images randomly instead of following a fixed scan order.
3. Style understanding is insufficient. Annotators recognize names but do not verify visual language.
4. Prompts are read only partially, causing missed objects, actions, text requirements, and style constraints.
5. The team lacks shared calibration anchors and often scores based on personal judgment rather than a unified standard.

## 5. Improvement Plan

### 5.1 Fixed Image Scan Order

Each image should be checked in this order:

1. Structural Integrity: anatomy, hands, faces, and object structure.
2. Prompt coverage: whether all requested elements appear and are correct.
3. Style match: analyze the actual style carefully and research if uncertain.
4. Text accuracy: presence, spelling, formatting, and capitalization.
5. Visual Quality: blur, stretching, skewing, clarity, and other technical issues.
6. Flags: safety, trademark, cultural, or other flag criteria.

### 5.2 Severity Calibration

#### Minor

- Not obvious at first glance and usually found only on close inspection.
- Examples include a slightly detached vase handle, a small chair missing two legs but not visibly obvious, slightly fused fingers, or small background castle structure issues.

#### Noticeable

- Visible without zooming and disruptive to viewing, but the image remains understandable.
- Examples include a hand that does not look like it is holding a cup, an abnormal clothing edge protrusion, or a hanger floating above a chair rather than hanging from it.
- Some obvious eye, nose, mouth, or ear problems should be upgraded to Noticeable instead of Minor.

#### Severe

- Immediately obvious and damaging to realism or the subject's basic form.
- Examples include a completely distorted human face, severely fused rabbit ears, eyes, mouth, or tail, or a person with extra fingers.
- Incorrect finger count should usually be treated as Severe Structural Integrity.

### 5.3 Penalty Calibration Examples

- Incorrect finger count: Severe Structural Integrity. Extra fingers on both adults must not be missed.
- Missing non-core elements: may be captures most but not all.
- Completely wrong or missing main subject: Not aligned. For example, if the prompt requests golden episcopal rings but the output shows wedding rings, the image is not aligned.
- Severely misspelled or heavily broken text: Low Accuracy, not moderate.
- Blurry subject: Visual Quality should be downgraded. If there is no single subject, the overall scenic view still should not be broadly unclear.
- Bokeh does not equal blur and should not be penalized as a defect when it is a normal depth-of-field effect.

### 5.4 Style Recognition Requirements

- If the guideline does not cover a style, annotators should research that style.
- If demo samples do not load, click Did Not Load and then switch back so examples refresh.
- Photorealism must be judged using texture, light, shadow, and material surface evidence.
- Overly smooth skin, food, or object surfaces often indicate that an image is not photorealistic.
- Obvious AI-generated images, illustrations, noir digital illustrations, and similar outputs must not be treated as real photographs.

### 5.5 Image Comparison Framework

When comparing left and right images, ask:

1. Which image misses fewer prompt elements?
2. Which image has fewer structural problems?
3. Which image has better Visual Quality?
4. Which image has more consistent dimension-level ratings?
5. Is the Preference Ranking consistent with the preceding dimension scores?

Core principle: choose the image with fewer errors, not the image that simply looks prettier.

## 6. Most Important Execution Reminders

- Do not downgrade severe hand, face, or limb problems to Minor.
- Do not ignore prompt omissions just because the image looks good overall.
- Do not use personal taste as evidence for Photorealism.
- Do not mark a text tag as requiring scoring when no text was requested.
- Style evaluation must inspect visual language, not just the style name.
- Preference Ranking must be consistent with Structural Integrity, Alignment, Style, Visual Quality, and other dimension ratings.
