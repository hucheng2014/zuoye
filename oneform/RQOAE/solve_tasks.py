import json
import urllib.request
import re
import os
import sys
import base64
import time
import fcntl
import numpy as np
import librosa
from websocket import create_connection

DONE_WAIT_SEC = -1.0
IDLE_EXIT_AFTER = 5
LOCK_PATH = "/tmp/rqoae_solve.lock"

# Load models config
CLAP_MODEL = "/app/RQOAE/models/music_audioset_epoch_15_esc_90.14.pt"
PANNS_MODEL = "/root/panns_data/Cnn14_mAP=0.431.pth"
WHISPER_MODEL = "/app/RQOAE/models/faster-whisper-large-v3"
CDP_ENDPOINT = "http://browser:9223"
POST_SUBMIT_WAIT_SEC = 90.0
# Page estimate ~2 min for MUSHRA; pad modestly if finished suspiciously fast
BATCH_MIN_DURATION_SEC = 90.0
BATCH_TARGET_BY_TYPE = {
    "SFX-MUSHRA-Style": 110.0,
    "Transition quality": 90.0,
}
MAX_PADDING_SEC = 40.0
SLIDER_SET_SLEEP_SEC = 0.35

# Global model instances for optimization
_clap_model = None
_panns_model = None
_whisper_model = None

def get_clap_model():
    global _clap_model
    if _clap_model is None:
        import laion_clap
        print("Loading CLAP model globally (once)...")
        _clap_model = laion_clap.CLAP_Module(enable_fusion=False, amodel='HTSAT-base')
        _clap_model.load_ckpt(ckpt=CLAP_MODEL)
        print("CLAP model loaded successfully.")
    return _clap_model

def get_panns_model():
    global _panns_model
    if _panns_model is None:
        from panns_inference import AudioTagging
        print("Loading PANNs model globally (once)...")
        _panns_model = AudioTagging(checkpoint_path=PANNS_MODEL, device='cpu')
        print("PANNs model loaded successfully.")
    return _panns_model

def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        print("Loading Whisper ASR model globally (once)...")
        _whisper_model = WhisperModel(WHISPER_MODEL, device="cpu")
        print("Whisper ASR model loaded successfully.")
    return _whisper_model

def get_ws_url():
    req = urllib.request.Request(f"{CDP_ENDPOINT}/json/list")
    req.add_header("Host", "localhost:9222")
    resp = urllib.request.urlopen(req, timeout=5)
    pages = json.loads(resp.read())
    for page in pages:
        if page.get("type") == "page" and "tryrating.com" in page.get("url", ""):
            return page["webSocketDebuggerUrl"].replace("ws://localhost:9222", "ws://browser:9223")
    for page in pages:
        if page.get("type") == "page":
            return page["webSocketDebuggerUrl"].replace("ws://localhost:9222", "ws://browser:9223")
    return pages[0]["webSocketDebuggerUrl"].replace("ws://localhost:9222", "ws://browser:9223")


def run_js(ws, js):
    ws.send(json.dumps({"id": 1, "method": "Runtime.enable", "params": {}}))
    ws.recv()
    ws.send(json.dumps({"id": 2, "method": "Runtime.evaluate", "params": {"expression": js, "returnByValue": True, "awaitPromise": True}}))
    while True:
        raw = ws.recv()
        data = json.loads(raw)
        if data.get("id") == 2:
            result = data.get("result", {})
            if "exceptionDetails" in result:
                print("JS Exception:", result["exceptionDetails"])
            return result.get("result", {}).get("value", "")

def normalize_audio_url(url):
    if "api.tryrating.com/v1/catalog/catalog-items/" in url:
        return url.replace(
            "https://api.tryrating.com/v1/catalog/catalog-items/",
            "https://www.tryrating.com/api/catalog/datasets/",
        )
    return url


def download_audio_js(ws, url, output_path):
    url = normalize_audio_url(url)
    js = f"""(async () => {{
        try {{
            const resp = await fetch("{url}", {{ credentials: "include" }});
            if (!resp.ok) return "ERROR:HTTP " + resp.status;
            const blob = await resp.blob();
            if (blob.size < 1000) return "ERROR:empty blob size=" + blob.size;
            const reader = new FileReader();
            return new Promise((resolve) => {{
                reader.onloadend = () => resolve(reader.result.split(',')[1]);
                reader.readAsDataURL(blob);
            }});
        }} catch(e) {{
            return 'ERROR:' + e.message;
        }}
    }})()"""
    val = run_js(ws, js)
    if not val or val.startswith("ERROR:"):
        raise Exception(f"Download failed: {val}")
    data = base64.b64decode(val)
    if len(data) < 1000:
        raise Exception(f"Downloaded empty or invalid audio ({len(data)} bytes)")
    with open(output_path, 'wb') as f:
        f.write(data)
    print(f"Downloaded {len(data)} bytes to {output_path}")

def analyze_with_panns(audio_path, edit_start, edit_end, sr=32000):
    y, _ = librosa.load(audio_path, sr=sr, mono=True)
    duration = len(y) / sr

    start_sample = max(0, int(edit_start * sr))
    end_sample = min(len(y), int(edit_end * sr))
    edit_region = y[start_sample:end_sample]

    if len(edit_region) < sr * 0.1:
        return {"score": 1.0, "issues": ["edit_region_too_short"], "acoustic": {}}

    at = get_panns_model()
    edit_clip = edit_region[np.newaxis, :]
    tags, _ = at.inference(edit_clip)

    rms = float(np.sqrt(np.mean(edit_region**2)))
    silence_ratio = float(np.sum(np.abs(edit_region) < 0.01)) / len(edit_region)

    hop = 512
    rms_env = librosa.feature.rms(y=edit_region, hop_length=hop)[0]
    max_jump = float(np.max(np.abs(np.diff(rms_env)))) if len(rms_env) > 2 else 0.0
    avg_energy = float(np.mean(rms_env))

    issues = []
    if silence_ratio > 0.7:
        issues.append("mostly_silence")
    elif silence_ratio > 0.4:
        issues.append("partial_silence")
    if max_jump > 0.4:
        issues.append("very_abrupt")
    elif max_jump > 0.25:
        issues.append("somewhat_abrupt")
    if rms < 0.003:
        issues.append("near_silent")

    score = 3.5
    if "mostly_silence" in issues or "near_silent" in issues:
        score = 1.0
    elif "partial_silence" in issues:
        score = 1.5
    elif "very_abrupt" in issues:
        score = 1.5
    elif "somewhat_abrupt" in issues:
        score = 2.5
    elif len(issues) == 0 and avg_energy > 0.02 and silence_ratio < 0.1:
        score = 4.0
    return {
        "score": round(score, 2),
        "issues": issues,
        "acoustic": {
            "rms": round(rms, 4),
            "silence_ratio": round(silence_ratio, 3),
            "max_energy_jump": round(max_jump, 4),
            "avg_energy": round(avg_energy, 4),
        },
        "duration": round(duration, 2),
    }

def analyze_with_clap(audio_path, task_type):
    model = get_clap_model()

    quality_texts = [
        f"awful {task_type} with complete silence and empty audio",
        f"awful {task_type} with very abrupt cut and harsh distortion",
        f"poor {task_type} with unnatural timing and jarring transition",
        f"poor {task_type} with slight audio artifacts and clicks",
        f"average {task_type} with minor imperfections but passable quality",
        f"good {task_type} with smooth natural sounding music",
        f"excellent {task_type} with perfect seamless musical transition",
    ]
    score_map = [1.0, 1.0, 2.0, 2.0, 3.0, 4.0, 5.0]

    audio_embed = model.get_audio_embedding_from_filelist([audio_path])
    text_embed = model.get_text_embedding(quality_texts)
    similarities = (audio_embed @ text_embed.T).squeeze()

    exp_sim = np.exp(similarities - np.max(similarities))
    probs = exp_sim / exp_sim.sum()

    clap_score = float(np.dot(probs, score_map))
    best_idx = int(np.argmax(similarities))

    return {
        "score": round(clap_score, 2),
        "best_match": quality_texts[best_idx],
        "confidence": round(float(probs[best_idx]), 3),
    }

def analyze_with_whisper(audio_path):
    y, sr = librosa.load(audio_path, sr=16000, mono=True)
    duration = len(y) / sr
    
    t_center = 10.0
    t_start = max(0.0, t_center - 1.5)
    t_end = min(duration, t_center + 1.5)
    
    start_sample = int(t_start * sr)
    end_sample = int(t_end * sr)
    clip = y[start_sample:end_sample]
    
    if len(clip) < sr * 0.5:
        return {"is_cutoff": False, "lyrics": "", "reason": "too_short"}
        
    model = get_whisper_model()
    segments, _ = model.transcribe(clip, beam_size=3, language="en", word_timestamps=True)
    segments = list(segments)
    
    relative_transition_time = t_center - t_start
    is_cutoff = False
    lyrics_words = []
    cutoff_reason = ""
    
    for segment in segments:
        if segment.words:
            for word in segment.words:
                w_text = word.word.strip()
                lyrics_words.append(w_text)
                if word.start < relative_transition_time < word.end:
                    if len(w_text) > 1 and w_text.lower() not in ["[music]", "(music)"]:
                        is_cutoff = True
                        cutoff_reason = f"vocals_cut_off_at_word_{w_text}_interval_{word.start:.2f}s-{word.end:.2f}s"
                        
    lyrics = " ".join(lyrics_words)
    return {
        "is_cutoff": is_cutoff,
        "lyrics": lyrics,
        "reason": cutoff_reason
    }

SLIDER_LABELS = ['Awful', 'Poor', 'Average', 'Good', 'Excellent']
SLIDER_FRACS = [0.0, 0.25, 0.5, 0.75, 1.0]
# aria-valuenow on handle is 1-5 (not 0-4)
EXPECTED_ARIA = [1, 2, 3, 4, 5]


def dispatch_mouse_click(ws, x, y):
    for event_type, extra in (
        ("mouseMoved", {}),
        ("mousePressed", {"button": "left", "clickCount": 1}),
        ("mouseReleased", {"button": "left", "clickCount": 1}),
    ):
        ws.send(json.dumps({
            "id": 99,
            "method": "Input.dispatchMouseEvent",
            "params": {"type": event_type, "x": float(x), "y": float(y), **extra},
        }))
        ws.recv()


def set_slider_on_page(ws, idx, slider_idx):
    scroll_js = f"""(() => {{
        let slider = document.querySelectorAll(".rc-slider")[{idx}];
        if (slider) slider.scrollIntoView({{ block: "center" }});
    }})()"""
    run_js(ws, scroll_js)
    time.sleep(SLIDER_SET_SLEEP_SEC)

    frac = SLIDER_FRACS[slider_idx]
    coord_js = f"""(() => {{
        let s = document.querySelectorAll(".rc-slider")[{idx}];
        let rail = s.querySelector(".rc-slider-rail");
        let r = rail.getBoundingClientRect();
        return JSON.stringify({{ x: r.left + r.width * {frac}, y: r.top + r.height / 2 }});
    }})()"""
    coords = json.loads(run_js(ws, coord_js))
    dispatch_mouse_click(ws, coords["x"], coords["y"])
    return f"rail-click at {int(coords['x'])},{int(coords['y'])}"


def read_slider_state(ws, idx):
    verify_js = f"""(() => {{
        let s = document.querySelectorAll(".rc-slider")[{idx}];
        if (!s) return JSON.stringify({{ error: "slider not found" }});
        let h = s.querySelector(".rc-slider-handle");
        let dots = s.querySelectorAll(".rc-slider-dot-active").length;
        return JSON.stringify({{
            handle: !!h,
            dots: dots,
            style: h ? h.getAttribute("style") : null,
            aria: h ? h.getAttribute("aria-valuenow") : null
        }});
    }})()"""
    return json.loads(run_js(ws, verify_js))


def verify_all_sliders(ws, slider_indices_to_set):
    all_ok = True
    details = []
    for idx, slider_idx in enumerate(slider_indices_to_set):
        exp_aria = EXPECTED_ARIA[slider_idx]
        label = SLIDER_LABELS[slider_idx]
        state = read_slider_state(ws, idx)
        if "error" in state:
            ok = False
        else:
            ok = state.get("handle") and str(state.get("aria")) == str(exp_aria)
        if not ok:
            all_ok = False
        details.append((idx, label, state, exp_aria, ok))
    return all_ok, details


def print_slider_verification(details):
    for idx, label, state, exp_aria, ok in details:
        if "error" in state:
            print(f"  Slider {idx} ({label}): ERROR {state['error']} ✗ FAILED")
        else:
            print(
                f"  Slider {idx} ({label}): handle={state.get('handle')}, "
                f"aria={state.get('aria')} (expected {exp_aria}) {'✓' if ok else '✗ FAILED'}"
            )


def infer_task_type_from_url(url):
    lower = (url or "").lower()
    if "post_extension" in lower or "post-extension" in lower:
        return "post-extension"
    if "pre_extension" in lower or "pre-extension" in lower:
        return "pre-extension"
    if "intro" in lower:
        return "intro"
    if "outro" in lower:
        return "outro"
    if "bridge" in lower:
        return "bridge"
    return "transition"


def infer_edit_window(url, duration, task_type):
    match = re.search(r"(\d+\.?\d*)-to-(\d+\.?\d*)", url or "")
    if match:
        return float(match.group(1)), float(match.group(2))
    seg = min(7.0, max(duration * 0.35, 1.0))
    if task_type in ("post-extension", "outro"):
        return max(0.0, duration - seg), duration
    if task_type in ("pre-extension", "intro"):
        return 0.0, min(duration, seg)
    if task_type == "bridge":
        mid = duration / 2.0
        return max(0.0, mid - 2.0), min(duration, mid + 2.0)
    return 0.0, duration


def score_to_slider_idx(combined_score):
    if combined_score <= 1.25:
        return 0
    if combined_score <= 2.25:
        return 1
    if combined_score <= 3.25:
        return 2
    if combined_score <= 4.25:
        return 3
    return 4


def analyze_and_rate_audio(ws, audio_src, name, task_type, edit_start=None, edit_end=None, test_info=None, run_whisper=False):
    audio_path = f"/tmp/{name}.wav"
    print(f"Downloading {audio_src} -> {audio_path}")
    download_audio_js(ws, audio_src, audio_path)

    file_size = os.path.getsize(audio_path)
    if file_size < 1000:
        raise Exception(f"Downloaded empty or invalid audio for {name}!")

    if edit_start is None or edit_end is None:
        y_full, sr_full = librosa.load(audio_path, sr=32000, mono=True)
        duration = len(y_full) / sr_full
        edit_start, edit_end = infer_edit_window(audio_src, duration, task_type)
        print(f"Task type: {task_type}, edit window: {edit_start:.2f}s - {edit_end:.2f}s")

    print("Running PANNs acoustic analysis...")
    try:
        panns_res = analyze_with_panns(audio_path, edit_start, edit_end)
        print("PANNs result:", json.dumps(panns_res, indent=2))
    except Exception as e:
        print(f"PANNs execution error: {e}")
        panns_res = {"score": 3.0, "issues": []}

    print("Running CLAP quality analysis...")
    try:
        clap_res = analyze_with_clap(audio_path, task_type)
        print("CLAP result:", json.dumps(clap_res, indent=2))
    except Exception as e:
        print(f"CLAP execution error: {e}")
        clap_res = {"score": 3.0, "best_match": ""}

    combined_score = (clap_res["score"] + panns_res["score"]) / 2.0
    if abs(clap_res["score"] - panns_res["score"]) > 1.5:
        combined_score = panns_res["score"]

    print("Running Whisper ASR vocals cut-off detection...")
    if run_whisper:
        try:
            whisper_res = analyze_with_whisper(audio_path)
            print("Whisper result:", json.dumps(whisper_res, indent=2))
            if whisper_res["is_cutoff"]:
                print("WARNING: Detected vocals cut-off in transition zone. Penalty applied!")
                combined_score = min(combined_score, 1.5)
        except Exception as e:
            print(f"Whisper execution error: {e}")
    else:
        print("Skipped (not needed for this task type).")

    print(f"Combined model score (after ASR adjustments): {combined_score:.2f}")

    allowed_scores = []
    if test_info and test_info.get("answer"):
        discrete_list = test_info["answer"].get("serializedAnswer", {}).get("score_range_discrete", [])
        for item in discrete_list:
            allowed_scores.append(float(item["value"]))

    print(f"Allowed scores (from exam metadata): {allowed_scores}")
    if allowed_scores:
        mapped_score = min(allowed_scores, key=lambda val: abs(val - combined_score))
        print(f"Clamped to closest allowed score: {mapped_score}")
    else:
        mapped_score = combined_score

    slider_idx = score_to_slider_idx(mapped_score)
    print(f"Determined Rating: {SLIDER_LABELS[slider_idx]} (slider index: {slider_idx})")

    if os.path.exists(audio_path):
        os.remove(audio_path)
    return slider_idx

def process_one_batch():
    batch_start_time = time.time()
    try:
        ws_url = get_ws_url()
        ws = create_connection(ws_url, timeout=30, skip_utf8_validation=True)
    except Exception as e:
        print(f"Failed to connect to CDP: {e}")
        return False, 5.0
        
    try:
        body_text = run_js(ws, "document.body ? document.body.innerText : ''")
        if any(marker in body_text for marker in ("Looking for surveys", "No more surveys")):
            print("No more surveys available. Stopping loop.")
            ws.close()
            return False, DONE_WAIT_SEC
            
        # Close any open modal
        modal_text = run_js(ws, "document.querySelector('.modal-container')?.textContent?.trim()?.substring(0,50)")
        if modal_text:
            print(f"Found active modal: {modal_text}. Closing it...")
            run_js(ws, """(() => {
                let btn = document.querySelector(".modal-container")?.querySelector("button");
                if (btn) btn.click();
            })()""")
            time.sleep(1.0)
            
        # Get all tasks from Redux store state
        js_get_tasks = """(() => {
            try {
                let state = window.store.getState();
                let workable = state.survey.workableSurvey;
                if (!workable) return "[]";
                let tasks = workable.tasks;
                if (!tasks || tasks.length === 0) return "[]";
                let templateTaskType = workable.templateTaskType;
                return JSON.stringify({
                    templateTaskType: templateTaskType,
                    tasks: tasks.map((t, idx) => ({
                        index: idx,
                        requestId: t.requestId,
                        audio_src: t.taskData ? t.taskData.audio_src : null,
                        overlap: t.taskData ? t.taskData.overlap : null,
                        mushra_models: t.taskData ? ["A","B","C","D","E"].map(function(m) {
                            var url = t.taskData["audio_model_" + m];
                            if (!url) return null;
                            return { key: m, url: url };
                        }).filter(Boolean) : [],
                        testQuestionInformation: (t.taskData && t.taskData.testQuestionInformation) ? t.taskData.testQuestionInformation : null
                    }))
                });
            } catch(e) {
                return "ERROR:" + e.message;
            }
        })()"""
        
        tasks_val = run_js(ws, js_get_tasks)
        if tasks_val.startswith("ERROR:") or tasks_val == "[]":
            if not tasks_val.startswith("ERROR:"):
                slider_count = run_js(ws, "document.querySelectorAll('.rc-slider').length")
                if str(slider_count) == "0":
                    print("No tasks in Redux and no sliders on page — survey finished.")
                    ws.close()
                    return False, DONE_WAIT_SEC
                print("No tasks found in Redux. Waiting...")
            ws.close()
            return False, 10.0
            
        data = json.loads(tasks_val)
        template_task_type = data.get("templateTaskType")
        tasks = data.get("tasks", [])
        supported_types = ("Transition quality", "SFX-MUSHRA-Style")

        if template_task_type not in supported_types:
            raise Exception(
                f"Unsupported task type: '{template_task_type}'. "
                f"Supported: {supported_types}. Aborting submission to prevent errors."
            )

        slider_indices_to_set = []

        if template_task_type == "SFX-MUSHRA-Style":
            print(f"\n=================== FOUND NEW BATCH: SFX-MUSHRA ({len(tasks)} task(s)) ===================")
            mushra_task = tasks[0]
            models = mushra_task.get("mushra_models") or []
            if not models:
                raise Exception("No MUSHRA model audio URLs found. Aborting submission.")
            page_hint = run_js(
                ws,
                "(() => { let t = document.body.innerText.toLowerCase(); "
                "if (t.includes('post-extension')) return 'post-extension'; "
                "if (t.includes('pre-extension')) return 'pre-extension'; "
                "if (t.includes('intro')) return 'intro'; "
                "if (t.includes('outro')) return 'outro'; "
                "if (t.includes('bridge')) return 'bridge'; "
                "return 'post-extension'; })()",
            )
            test_info = mushra_task.get("testQuestionInformation")
            for model in models:
                key = model.get("key")
                url = model.get("url")
                print(f"\n--- Sample {key} ---")
                if not url:
                    raise Exception(f"Missing audio URL for sample {key}")
                task_type = infer_task_type_from_url(url)
                if task_type == "transition":
                    task_type = page_hint
                slider_idx = analyze_and_rate_audio(
                    ws, url, f"mushra_{key}", task_type, test_info=test_info, run_whisper=False
                )
                slider_indices_to_set.append(slider_idx)
        else:
            print(f"\n=================== FOUND NEW BATCH: {len(tasks)} TASKS ===================")
            for t in tasks:
                idx = t.get("index")
                req_id = t.get("requestId")
                audio_src = t.get("audio_src")
                overlap = t.get("overlap") or 0.0
                test_info = t.get("testQuestionInformation")

                print(f"\n--- Task {idx} (Request ID: {req_id}) ---")

                edit_start = max(0.0, 10.0 - (overlap / 2.0) - 0.5)
                edit_end = 10.0 + (overlap / 2.0) + 0.5

                if not audio_src:
                    raise Exception(
                        f"audio_src is empty/null for task {idx}! Aborting submission to prevent errors."
                    )

                slider_idx = analyze_and_rate_audio(
                    ws, audio_src, f"task_{idx}", "transition", edit_start, edit_end, test_info, run_whisper=True
                )
                slider_indices_to_set.append(slider_idx)

        if not slider_indices_to_set:
            raise Exception("No slider ratings determined. Aborting submission.")

        # Move sliders in the page
        print("\n=== SETTING SLIDERS ON THE PAGE ===")
        ws.send(json.dumps({"id": 3, "method": "Input.enable"}))
        ws.recv()

        for idx, slider_idx in enumerate(slider_indices_to_set):
            label = SLIDER_LABELS[slider_idx]
            exp_aria = EXPECTED_ARIA[slider_idx]
            print(f"Setting slider {idx} to {label} (aria={exp_aria})...")
            result = set_slider_on_page(ws, idx, slider_idx)
            print(f"  Click result: {result}")
            time.sleep(SLIDER_SET_SLEEP_SEC)
            state = read_slider_state(ws, idx)
            ok = state.get("handle") and str(state.get("aria")) == str(exp_aria)
            if not ok:
                print(f"  Slider {idx} first attempt failed, retrying...")
                set_slider_on_page(ws, idx, slider_idx)
                time.sleep(SLIDER_SET_SLEEP_SEC)
                state = read_slider_state(ws, idx)
                ok = state.get("handle") and str(state.get("aria")) == str(exp_aria)
            print(f"  Slider {idx} set check: aria={state.get('aria')} {'✓' if ok else '✗ FAILED'}")

        elapsed = time.time() - batch_start_time
        target_duration = BATCH_TARGET_BY_TYPE.get(template_task_type, BATCH_MIN_DURATION_SEC)
        if elapsed < target_duration:
            sleep_needed = min(target_duration - elapsed, MAX_PADDING_SEC)
            print(
                f"\n[TIME CONTROL] Elapsed {elapsed:.1f}s, padding {sleep_needed:.1f}s "
                f"(target ~{target_duration:.0f}s, cap +{MAX_PADDING_SEC:.0f}s)..."
            )
            if sleep_needed > 0:
                time.sleep(sleep_needed)
        else:
            print(f"\n[TIME CONTROL] Elapsed {elapsed:.1f}s — no padding needed.")

        # Pre-submit batch verification (mandatory)
        print("\n=== PRE-SUBMIT VERIFICATION ===")
        all_ok, details = verify_all_sliders(ws, slider_indices_to_set)
        print_slider_verification(details)
        if not all_ok:
            print("ERROR: Pre-submit verification failed. Retrying failed sliders once...")
            for idx, slider_idx in enumerate(slider_indices_to_set):
                exp_aria = EXPECTED_ARIA[slider_idx]
                state = read_slider_state(ws, idx)
                ok = state.get("handle") and str(state.get("aria")) == str(exp_aria)
                if not ok:
                    label = SLIDER_LABELS[slider_idx]
                    print(f"  Re-setting slider {idx} to {label}...")
                    set_slider_on_page(ws, idx, slider_idx)
                    time.sleep(SLIDER_SET_SLEEP_SEC)
            all_ok, details = verify_all_sliders(ws, slider_indices_to_set)
            print("\n=== PRE-SUBMIT RE-VERIFICATION ===")
            print_slider_verification(details)
        if not all_ok:
            print("ERROR: Pre-submit verification still failed. Aborting submit.")
            ws.close()
            return False, 5.0

        # Submit
        print("\n=== SUBMITTING RATINGS ===")
        submit_js = """(() => {
            let btns = Array.from(document.querySelectorAll("button"));
            let btn = btns.find(b => b.textContent.trim() === "Submit Rating" && !b.disabled);
            if (btn) {
                btn.click();
                return "clicked Submit Rating";
            }
            return "Submit button not found or disabled. buttons: " + btns.map(b => b.textContent.trim()).join("|");
        })()"""
        
        submit_status = run_js(ws, submit_js)
        print("Submit status:", submit_status)
        if "clicked Submit Rating" not in str(submit_status):
            print("ERROR: Submit did not succeed. Aborting batch.")
            ws.close()
            return False, 5.0
        time.sleep(3.0)
        post_url = run_js(ws, "window.location.href")
        post_modal = run_js(ws, "document.querySelector('.modal-container')?.textContent?.trim()?.substring(0,120) || ''")
        print(f"Post-submit URL: {post_url}")
        if post_modal:
            print(f"Post-submit modal: {post_modal}")
        
        ws.close()
        return True, POST_SUBMIT_WAIT_SEC
        
    except Exception as e:
        print(f"Error processing batch: {e}")
        try:
            ws.close()
        except:
            pass
        return False, 5.0

def acquire_single_instance_lock():
    lock_fd = open(LOCK_PATH, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        print(f"Another solve_tasks instance holds {LOCK_PATH}. Exit.")
        sys.exit(1)
    lock_fd.write(str(os.getpid()))
    lock_fd.flush()
    return lock_fd


def main():
    acquire_single_instance_lock()
    print("Continuous task solver loop started...")
    get_clap_model()
    get_panns_model()
    print("Models pre-warmed (CLAP + PANNs). Whisper loads on demand for Transition quality.")
    idle_streak = 0
    while True:
        success, wait_sec = process_one_batch()
        if wait_sec == DONE_WAIT_SEC:
            print("Loop finished: no more work.")
            break
        if success:
            idle_streak = 0
            print(f"Successfully processed batch. Sleeping {wait_sec}s...")
        else:
            idle_streak += 1
            print(f"No action taken ({idle_streak}/{IDLE_EXIT_AFTER}). Sleeping {wait_sec}s...")
            if idle_streak >= IDLE_EXIT_AFTER:
                print("No tasks after repeated attempts. Exiting.")
                break
        time.sleep(wait_sec)

if __name__ == "__main__":
    main()
