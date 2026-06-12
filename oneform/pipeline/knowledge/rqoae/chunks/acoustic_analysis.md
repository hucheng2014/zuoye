# Acoustic Analysis & Models

## Dual Verification Architecture

Every audio edit must be analyzed by at least two independent methods before scoring. Never rate based on a single signal.

### Model 1: PANNs (Pretrained Audio Neural Networks)

**Purpose**: Audio event tagging -- identifies what sounds are present in the edit region.

**Setup**:
- Model: Cnn14_mAP=0.431.pth (path: `/root/panns_data/`)
- Labels: class_labels_indices.csv
- Sample rate: 32kHz
- Input: mono audio, numpy array with batch dimension

**Usage**:
```
at = AudioTagging(checkpoint_path=None, device='cpu')
y, sr = librosa.load(path, sr=32000, mono=True)
tags, _ = at.inference(y[np.newaxis, :])
```

**Interpretation**:
| Top Tag | Confidence | Implication |
|---------|------------|-------------|
| Music | > 0.7 | Strong musical content -> bonus toward Good/Excellent |
| Silence | > 0.3 | Significant silence present -> penalty, likely Awful/Poor |
| Static / White noise / Noise | high | Non-musical content in edit region -> penalty |
| Speech / Singing | present | Vocal content -- check for truncation at edit boundaries |
| Explosion / Siren | present | Anomalous non-music content -> likely Awful |

### Model 2: CLAP (Contrastive Language-Audio Pretraining)

**Purpose**: Semantic matching -- compares audio embedding to text descriptions of quality levels.

**Setup**:
- Model: music_audioset_epoch_15_esc_90.14.pt (path: `/app/RQOAE/models/`)
- Architecture: HTSAT-base, fusion disabled

**Usage**:
- Generate audio embedding from the edit region
- Compare against quality-level text descriptions (e.g., "awful intro with complete silence", "excellent outro with seamless transition")
- Softmax over similarity scores produces a quality probability distribution
- Weighted average against score map [1, 1, 2, 2, 3, 4, 5] gives CLAP score

**Important**: CLAP analyzes the entire audio file by default. For accurate edit evaluation, crop the audio to the edit region before analysis.

### Combined Scoring

1. Compute CLAP score (1-5 float) and PANNs/acoustic score (1-5 float)
2. Combined = average of both scores
3. **Divergence rule**: if |CLAP - PANNs| > 1.5, trust the PANNs/acoustic score (more reliable for technical defects)
4. Map combined score to label: <=1.5 Awful, <=2.5 Poor, <=3.5 Average, <=4.5 Good, else Excellent

---

## Acoustic Feature Analysis

Computed via librosa on the edit region (not the full track).

### Feature Definitions

| Feature | Computation | What It Measures |
|---------|-------------|------------------|
| **RMS** | sqrt(mean(y^2)) | Overall loudness/energy level |
| **silence_ratio** | mean(abs(y) < 0.01) | Proportion of near-silent samples |
| **max_energy_jump** | max(abs(diff(rms_envelope))) | Largest sudden energy change (abruptness) |
| **avg_energy** | mean(rms_envelope) | Average energy across edit region |
| **zero_crossing_rate** | mean(zcr) | Rate of signal sign changes (noise indicator) |
| **spectral_flatness** | mean(flatness) | How noise-like vs tonal the spectrum is |
| **spectral_centroid** | mean(centroid) | Brightness of the sound |
| **spectral_bandwidth** | mean(bandwidth) | Spread of the frequency spectrum |

### Threshold Table

| Feature | Threshold | Issue Detected | Score Impact |
|---------|-----------|----------------|--------------|
| silence_ratio > 0.7 | mostly_silence | Nearly all edit region is quiet | Awful (1) |
| silence_ratio > 0.4 | partial_silence | Large portion is quiet | Awful-Poor (1-2) |
| silence_ratio < 0.1 | normal | Acceptable silence level | Neutral/Good |
| max_energy_jump > 0.4 | very_abrupt | Jarring sudden volume change | Awful-Poor (1-2) |
| max_energy_jump > 0.25 | somewhat_abrupt | Noticeable but not extreme | Poor-Average (2-3) |
| max_energy_jump < 0.25 | smooth | Natural energy flow | Neutral/Good |
| rms < 0.003 | near_silent | Audio is essentially inaudible | Awful (1) |
| rms > 0.02 | audible | Normal listening level | Neutral |
| avg_energy > 0.02 + silence < 0.1 | normal_music | Healthy musical content | Good+ (4-5) |

### Score Derivation Logic

```
Base score = 3.5
If mostly_silence OR near_silent -> 1.0
If partial_silence -> 1.5
If very_abrupt -> 1.5
If somewhat_abrupt -> 2.5
If no issues AND avg_energy > 0.02 AND silence < 0.1 -> 4.0
```

---

## Analysis Workflow

1. Load audio at native sample rate (librosa, mono)
2. Extract edit region using parsed start/end timestamps
3. Compute all acoustic features on edit region
4. Run PANNs inference on edit region (at 32kHz)
5. Run CLAP inference on edit region (optional, if model available)
6. Detect issues from acoustic thresholds
7. Compute PANNs score from issues + features
8. Compute CLAP score from semantic similarity
9. Combine scores (average, with divergence override)
10. Map to 1-5 integer rating
