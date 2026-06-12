# VCG Base Creation and Edit Model Workflow Tutorial Summary

Source: PDF open in the browser tab, `VCG Base Creation & Edit Model info.pdf`  
Browser title: `VCG Base Creation & Edit Model info`  
PDF metadata: 2 pages, exported from Microsoft Word, created/modified on 2026-03-06.  
Summary date: 2026-05-11.

## 1. Purpose

This tutorial clarifies evaluation guidance for two separate VCG workflows:

- `Base Creation`
- `Edit Model`

The main instruction is to treat these as distinct workflows with their own current guidelines. Do not mix them with previous Image Evaluation, ADM, or older workflow guides. Evaluators should watch the provided recordings before using the guides, then evaluate carefully without rushing or making unsupported assumptions.

## 2. General Principles

### 2.1 Watch the recordings first

Before starting the written guides, watch the recordings provided for the workflow. The recordings are part of the training context and help explain scoring boundaries, examples, and common mistakes.

### 2.2 Use only the current workflow guidelines

`Base Creation` and `Edit Model` each have their own specific updated guidance. Use the correct guide for the active workflow. Do not rely on old Image Evaluation rules, ADM rules, or habits from previous projects.

### 2.3 Evaluate slowly and verify details

Evaluation should be deliberate. Check the image, prompt requirements, and scoring dimensions directly. Do not assume that a mostly acceptable image satisfies all requirements, and do not guess when evidence is missing or unclear.

## 3. Key Differences Between the Two Workflows

| Topic | Base Creation | Edit Model |
| --- | --- | --- |
| Relationship between Text Quality and Structural Integrity | `Text Quality` is a separate dimension and should not be evaluated under `Structural Integrity` | `Text Quality` is part of `Structural Integrity` |
| Main focus | Whether the generated image satisfies the prompt, requested style, quality, and structural requirements | Whether the edit correctly performs the requested change while preserving unedited areas and character consistency |
| Apparent ethnicity and gender | Not evaluated when there is a single person in the image | No special single-person rule is stated in this document; follow the Edit Model guide |
| Left/right image handling | The document does not emphasize left/right separation for Base Creation | Evaluate each image separately by dimension: first Left, then Right |
| Structural checks | Pay close attention to humans, animals, faces, eyes, fingers, limb proportions, and limb counts | Same checks, with extra attention to unedited portions and character consistency |

## 4. Base Creation Workflow

### 4.1 When to mark an image as blurry

Mark an image as blurry only if the entire image is blurry. Do not mark it blurry merely because the background is blurred.

The evaluator should distinguish between:

- photographic depth of field or background blur
- full-image blur where the subject is also unclear
- localized blur that does not prevent the main subject from being evaluated

### 4.2 Text Quality is its own dimension

In `Base Creation`, text quality is evaluated as the separate `Text Quality` dimension. Do not include text spelling, readability, or clarity issues under `Structural Integrity`.

Practical implications:

- Unreadable or low-quality text belongs under `Text Quality`.
- Structural integrity should focus on image structure, anatomy, object construction, spatial layout, and similar issues.
- Do not double-penalize text problems under structural integrity.

### 4.3 How to handle unreadable text

If text appears in the image and cannot be read, mark it as `Low Quality`, regardless of whether the prompt requested text.

Use `can't tell` only when the prompt requested text but the image does not contain the requested text, making the text impossible to assess. This is different from text being present but unreadable.

Decision boundary:

- Text is present but unreadable: `Low Quality`
- Prompt requested text, but no text is present: `can't tell`
- Prompt did not request text, but unreadable text appears: still `Low Quality`

### 4.4 Low poly style requires visible polygon structure

For a `Low poly` output style, the subject must show clear polygonal features. These are mostly triangular shapes, though quadrilateral shapes can also count.

Do not treat an image as low poly only because it is simplified, stylized, or low-detail. Expand the image and inspect the subject for actual polygon facets.

### 4.5 Photorealism means camera-like realism

`Photorealism` means the image should look as if it was captured by a real camera. This is not the same as simply being high quality or highly detailed.

Check whether:

- lighting resembles a real photographic environment
- materials, shadows, and depth of field feel natural
- people, animals, and objects avoid obvious AI-generated or illustrated artifacts
- the image looks more like a photograph than a render, drawing, cartoon, or concept image

### 4.6 Known page/example issues in the guide

The `Base Creation` guide contains two known mismatches, and the client has been informed:

- Page 102 says Egyptian style, but the example images are Persian paintings.
- Page 103 says Benin Bronze, but the images are also Persian paintings.

Do not let those titles mislead the evaluation. Recognize that the page labels and examples do not match.

### 4.7 Apparent ethnicity and gender rules

When there is a single person in the image, apparent ethnicity and gender are not evaluated.

For group images, if even one person's face cannot be seen or assessed, select `can't determine` for both apparent ethnicity and gender. This applies even if the other people in the group are clear.

Example logic:

- Five people are shown; four are clear and one face is hidden: choose `can't determine` for both apparent ethnicity and gender.
- A single-person image: do not evaluate these two attributes.
- A group image where every face is visible: evaluate according to the guide.

### 4.8 Expand images for detailed structural checks

Images can be clicked and expanded with the `+` control. Use this to inspect details carefully, especially for `Structural Integrity`.

Pay close attention to:

- humans
- animals
- facial features
- eyes and gaze direction
- finger count, shape, and attachment
- limb proportions, counts, and placement

Clear face distortions are severe issues. Evaluators should be detailed and apply the proper criteria. Most obvious structural problems should not be treated as merely `minor`.

### 4.9 Alignment requires full prompt coverage

For `Alignment`, confirm that all required prompt elements are covered properly. Elements should not be missing, partial, or only vaguely implied.

For example, if the prompt requires a gym setting, verify that the setting actually looks like a gym. The question is not whether the image is generally attractive, but whether the prompt requirements were fully and accurately satisfied.

## 5. Edit Model Workflow

### 5.1 Text Quality is part of Structural Integrity

Unlike `Base Creation`, text quality is part of `Structural Integrity` in `Edit Model`.

Rules from the document:

- A spelling mistake can be a `Noticeable` issue for single-word images.
- Small artifacts in letters can be `minor` if the overall integrity is good and the text remains understandable and clear.
- The judgment depends on readability, clarity, and whether the defect harms overall structural integrity.

This is one of the easiest workflow differences to mix up: in `Base Creation`, text quality is separate; in `Edit Model`, it belongs under structural integrity.

### 5.2 Missing text and page corrections in the guide

The `Edit Model` guide has several known missing-text or page-content issues:

- Page 37 is missing a small phrase; the missing text should read: `...reflecting in the output.`
- Page 64 is also missing part of the sentence; the missing text should read: `...thus not a total failure.`
- Pages 103 and 105 have the same content; the client is aware.
- Page 105 should list four options to choose from when an image is `Fair` or `Poor`, such as blur or a different output style.
- Page 121 is about comments, not `Usability`; the client is aware.
- Page 122 contains the `Usability` content.

Use these corrections while interpreting the guide so that missing text, repeated content, or mislabeled sections do not affect evaluation.

### 5.3 Visual Quality can overlap with Structural Integrity

Some issues that appear related to `Visual Quality` can also affect `Structural Integrity`. The document specifically calls out implausible scenes and spatial layout.

If the layout, spatial relationship, object placement, or scene logic is not plausible, do not treat it only as a visual-quality issue. It may also be a structural-integrity issue.

### 5.4 Expand images and inspect each dimension

`Edit Model` also requires clicking and expanding images before evaluation. Pay special attention to:

- `Structural Integrity`
- `Unedited portions`
- `Character consistency`

As with Base Creation, inspect humans and animals closely: faces, eyes, gaze, fingers, limb proportions, and limb counts. Clear face distortions are severe. Obvious errors should usually not be downgraded to `minor`.

### 5.5 Evaluate Left and Right separately

In `Edit Model`, evaluate each image individually for each dimension. Start with the Left image, then evaluate the Right image.

Do not combine the two images into one overall judgment. If the Left image has a structural issue and the Right image does not, each image still needs its own dimension-level assessment.

### 5.6 Check the required edit action

`Edit Model` prompts usually specify actions such as change, remove, or add. Verify whether the model performed the requested action and whether all required elements are present.

These requirements directly affect:

- `Instructions`
- `Alignment`

If the prompt asks to remove an element and it remains, or asks to add an object and it is missing, the relevant dimensions should reflect that failure.

### 5.7 Unedited portions and character consistency

Edit Model evaluation is not just about whether the edited target changed. It also requires checking whether areas that should remain unchanged were preserved.

Check whether:

- unedited portions were accidentally modified
- the original character remained consistent
- identity, appearance, position, or key character features changed unnecessarily
- the edit damaged the original structure or spatial relationship

## 6. Specific Example Correction

The document says to ignore the rating suggestions for a specific example involving children, a life ring, and life jackets.

The suggested `Minor issues` and `Highly aligned` ratings are wrong. The corrected interpretation is:

- `Alignment` should be downgraded because the prompt's scene or element requirements are not sufficiently satisfied.
- `Structural Integrity` should receive a higher penalty, meaning the issue should be judged more severely rather than treated as minor.

This example is a reminder not to follow suggested example ratings mechanically. If a rating suggestion conflicts with the corrected workflow guidance, use the corrected guidance.

## 7. Practical Checklist

### 7.1 Before evaluation

- Have the recordings been watched?
- Is the task `Base Creation` or `Edit Model`?
- Are you using only the current guide for that workflow?
- Are you avoiding old Image Evaluation or ADM standards?

### 7.2 Image quality and structural checks

- Is the whole image blurry, or only the background?
- Are human or animal faces distorted?
- Are eyes and gaze direction plausible?
- Are finger count, finger shape, and finger attachment correct?
- Are limb proportions, counts, and placements believable?
- Are spatial layout and scene relationships plausible?

### 7.3 Text quality checks

- Is the workflow `Base Creation`? If yes, evaluate text quality separately.
- Is the workflow `Edit Model`? If yes, include text quality under `Structural Integrity`.
- Is there unreadable text in the image?
- If the prompt requested text but the image lacks it, is `can't tell` being used correctly?

### 7.4 Prompt alignment checks

- Are all prompt elements present?
- Does the scene truly match the request, rather than only approximately matching it?
- Is there clear evidence for the requested style?
- For `Low poly`, are polygon facets actually visible?
- For `Photorealism`, does the image look like a real camera photo?

### 7.5 Additional Edit Model checks

- Did you evaluate Left first, then Right?
- Was each image judged independently by dimension?
- Were change, remove, add, and similar actions performed correctly?
- Were unedited portions preserved?
- Was character consistency maintained?
- Did the edit affect `Instructions` or `Alignment`?

## 8. Common Mistakes to Avoid

- Penalizing text quality under `Structural Integrity` in `Base Creation`.
- Forgetting that text quality belongs under `Structural Integrity` in `Edit Model`.
- Evaluating only thumbnails instead of expanding images to inspect faces, hands, eyes, and limbs.
- Treating clear structural errors as `minor`.
- Forcing apparent ethnicity or gender judgments in group images where even one face is not visible.
- Mistaking background blur for full-image blur.
- Treating a simplified style as `Low poly` without checking for polygon facets.
- Combining Left and Right image judgments instead of evaluating them separately.
- Ignoring specific edit actions in the Edit Model prompt.
- Being misled by known page errors, duplicated pages, or missing text in the guide.
