# Audio Edit Types

RQOAE evaluates five types of music audio edits. Each type has different evaluation focus areas and common failure modes.

## 1. Intro (Beginning Edit)

**What it is**: An edit applied to the beginning of a music track to create a new starting point.

**Evaluation Focus**:
- Does the audio start smoothly and naturally?
- Is there a proper lead-in or does it sound abruptly dropped in?
- Is there unwanted silence at the very beginning?

**Common Problems (score down)**:
- Starts in the middle of a vocal phrase -> Poor/Awful
- Energy suddenly drops right after the start -> Poor
- Starts at the tail end of a previous section (hearing a leftover ending) -> Poor
- Opening is too abrupt with no ramp-up -> Poor
- Entire intro is silence -> Awful

**Filename Pattern**: `intro_NNNNN_D` where D = edit duration in seconds (e.g., `intro_12345_2` = 2-second intro edit)

---

## 2. Outro (Ending Edit)

**What it is**: An edit applied to the end of a music track to create a new ending point.

**Evaluation Focus**:
- Does the audio end naturally with a proper fadeout or musical resolution?
- Is there a cliff-hang or abrupt cutoff?
- Is there excessive silence padding at the end?

**Common Problems (score down)**:
- Cuts off in the middle of vocals -> Awful
- Energy suddenly rises right before the end -> Poor
- Ends at the start of a new section (feels like it was just about to continue) -> Poor
- Ending is too abrupt with no wind-down -> Poor/Awful
- More than 50% of the outro duration is silence -> Awful

**Filename Pattern**: `outro_NNNNN_D` (e.g., `outro_94_7` = 7-second outro edit)

---

## 3. Bridge (Middle Transition)

**What it is**: An edit that connects two different sections of music, creating a transition in the middle of a track.

**Evaluation Focus**:
- Do the two sections flow together naturally?
- Is the transition smooth or jarring?
- Are vocals preserved across the join point?

**Common Problems (score down)**:
- Two sections are too different in style/energy, causing a jarring jump -> structural problem -> Poor
- Vocals are truncated, warped, or become unintelligible at the join -> vocal problem -> Awful/Poor
- Audible click or pop at the transition point -> Poor
- Tempo or key mismatch between sections -> Poor/Average

**Filename Pattern**: `bridge_NNNNN_...` with time range indicating the transition region

---

## 4. Pre-Extension (Extending Beginning)

**What it is**: An edit that extends the audio before a specific point, adding new musical content at the beginning.

**Evaluation Focus**:
- Does the extended portion sound musically coherent?
- Does it blend naturally into the original content that follows?
- Is the extension musically meaningful (not just repeated silence or noise)?

**Common Problems (score down)**:
- Extended section lacks musical quality -> Poor
- Vocals are truncated or distorted in the extension -> Awful/Poor
- Extension does not match the key/tempo of the following section -> Poor/Average
- Extension is empty silence -> Awful

**Filename Pattern**: `pre_NNNNN_D` (e.g., `pre_42_7` = 7-second pre-extension)

---

## 5. Post-Extension (Extending Ending)

**What it is**: An edit that extends the audio after a specific point, adding new musical content at the end.

**Evaluation Focus**:
- Does the extended portion continue the musical idea naturally?
- Does it blend smoothly from the original content into the extension?
- Does the extension have a proper ending or resolution?

**Common Problems (score down)**:
- Extension sounds unmusical or random -> Poor
- Beat hesitation or drag at the extension start point -> Poor
- Vocals are cut or distorted -> Awful/Poor
- Extension is empty silence -> Awful

**Filename Pattern**: `post_NNNNN_D` (e.g., `post_32_2` = 2-second post-extension); time range like `7.5-to-13.7` indicates edit region

---

## Filename Parsing Guide

Full filename example: `post_00902500-007-000-cfg-6.0-no-ema-7.5-to-13.7_mode_post_extension...`

| Component | Meaning |
|-----------|---------|
| First token (intro/outro/bridge/pre/post) | Edit type |
| `_2_` or `_7_` in name | Edit duration: 2s or 7s |
| `7.5-to-13.7` | Edit region: 7.5s to 13.7s in the audio |
| cfg value | Model configuration parameter (informational) |

## Universal Quality Signals

Regardless of edit type, these always indicate problems:
- Silence/empty audio in the edit region -> Awful
- Vocal truncation at edit boundaries -> Awful/Poor
- Beat drag or rhythmic hesitation -> Poor
- Buzzing, hissing, distortion -> Poor/Average
- Random dissonant sounds -> Poor/Average
- Pops or clicks at edit points -> Poor/Average (severity dependent)
