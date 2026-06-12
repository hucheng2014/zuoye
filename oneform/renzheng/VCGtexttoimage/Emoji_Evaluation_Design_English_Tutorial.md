# Emoji Evaluation Design — English Tutorial

## 1. Task Goal

This task is part of the Visual Content Generation evaluation program. The overall goal is to judge whether machine-generated content is relevant to an input request or prompt. The generated products may include text, sketches, emojis, and more; this specific project evaluates **generated emoji images**.

In this task, you will see:

- **Input Prompt**;
- **Output Image(s)**;
- **Reference Emojis** — Apple’s existing emojis that are relevant to a character or object mentioned in the prompt, such as a pink heart, tears of joy, or folded hands. Some prompts may not have reference emojis.

Your job is to evaluate the quality of the output emojis in relation to the input prompt, using the general **Image Evaluation Guidelines** together with the project-specific rules summarized here.

---

## 2. Flags

Apply the following flags when applicable. Use the general Image Evaluation Guidelines for the full definitions.

| Flag | When to consider it |
|---|---|
| **Inappropriate** | The output contains inappropriate content. |
| **Sensitive** | The output involves sensitive topics, sensitive groups, or content that requires caution. |
| **Stereotype** | The output reinforces stereotypes or presents group characteristics in an inappropriate way. |

> Flags are separate from quality grading. An image can be structurally strong and prompt-aligned while still requiring a content flag.

---

## 3. Grading Dimensions

Evaluate each output emoji on the following dimensions:

1. **Structural Integrity**
2. **Input/Output Alignment**
   - **Text-to-Image Alignment**
   - **Image-to-Image Alignment**, when reference images or reference emojis are relevant

---

## 4. Structural Integrity

### 4.1 What to evaluate

Structural Integrity measures whether the emoji is visually complete, natural, and free from obvious defects. Check whether:

- there are visible distortions, artifacts, broken areas, or incorrect blending;
- body/object parts are reasonable, such as hands, feet, tails, faces, and proportions;
- object shapes make sense, such as a shrimp not having claws and a cat face not being severely distorted;
- the output matches the clean, recognizable visual language of Apple-style emojis;
- segmentation edges are clean, with no missing chunks or leftover background artifacts.

### 4.2 Issue levels

- **No Structural Integrity Issue**: No visible defects; the subject is clear, natural, and usable as an emoji.
- **Minor Structural Integrity Issue**: A small flaw is present but does not seriously affect recognition or overall quality, such as minor hand artifacts.
- **Noticeable Structural Integrity Issue**: A visible defect affects the appearance or realism, such as a distorted cat face or an incomplete ice-cream cone.
- **Severe Structural Integrity Issue**: A major error makes the subject or structure fundamentally wrong, such as a shrimp rendered as a worm or a shrimp with impossible claws.

---

## 5. Input/Output Alignment

### 5.1 What to evaluate

Input/Output Alignment measures whether the emoji satisfies the prompt. Check whether the output includes:

- the correct main subject;
- all key objects mentioned in the prompt;
- the required action;
- the required scene or context;
- important attributes such as color, hats, balloons, surfboards, forests, sunny weather, etc.;
- required body scope, quantity, or relationships, such as “full body” or “balloon tied to tail.”

### 5.2 Alignment levels

| Rating | Meaning |
|---|---|
| **High** | The output accurately represents the core requirements of the prompt. |
| **Moderate** | The output is related, but a key element is weak, missing, or only partially represented. |
| **Low** | The output is clearly misaligned, has the wrong subject, or misses crucial context. |

---

## 6. Ranking Scale

Rank output images based on the grades assigned for:

- Structural Integrity;
- Text-to-Image Alignment;
- Image-to-Image Alignment;
- applicable flags;
- overall usability as a clear, natural emoji.

In general, prefer outputs that:

1. have no serious content risks;
2. are structurally intact;
3. are highly aligned with the prompt;
4. resemble Apple-style emoji design;
5. remain simple, readable, and recognizable at emoji size.

---

## 7. Comment Requirement

Provide a concise, specific, and well-structured comment that explains your decision-making process to the engineers.

A useful comment often includes:

1. Structural Integrity observations;
2. prompt alignment observations;
3. any flags or special concerns;
4. the reason for the final grade or ranking.

Example wording:

- “The emoji has no visible structural defects and clearly depicts the requested subject, so alignment is High.”
- “The output is structurally acceptable, but it misses the bamboo forest context, so alignment is Moderate/Low.”
- “The hand contains minor artifacts, but the prompt is still clearly represented.”

---

## 8. Special Note on Background Segmentation

Some evaluation projects test how well the object or person is separated from the background. In these cases, the grading UI may show the emoji on a **solid green background** to help reveal:

- incorrectly carved edges;
- leftover background artifacts;
- missing parts of the subject;
- unnatural transparent areas;
- regions that were wrongly removed during segmentation.

Rules:

- Treat the solid green background the same as a white background.
- When grading input-output alignment, still consider whether elements mentioned in the prompt, such as beach, forest, or city, are missing from the output emoji.
- Do not treat the green background itself as the intended scene. It is only a UI aid for checking segmentation.

---

## 9. Example Summary

### 9.1 “An emoji of rainbow flag heart shaped”

- **Structural Integrity**: No Structural Integrity Issue.
- **Reason**: The emoji has no visible defects, accurately depicts the user’s intention, and matches Apple emoji style.
- **Alignment**: High.

### 9.2 “yellow shrimp”

| Case | Structural Integrity | Alignment | Reason |
|---|---|---|---|
| Shrimp has claws and only shows the head | Severe | Low | Shrimp normally implies a full body, and claws are an artifact. |
| Output looks like a worm, not a shrimp | Severe | Low | The subject category is wrong. |
| Output is a snake-shrimp fusion | Noticeable | Low | The structure deviates from an accurate shrimp. |

### 9.3 “An emoji of a cat wearing sunglasses”

- If the right side of the cat face is prominently distorted: **Noticeable Structural Integrity Issue**, but alignment can still be **High** if it clearly shows a cat wearing sunglasses.
- Versions without visible defects: **No Structural Integrity Issue** and **High** alignment.

### 9.4 “A giant panda practicing Tai Chi in a serene bamboo forest”

| Case | Structural Integrity | Alignment | Reason |
|---|---|---|---|
| Panda practices Tai Chi but lacks the bamboo forest | No issue | Low | The crucial “serene bamboo forest” context is missing. |
| Panda practices Tai Chi and holds bamboo, but no full forest atmosphere | No issue | Moderate | The bamboo idea is partially represented, but the forest is not complete. |
| Panda, Tai Chi, and bamboo forest context are all clear | No issue | High | The key subject, action, and scene are satisfied. |

### 9.5 “a blob-face wearing a Christmas hat and holding balloons”

| Case | Structural Integrity | Alignment | Reason |
|---|---|---|---|
| Hugging blob-face holds balloons but does not wear a Christmas hat | Noticeable | Moderate | Balloons are present, but the hat is missing. |
| Christmas hat is almost entirely blocked by a purple balloon | Noticeable | Moderate | The hat is too weak or nearly invisible. |
| Blob-face, Christmas hat, and balloons are all clear | No issue | High | The prompt is accurately depicted. |

### 9.6 “a dog with full body surfing on the sea on a sunny day”

| Case | Structural Integrity | Alignment | Reason |
|---|---|---|---|
| Only a dog face is shown | No issue | Low | It lacks full body, surfing, sea, and sunny-day context. |
| Dog with a surfboard, loosely related to surfing | No issue | Moderate | It is related, but not fully aligned with the prompt. |
| Dog surfs on the sea, but sunny day is not pronounced | Minor issue | Moderate | The main action is present, but the weather context is weak. |
| Full-body dog surfing on the sea on a sunny day | No issue | High | The prompt is accurately represented. |

### 9.7 Additional examples

| Prompt | Structural Integrity | Alignment | Note |
|---|---|---|---|
| a kid wearing a backpack | No issue | High | Kid and backpack are clear. |
| a boy holding a balloon | No issue | High | The boy-balloon relationship is clear. |
| a man holding a kitten | Minor issue | High | Hands have some artifacts, but the prompt is clear. |
| a rainbow ice-cream | Noticeable | Moderate | The cone is incomplete; prompt asks for one ice cream, but output shows two. |
| bowl of oatmeal with blueberries | No issue | High | Oatmeal and blueberries are clear. |
| a bathroom with a shower and a toilet | Minor issue | Moderate | The left toilet is misshaped, and two toilets appear; the left one would be better as a bathtub/shower element. |
| a bicycle with a basket full of flowers | No issue | High | Bicycle and flower basket are clear. |
| a candle on a shelf | No issue | High | Candle and shelf are clear. |
| person wearing a bowler hat | No issue | High | Person and bowler hat are clear. |
| a person giving a presentation | No issue | High | Presentation action/context is clear. |

---

## 10. Quick Checklist

Before submitting, confirm that:

- [ ] You read the prompt before judging the output.
- [ ] You considered the reference emojis without requiring the output to copy them exactly.
- [ ] You checked for structural defects, artifacts, and incorrect parts.
- [ ] You verified that key prompt objects, actions, scenes, and attributes are represented.
- [ ] If a green background is shown, you treated it as a segmentation aid rather than the intended scene.
- [ ] You applied Inappropriate / Sensitive / Stereotype flags when applicable.
- [ ] Your comment is concise, specific, and explains the grade or ranking.
