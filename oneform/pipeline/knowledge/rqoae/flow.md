# RQOAE -- Operation Flow

## 6-Step Workflow

### Step 1: Read Task Page
- Connect to browser via CDP (`http://browser:9223`, Host: `localhost:9222`)
- WebSocket URL replacement: `ws://localhost:9222` -> `ws://browser:9223`
- Extract: audio elements (src URLs), slider count, button states, body text
- Identify edit type from filename: intro/outro/bridge/pre/post
- Parse edit region from filename (e.g. `7.5-to-13.7` = edit at 7.5s-13.7s)
- Distinguish tutorial examples (audio index 0-31, dataset 212640) from formal questions (index 32-34, dataset 212641)

### Step 2: Simulate Audio Playback
- Trigger `play()` on each `<audio>` element via CDP
- Wait for actual duration + 1.5s safety buffer per audio
- Backend monitors playback events -- skipping triggers risk controls
- If audio fails to load: check "Audio does not load/play" option and submit immediately
- Never skip this step -- instant submission without playback will be flagged

### Step 3: Download Audio Files
- Download formal audio via browser `fetch()` with `credentials: 'include'`
- Transfer audio data as base64 through CDP evaluation
- Validate each download: status 200, content-type audio, RIFF header, size > few hundred bytes
- Save to `/tmp/audio_{label}.wav`
- If download fails or returns HTML: stop, do not rate

### Step 4: Dual Verification (PANNs + Acoustic Features)
- **PANNs audio tagging**: load at 32kHz, run inference, check top-10 tags
  - Music tag >0.7 = strong musical content (bonus)
  - Silence/Static/Noise tags = quality concern (penalty)
- **Acoustic features** via librosa:
  - RMS, silence ratio, zero-crossing rate, spectral flatness, centroid, bandwidth
  - Energy envelope: compute RMS envelope, detect max energy jump
- **CLAP semantic matching** (optional second model):
  - Compare audio embedding to quality-level text descriptions
  - Softmax over similarity scores to get quality distribution
- **Combined score**: average CLAP + PANNs scores; if divergence >1.5, trust PANNs
- Map combined score to rating: <=1.5 Awful, <=2.5 Poor, <=3.5 Average, <=4.5 Good, else Excellent

### Step 5: Fill Sliders (1-5 Scale)
- Slider position mapping: 1=0%, 2=25%, 3=50%, 4=75%, 5=100%
- Identify correct sliders: total slider count minus formal question count = starting offset
- Scroll each slider into view, compute click coordinates from rail bounding rect
- Dispatch mouse events: mouseMoved -> mousePressed -> mouseReleased
- After setting all sliders, read back `aria-valuenow` attributes and verify match
- If mismatch: stop immediately, do not submit

### Step 6: Submit with Quality Checks
- Read all slider values one final time
- Compare tail values against expected ratings array
- If any mismatch: abort, do not submit
- Click "Submit Rating" button (must not be disabled)
- Wait 3s, read page tail text to confirm success
- Success indicators: "No more surveys" or new question loaded

## Page Structure

| Section             | Audio Index | Dataset  | Purpose                     |
|---------------------|-------------|----------|-----------------------------|
| Tutorial examples   | 0-31        | 212640   | Reference with explanations |
| Formal questions    | 32-34       | 212641   | Actual rating targets       |

## Iron Rules
- No guessing -- every rating must come from downloaded + analyzed audio
- No auto-scoring scripts with hardcoded rules -- each audio requires independent analysis
- Download failure = cannot rate = do not submit
- Dual verification mandatory: PANNs + acoustic features
- Pre-submit slider verification mandatory: values must equal expected
- Broken audio -> use "Audio does not load/play" checkbox, not a guess score
- All commands run inside container: `docker exec -i oneform-agent python3 - <<'PY' ... PY`
