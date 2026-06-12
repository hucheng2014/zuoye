# RQOAE -- Compact Audio Edit Quality Rules

## Single Dimension: Quality (1-5)

| Score | Label     | Key Indicators                                                  |
|-------|-----------|-----------------------------------------------------------------|
| 1     | Awful     | Intro silence, outro 50%+ silence, abrupt ending, static/low RMS (<0.003), mostly silence (>70%) |
| 2     | Poor      | Beat lag/drag, unnatural transitions, slight oddities, distortion, partial silence (>40%) |
| 3     | Average   | Minor audio issues but acceptable; slight dissonance, small artifacts |
| 4     | Good      | Smooth natural transitions, hard-to-detect edits, music flow intact |
| 5     | Excellent | Seamless, completely undetectable edits, natural musical continuity |

## Edit Types
- **intro**: beginning edit -- smooth lead-in, no mid-vocal start, no energy drop after start
- **outro**: ending edit -- natural fadeout/stop, no cliff-hang, no mid-vocal cut
- **bridge**: middle transition -- two sections connect naturally, no vocal truncation
- **pre-extension**: extending beginning -- musically coherent extension before a point
- **post-extension**: extending ending -- musically coherent extension after a point

## Dual Verification (mandatory)
1. **PANNs** -- audio tagging: top tags should be Music (>0.7 = bonus); Silence (>0.3 = penalty)
2. **CLAP** -- semantic matching: compare audio embedding to quality-level text descriptions
3. **Acoustic features** -- silence ratio, energy jumps, RMS, spectral flatness/centroid/bandwidth

## Acoustic Thresholds

| Feature            | Threshold     | Implication         |
|--------------------|---------------|---------------------|
| silence_ratio >0.7 | mostly silent | Awful (1)           |
| silence_ratio >0.4 | partial silence | Awful-Poor (1-2)  |
| max_energy_jump >0.4 | very abrupt | Awful-Poor (1-2)   |
| max_energy_jump >0.25 | somewhat abrupt | Poor-Average (2-3) |
| rms <0.003         | near silent   | Awful (1)           |
| silence <0.1 & energy >0.02 | normal music | Good+ (4-5) |

## Critical Rules
- Never guess -- download audio and run dual analysis before scoring
- Download failure = cannot rate; do not submit
- PANNs + acoustic features must agree; if CLAP and PANNs diverge >1.5, trust PANNs
- Slider values must match expected scores before submitting
- Broken/unplayable audio -> check "Audio does not load/play" and submit
