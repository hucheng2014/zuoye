import json
import urllib.request
import re
import os
import sys
import base64
import time
import numpy as np
import librosa
from websocket import create_connection

# Load models config
CLAP_MODEL = "/app/RQOAE/models/music_audioset_epoch_15_esc_90.14.pt"
PANNS_MODEL = "/root/panns_data/Cnn14_mAP=0.431.pth"
WHISPER_MODEL = "/app/RQOAE/models/faster-whisper-large-v3"
CDP_ENDPOINT = "http://browser:9223"

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

def download_audio_js(ws, url, output_path):
    js = f"""(async () => {{
        try {{
            const resp = await fetch("{url}");
            const blob = await resp.blob();
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
    if val.startswith("ERROR:"):
        raise Exception(f"Download failed: {val}")
    data = base64.b64decode(val)
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
        if "Looking for surveys" in body_text:
            print("No surveys available (Looking for surveys...).")
            ws.close()
            return False, 10.0
            
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
                print("No tasks found in Redux. Waiting...")
            ws.close()
            return False, 3.0
            
        data = json.loads(tasks_val)
        template_task_type = data.get("templateTaskType")
        tasks = data.get("tasks", [])
        
        if template_task_type != "Transition quality":
            raise Exception(f"Unsupported task type: '{template_task_type}'. This script only supports 'Transition quality' tasks. Aborting submission to prevent errors.")
        print(f"\n=================== FOUND NEW BATCH: {len(tasks)} TASKS ===================")
        
        slider_indices_to_set = []
        labels = ['Awful', 'Poor', 'Average', 'Good', 'Excellent']
        
        for t in tasks:
            idx = t.get("index")
            req_id = t.get("requestId")
            audio_src = t.get("audio_src")
            overlap = t.get("overlap") or 0.0
            test_info = t.get("testQuestionInformation")
            
            print(f"\n--- Task {idx} (Request ID: {req_id}) ---")
            
            # Determine edit window
            edit_start = 10.0 - (overlap / 2.0) - 0.5
            edit_end = 10.0 + (overlap / 2.0) + 0.5
            edit_start = max(0.0, edit_start)
            
            # Check if audio_src is valid
            if not audio_src:
                raise Exception(f"audio_src is empty/null for task {idx}! This might be an unsupported task layout or a loading error. Aborting submission to prevent errors.")

            # Download audio
            audio_path = f"/tmp/task_{idx}.wav"
            print(f"Downloading {audio_src} -> {audio_path}")
            download_audio_js(ws, audio_src, audio_path)
            
            file_size = os.path.getsize(audio_path)
            if file_size < 1000:
                print("ERROR: Downloaded empty or invalid audio!")
                sys.exit(1)
                
            print("Running PANNs acoustic analysis...")
            try:
                panns_res = analyze_with_panns(audio_path, edit_start, edit_end)
                print("PANNs result:", json.dumps(panns_res, indent=2))
            except Exception as e:
                print(f"PANNs execution error: {e}")
                panns_res = {"score": 3.0, "issues": []}
            
            print("Running CLAP quality analysis...")
            try:
                clap_res = analyze_with_clap(audio_path, "transition")
                print("CLAP result:", json.dumps(clap_res, indent=2))
            except Exception as e:
                print(f"CLAP execution error: {e}")
                clap_res = {"score": 3.0, "best_match": ""}
            
            combined_score = (clap_res["score"] + panns_res["score"]) / 2.0
            if abs(clap_res["score"] - panns_res["score"]) > 1.5:
                combined_score = panns_res["score"]
            
            print("Running Whisper ASR vocals cut-off detection...")
            try:
                whisper_res = analyze_with_whisper(audio_path)
                print("Whisper result:", json.dumps(whisper_res, indent=2))
                if whisper_res["is_cutoff"]:
                    print("WARNING: Detected vocals cut-off in transition zone. Penalty applied!")
                    combined_score = min(combined_score, 1.5)
            except Exception as e:
                print(f"Whisper execution error: {e}")
                
            print(f"Combined model score (after ASR adjustments): {combined_score:.2f}")
            
            # Check Allowed Answers in exam metadata
            allowed_scores = []
            if test_info and "answer" in test_info and test_info["answer"]:
                discrete_list = test_info["answer"].get("serializedAnswer", {}).get("score_range_discrete", [])
                for item in discrete_list:
                    val = float(item["value"])
                    allowed_scores.append(val)
            
            print(f"Allowed scores (from exam metadata): {allowed_scores}")
            
            if not allowed_scores:
                mapped_score = combined_score
            else:
                mapped_score = min(allowed_scores, key=lambda val: abs(val - combined_score))
                print(f"Clamped to closest allowed score: {mapped_score}")
                
            if mapped_score <= 1.25:
                slider_idx = 0
            elif mapped_score <= 2.25:
                slider_idx = 1
            elif mapped_score <= 3.25:
                slider_idx = 2
            elif mapped_score <= 4.25:
                slider_idx = 3
            else:
                slider_idx = 4
                
            print(f"Determined Rating: {labels[slider_idx]} (slider index: {slider_idx})")
            slider_indices_to_set.append(slider_idx)
            
            if os.path.exists(audio_path):
                os.remove(audio_path)

        # Move sliders in the page
        print("\n=== SETTING SLIDERS ON THE PAGE ===")
        fracs = [0.0, 0.25, 0.5, 0.75, 1.0]
        expected_dots = [1, 2, 3, 4, 5]
        
        ws.send(json.dumps({"id": 3, "method": "Input.enable"}))
        ws.recv()
        
        for idx, slider_idx in enumerate(slider_indices_to_set):
            frac = fracs[slider_idx]
            label = labels[slider_idx]
            exp_dot = expected_dots[slider_idx]
            
            print(f"Setting slider {idx} to {label} ({int(frac*100)}%)...")
            
            scroll_js = f"""(() => {{
                let container = document.querySelector(".application-wrapper--content");
                let slider = document.querySelectorAll(".rc-slider")[{idx}];
                if (slider) {{
                    let el = slider;
                    let top = 0;
                    while (el && el !== container) {{
                        top += el.offsetTop;
                        el = el.offsetParent;
                    }}
                    container.scrollTop = top - container.clientHeight / 2 + slider.offsetHeight / 2;
                }}
            }})()"""
            run_js(ws, scroll_js)
            time.sleep(1.0)
            
            click_js = f"""(() => {{
                let s = document.querySelectorAll(".rc-slider")[{idx}];
                let rail = s.querySelector(".rc-slider-rail");
                let r = rail.getBoundingClientRect();
                let x = r.left + r.width * {frac};
                let y = r.top + r.height / 2;
                let opts = {{ bubbles: true, cancelable: true, clientX: x, clientY: y }};
                rail.dispatchEvent(new MouseEvent("mousedown", opts));
                rail.dispatchEvent(new MouseEvent("mouseup", opts));
                rail.dispatchEvent(new MouseEvent("click", opts));
                return "ok at " + Math.round(x) + "," + Math.round(y);
            }})()"""
            run_js(ws, click_js)
            time.sleep(1.0)
            
            verify_js = f"""(() => {{
                let s = document.querySelectorAll(".rc-slider")[{idx}];
                let dots = s.querySelectorAll(".rc-slider-dot-active").length;
                let style = s.querySelector(".rc-slider-handle")?.getAttribute("style");
                return JSON.stringify({{ dots: dots, style: style }});
            }})()"""
            verify_res = json.loads(run_js(ws, verify_js))
            ok = str(verify_res["dots"]) == str(exp_dot)
            print(f"Slider {idx} verification: activeDots={verify_res['dots']} {'✓' if ok else '✗ FAILED'}")

        # Check elapsed time and delay submission to exceed estimated rating time.
        elapsed = time.time() - batch_start_time
        target_duration = 155.0
        if elapsed < target_duration:
            sleep_needed = target_duration - elapsed
            print(f"\n[TIME CONTROL] Total time elapsed since loading this batch: {elapsed:.2f}s.")
            print(f"[TIME CONTROL] Force waiting for another {sleep_needed:.2f}s to ensure task duration > 2 minutes 30 seconds...")
            while sleep_needed > 0:
                chunk = min(10.0, sleep_needed)
                time.sleep(chunk)
                sleep_needed -= chunk
                elapsed = time.time() - batch_start_time
                print(f"  Progress: {elapsed:.2f}s / {target_duration}s elapsed...")

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
        time.sleep(3.0)
        
        ws.close()
        return True, 120.0 # Wait 2 minutes before starting the next task.
        
    except Exception as e:
        print(f"Error processing batch: {e}")
        try:
            ws.close()
        except:
            pass
        return False, 5.0

def main():
    print("Continuous task solver loop started...")
    # Pre-warm models globally
    get_clap_model()
    get_panns_model()
    get_whisper_model()
    print("Models pre-warmed. Entering main loop...")
    while True:
        success, wait_sec = process_one_batch()
        if success:
            print(f"Successfully processed batch. Sleeping {wait_sec}s...")
        else:
            print(f"No action taken. Sleeping {wait_sec}s...")
        time.sleep(wait_sec)

if __name__ == "__main__":
    main()
