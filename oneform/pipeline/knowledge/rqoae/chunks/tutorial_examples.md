# Tutorial Examples & Page Structure

## Page Layout

The RQOAE task page on tryrating.com contains two distinct sections:

### Tutorial Section (Audio Index 0-31)
- **Dataset**: 212640
- **Purpose**: Reference examples with explanatory text showing correct ratings
- **Content**: Pre-rated audio samples with written justifications for each score
- **Count**: 32 audio elements (index 0 through 31)
- **Has sliders**: Yes, but these are pre-filled tutorial demonstrations

### Formal Questions (Audio Index 32-34)
- **Dataset**: 212641
- **Purpose**: Actual rating targets that you must score
- **Content**: Audio samples with sliders, no pre-filled ratings or explanations
- **Count**: 3 audio elements (index 32 through 34)
- **Has sliders**: Yes, these must be set to your ratings

### Example Formal Questions
| Audio Index | Filename Pattern | Edit Type | Duration |
|-------------|-----------------|-----------|----------|
| 32 | outro_94_7 | Outro | 7s edit |
| 33 | pre_42_7 | Pre-Extension | 7s edit |
| 34 | post_32_2 | Post-Extension | 2s edit |

*Note: actual filenames and edit types vary per task instance.*

---

## Using Tutorial Examples for Calibration

The tutorial examples serve as your scoring calibration reference. Before rating formal questions:

### Step 1: Study the Tutorial Ratings
- Read the explanatory text for each tutorial example
- Note which audio characteristics map to which scores
- Pay attention to the reasoning, not just the final score

### Step 2: Calibrate Your Thresholds
- Awful examples establish your floor: what does a score-1 audio actually sound like?
- Excellent examples establish your ceiling: what does a perfect edit sound like?
- Average examples define the middle: what level of imperfection is "acceptable"?

### Step 3: Cross-Reference with Analysis
- Run your acoustic analysis on tutorial audio to see what feature values correspond to known ratings
- This helps validate that your PANNs/acoustic thresholds are calibrated correctly

---

## Tutorial Rating Patterns (from TUTORIAL_NOTES.md)

### Awful (1) Patterns
- Intro with entire duration as silence
- Outro where 50%+ of duration is silence
- Outro with nothing added, just abrupt stop
- Key acoustic signature: silence_ratio > 0.7, rms < 0.003

### Poor (2) Patterns
- Outro with dragging sensation on last beat
- Post-extension with audible beat hesitation at transition point
- Outro that feels rushed despite adequate duration
- Key acoustic signature: max_energy_jump 0.25-0.4, partial silence

### Average (3) Patterns
- Beat drag is present but not very obvious
- Slight sound anomalies that do not severely impact listening
- Some random dissonant sounds but still acceptable
- Key: issues exist but are minor and non-persistent

### Good (4) Patterns
- Smooth, natural-sounding transitions
- Edit point is very difficult to detect
- Musical quality and flow are preserved
- Key: silence < 0.1, stable energy, no jumps > 0.25

### Excellent (5) Patterns
- Perfectly seamless edit
- Impossible to tell the audio was edited
- Music flows as if it were the original recording
- Key: all features in healthy range, strong Music tag from PANNs

---

## Slider Identification

When setting ratings, the formal question sliders are the **last N sliders** on the page, where N = number of formal questions.

**Calculation**:
```
total_sliders = document.querySelectorAll(".rc-slider").length
formal_count = len(ratings)  # typically 3-10 depending on task
start_index = total_sliders - formal_count
```

Each slider maps: 1=0%, 2=25%, 3=50%, 4=75%, 5=100% of the rail width.

**Verification**: after setting, read back `aria-valuenow` from all `.rc-slider-handle` elements and confirm the tail values match your expected ratings array. Any mismatch = do not submit.

---

## Buttons

| Button | Action | When to Use |
|--------|--------|-------------|
| Submit Rating | Submit all ratings | After all sliders verified |
| Release Survey | Abandon current task | Only if task is truly broken |
| Audio does not load/play | Mark broken audio | When audio genuinely cannot play |
