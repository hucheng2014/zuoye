# Scoring Rubric -- 5-Level Quality Rating

## 1 -- Awful
The edit has severe, immediately obvious defects that make the audio unlistenable or broken.

### Identifying Characteristics
- **Silence**: entire intro is silent; outro has 50%+ silence; extended section is empty
- **Abrupt endings**: audio cuts off mid-note or mid-phrase without any fadeout
- **Static/noise**: edit region contains only static, white noise, or hiss instead of music
- **Near-silent**: RMS < 0.003, audio is essentially inaudible
- **Vocal truncation**: vocals are cut off mid-word at an edit boundary

### Tutorial Examples
- Intro 2s: entire 2 seconds is silence -> Awful
- Outro 7s: 5 of 7 seconds are silence -> Awful
- Outro 2s: no content added, just abrupt stop -> Awful

### Acoustic Signatures
- silence_ratio > 0.7 (mostly silence)
- rms < 0.003 (near silent)
- max_energy_jump > 0.4 (very abrupt transition)

---

## 2 -- Poor
The edit has noticeable problems that clearly indicate artificial manipulation.

### Identifying Characteristics
- **Beat drag/lag**: rhythm stumbles or hesitates at the edit point
- **Unnatural transitions**: the join between sections sounds forced or mechanical
- **Slight oddities**: clicking, popping, or brief artifacts at edit boundaries
- **Distortion**: audio quality degrades noticeably in the edited region
- **Rushed feeling**: outro feels hurried despite being long enough in duration

### Tutorial Examples
- Outro 2s: last beat has a dragging sensation -> Poor
- Post-Extension 6.2s: audible beat hesitation at 7.5s mark -> Poor
- Outro 7s: 7 seconds is adequate length but feels rushed -> Poor

### Acoustic Signatures
- silence_ratio 0.4-0.7 (partial silence)
- max_energy_jump 0.25-0.4 (somewhat abrupt)
- PANNs detects anomalous non-music tags in edit region

---

## 3 -- Average
The edit has minor imperfections that are noticeable on careful listening but do not ruin the experience.

### Identifying Characteristics
- **Slight beat drag**: rhythm wobbles slightly but recovers
- **Minor dissonance**: brief moments of harmonic clash that resolve quickly
- **Small artifacts**: very faint clicks or pops, barely perceptible
- **Acceptable but not seamless**: a trained ear can detect the edit point
- **Random inharmonic sounds**: occasional odd tones that do not persist

### When to Use
- The edit is functional and listenable but clearly imperfect
- You can tell something was edited but it does not bother you much
- Minor audio anomalies present but not severe

### Acoustic Signatures
- silence_ratio 0.1-0.4, moderate energy, no extreme jumps
- Some anomalous spectral features but not dominant

---

## 4 -- Good
The edit is smooth and natural-sounding. Only very careful, repeated listening reveals the edit.

### Identifying Characteristics
- **Smooth transitions**: energy flows naturally across edit boundaries
- **Musical continuity**: key, tempo, and rhythm are maintained
- **Nearly invisible edits**: the join point is very hard to detect
- **Preserved musicality**: the edited section sounds like it belongs
- **No artifacts**: no clicks, pops, distortion, or unnatural sounds

### Tutorial Examples
- Transitions are smooth and natural-sounding
- Almost impossible to hear where the edit was made
- Musical quality and flow are fully preserved

### Acoustic Signatures
- silence_ratio < 0.1, avg_energy > 0.02
- No energy jumps above 0.25
- PANNs top tag: Music with confidence > 0.7

---

## 5 -- Excellent
The edit is perfect and completely undetectable. The audio sounds as if it was never edited.

### Identifying Characteristics
- **Seamless**: absolutely no audible indication of editing
- **Perfect musical flow**: the music sounds entirely natural and continuous
- **Undetectable**: even repeated careful listening cannot find the edit point
- **Studio quality**: the edited audio is indistinguishable from the original recording

### Tutorial Examples
- Perfectly seamless edit
- Cannot tell it was edited at all
- Music flows as if it were the original recording

### Acoustic Signatures
- Very low silence ratio, stable energy envelope
- Consistent spectral features across edit boundary
- PANNs: strong Music tag, no anomalous tags
- CLAP: highest similarity to "excellent seamless musical transition" description

---

## Decision Shortcuts

| Symptom | Score |
|---------|-------|
| All/mostly silence in edit region | 1 |
| Abrupt cut mid-vocal or mid-note | 1 |
| RMS < 0.003 | 1 |
| Beat drag, audible hesitation | 2 |
| Distortion or clicking at edit point | 2 |
| Minor imperfections, still listenable | 3 |
| Smooth, natural, hard to detect | 4 |
| Perfect, undetectable | 5 |
