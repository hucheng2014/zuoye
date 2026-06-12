# Structural Integrity — Complete Rules

## Purpose
Detect anatomical, structural, or compositional errors in the generated image.

## What to Inspect
- Human anatomy: face, eyes, nose, mouth, ears, fingers, hands, limbs, joints, proportions
- Animal anatomy: limbs, tails, ears, eyes, body proportions
- Object structure: expected components, physical logic, connections
- Scene logic: floating objects, merged elements, disconnected parts
- Unintended artifacts: objects that don't logically belong

## Diagnostic Questions
1. Does the subject have an incorrect number of parts? (humans: eyes, hands, legs; animals: limbs; objects: components)
2. Are proportions anatomically/structurally implausible given the prompt?
3. Missing or extra body parts/components not justified by prompt?
4. Parts merged, fused, floating, or disconnected?
5. Visible distortions — twisted, melted, malformed?
6. Unintended artifacts — objects that don't logically belong?
7. For stylized art: structural issues relative to the style's internal logic (NOT real-world realism)?

## Severity Scale

### Severe
- Immediately apparent; breaks basic form of subject
- Examples:
  - Completely distorted face
  - Extra or missing fingers (ALWAYS Severe)
  - Missing key limbs
  - Merged humans/animals/objects
  - Unrecognizable subject
  - Melted hands lacking finger definition
  - Duplicated facial features
  - Severely elongated head
  - Person with no facial features at all

### Noticeable
- Visible without zooming; breaks flow but image remains interpretable
- **UPGRADE RULE:** Eye/nose/mouth/ear issues → minimum Noticeable (even if subtle)
- Examples:
  - Twisted fingers (not extra/missing)
  - Eye asymmetry or shape issues
  - Floating/unrealistic object positioning (e.g., floating hanger, floating weight plate)
  - Two steering wheels on a vehicle
  - Undefined/unclear object connections
  - Hands not properly holding objects
  - Clothing protrusions/anomalies
  - Swimmer's foot defect visible on zoom
  - Abnormal thumb shape

### Minor
- Only found on close inspection; not obvious at first glance
- Examples:
  - Slight proportion issues in non-focal areas
  - Minor background distortions
  - Small decorative element flaws (tower ornaments, statues)
  - Vase handle slightly detached
  - Small chair missing legs but not visibly obvious
  - Slight merged fingers barely visible

### No Issues
- All diagnostic questions answered "no"

## Critical Decision Rules

| Situation | Rating |
|-----------|--------|
| Incorrect finger count (extra or missing) | **Severe** — always |
| Face completely distorted | **Severe** |
| Missing key limbs | **Severe** |
| Eye/nose/mouth/ear issues (any) | **Noticeable** minimum |
| Floating/physically impossible positioning | **Noticeable** |
| Multiple defects present | Rate by **highest severity** |
| Main subject defect vs background defect | Main subject rated **more harshly** |
| Stylized art (cartoon/anime/abstract) | Only penalize if breaks **style's own logic** |
| Prompt requested unusual structure (3-headed dog) | **Not a defect** |

## DO NOT confuse with other dimensions:
- Blurry face → Visual Quality (not SI)
- Missing prompt element → Alignment (not SI)
- Text distortion → Text Quality (not SI, in Base Creation)
