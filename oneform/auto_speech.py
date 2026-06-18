"""
🎙️ Speech Human Recording 自动化脚本
=====================================

功能:
  1. 自动启动 Chrome (使用你已登录的 Profile)
  2. 读取页面 Utterance 文本
  3. 优先使用本地 GPT-SoVITS 生成克隆语音
  4. 若本地模型不可用或参考音不合格则直接停止
  5. 通过 JS 注入将音频注入录制流 (绕过真实麦克风)
  6. 自动完成录制、上传和 Validation 填写

使用方法:
  1. 关闭所有 Chrome 窗口 (重要!)
  2. 运行: py auto_speech.py
  3. 脚本会自动启动 Chrome 并打开做题页面
"""

from __future__ import annotations

import asyncio
import base64
import json
import math
import os
import random
import re
import socket
import subprocess
import sys
import time
import wave
from difflib import SequenceMatcher
from pathlib import Path
from urllib import error, parse, request

try:
    import edge_tts
except ImportError:
    edge_tts = None

try:
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError
    from playwright.async_api import async_playwright
except ImportError:
    print("❌ playwright not installed. Run: py -m pip install playwright && py -m playwright install chromium")
    sys.exit(1)

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


# ============================
# ⚙️ 配置区域
# ============================

IS_WINDOWS = sys.platform.startswith("win")
IS_LINUX = sys.platform.startswith("linux")

# Chrome 路径 (跨平台自动检测)
if IS_WINDOWS:
    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
elif IS_LINUX:
    CHROME_PATH = "/usr/bin/google-chrome"
else:
    CHROME_PATH = "chrome"

# Chrome Profile (跨平台)
if IS_WINDOWS:
    CHROME_PROFILE = "Profile 2"
else:
    CHROME_PROFILE = "Default"

# Chrome 远程调试端口；如需连接现有 Docker 浏览器，可设置 SPEECH_CDP_URL=http://127.0.0.1:9225
CHROME_DEBUG_PORT = 9222
SPEECH_CDP_URL = os.environ.get("SPEECH_CDP_URL", "").strip()

# 做题页面 URL
TASK_URL = "https://www.tryrating.com/app/survey/rate"

# 🤖 TTS 声音配置
USE_GPT_SOVITS = True

# === GPT-SoVITS 配置项 ===
GPT_SOVITS_HOST = "127.0.0.1"
GPT_SOVITS_PORT = 9880
SOVITS_API_URL = f"http://{GPT_SOVITS_HOST}:{GPT_SOVITS_PORT}/tts"
SOVITS_API_TIMEOUT = 180
SOVITS_START_TIMEOUT = 90
SOVITS_MIN_REF_DURATION = 3.0
SOVITS_MAX_REF_DURATION = 10.0
SOVITS_ALLOW_STITCHED_REFERENCE = False
SOVITS_VALIDATE_OUTPUT = True
SOVITS_MIN_DURATION_RATIO = 0.65
SOVITS_MIN_MEAN_ABS_RATIO = 0.22
SOVITS_MIN_PEAK_RATIO = 0.25
SOVITS_POSTPROCESS_GENERATED_AUDIO = True
SOVITS_POSTPROCESS_FILTER = "highpass=f=80,afftdn=nf=-28:nt=w,lowpass=f=12000"
SOVITS_REFERENCE_WARN_NOISE_FLOOR_RATIO = 0.03
# 生成音频底噪阈值：原来偏宽松，容易把“有背景沙沙声”的结果放过。
SOVITS_OUTPUT_NOISE_FLOOR_RATIO = 0.03
SOVITS_OUTPUT_CONSTANT_NOISE_CV = 0.95
SOVITS_POSTPROCESS_TRIGGER_NOISE_FLOOR_RATIO = 0.018
SOVITS_POSTPROCESS_KEEP_MEAN_ABS_RATIO = 0.45
SOVITS_POSTPROCESS_MIN_NOISE_IMPROVEMENT = 0.08
SOVITS_ENGLISH_RESCORING = True

# ASR 模型路径 (跨平台)
if IS_WINDOWS:
    SOVITS_ENGLISH_ASR_MODEL_PATH = r"D:\putonghuaasr\models\faster-whisper-large-v3"
else:
    SOVITS_ENGLISH_ASR_MODEL_PATH = os.path.expanduser("~/putonghuaasr/models/faster-whisper-large-v3")

SOVITS_ENGLISH_ASR_COMPUTE_TYPE = "int8"
SOVITS_ENGLISH_RESCORING_MIN_WORDS = 2

# 如需手工指定参考音频，可填入以下三个值；留空则自动从训练结果推断
SOVITS_REF_AUDIO = ""
SOVITS_PROMPT_TEXT = ""
SOVITS_PROMPT_LANG = ""

# 如需分别锁定中英文参考音频，可填入以下配置；留空则回退到上面的通用配置
if IS_WINDOWS:
    SOVITS_REF_AUDIO_ZH = r"D:\oneform\generated_audio\manual_refs\myvoice_v2_ref_zh_clean.wav"
    SOVITS_REF_AUDIO_EN = r"D:\oneform\generated_audio\manual_refs\myvoice_v2_ref_en_clean.wav"
else:
    SOVITS_REF_AUDIO_ZH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_audio", "manual_refs", "myvoice_v2_ref_zh_clean.wav")
    SOVITS_REF_AUDIO_EN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_audio", "manual_refs", "myvoice_v2_ref_en_clean.wav")

SOVITS_PROMPT_TEXT_ZH = "星光之城。夏夜微风。月光列车。"
SOVITS_PROMPT_LANG_ZH = "zh"
SOVITS_PROMPT_TEXT_EN = "Blue Sky. Good Night. New World."
SOVITS_PROMPT_LANG_EN = "en"

# 音频输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_audio")
SOVITS_CONFIG_PATH = os.path.join(OUTPUT_DIR, "gpt_sovits_tts_infer.yaml")
SOVITS_LOG_PATH = os.path.join(OUTPUT_DIR, "gpt_sovits_api.log")

# ⚠️ 是否自动提交 (默认 False = 绝不自动提交!)
AUTO_SUBMIT = False

# 提交间隔
MIN_DELAY = 8
MAX_DELAY = 20


# ============================
# 🌐 Chrome 启动器
# ============================

if IS_WINDOWS:
    CHROME_USER_DATA = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
else:
    CHROME_USER_DATA = os.path.expanduser("~/.config/google-chrome")


def kill_chrome_zombies():
    """杀掉所有残留 Chrome 后台进程，防止新启动的 Chrome 无法绑定调试端口"""
    try:
        if IS_WINDOWS:
            subprocess.run(
                ["taskkill", "/F", "/IM", "chrome.exe", "/T"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1)
            for _ in range(3):
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(1)
                check = subprocess.run(
                    ["powershell", "-Command",
                     "(Get-Process chrome -ErrorAction SilentlyContinue | Measure-Object).Count"],
                    capture_output=True, text=True,
                )
                if check.stdout.strip() == "0":
                    break
        else:
            subprocess.run(
                ["pkill", "-f", "chrome"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1)
    except Exception:
        pass


def launch_chrome():
    """启动带调试端口的 Chrome (使用已登录的 Profile)"""
    print("  🌐 启动 Chrome...")
    print(f"     Profile: {CHROME_PROFILE}")
    print(f"     User Data: {CHROME_USER_DATA}")
    print(f"     Debug Port: {CHROME_DEBUG_PORT}")

    # 先杀掉所有残留 Chrome 进程 (包括系统托盘隐藏的后台进程)
    kill_chrome_zombies()

    cmd = [
        CHROME_PATH,
        f"--remote-debugging-port={CHROME_DEBUG_PORT}",
        f"--user-data-dir={CHROME_USER_DATA}",
        f"--profile-directory={CHROME_PROFILE}",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print(f"  ✅ Chrome 已启动 (PID: {process.pid})")
    return process


def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("localhost", port)) == 0


def wait_for_port(port: int, timeout: float) -> bool:
    """等待端口开始监听"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_port_in_use(port):
            return True
        time.sleep(1)
    return False


# ============================
# 🔊 TTS 引擎
# ============================

SOVITS_RUNTIME = None
SOVITS_API_PROCESS = None
SOVITS_API_LOG_HANDLE = None
SOVITS_ACTIVE_MODEL_KEY = None
FFMPEG_EXE = None
SOVITS_ASR_MODEL = None


def detect_language(text: str) -> str:
    """检测文本主要语言"""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    english_chars = len(re.findall(r"[a-zA-Z]", text))
    if chinese_chars and english_chars:
        return "mixed"
    if chinese_chars:
        return "zh"
    if english_chars:
        return "en"
    return "en"


def to_sovits_lang(lang: str) -> str:
    """映射到 GPT-SoVITS 更稳的语言枚举"""
    if lang == "mixed":
        return "auto"
    return "all_zh" if lang == "zh" else "en"


def normalize_sovits_text(text: str, lang: str) -> str:
    """对送入 GPT-SoVITS 的文本做轻量标准化"""
    normalized = re.sub(r"\s+", " ", text).strip()
    if lang == "en":
        words = normalized.split(" ")
        if len(words) <= 3:
            normalized = normalized.upper()
        else:
            titled_words = [word.capitalize() for word in words]
            small_words = {"a", "an", "and", "as", "at", "for", "in", "of", "on", "or", "the", "to"}
            for i in range(1, len(titled_words) - 1):
                if titled_words[i].lower() in small_words:
                    titled_words[i] = titled_words[i].lower()

            normalized = " ".join(titled_words)

            if not re.search(r"[.!?;,]", normalized):
                for i in range(2, len(titled_words) - 1):
                    if titled_words[i].lower() in {"the", "a", "an"}:
                        left = " ".join(titled_words[:i])
                        right = " ".join(titled_words[i:])
                        normalized = f"{left}. {right}"
                        break
    return normalized


def split_english_title_case(text: str) -> str:
    """为较长英文标题补一个更像副标题的断句"""
    words = text.split(" ")
    if len(words) < 5 or re.search(r"[.!?;,]", text):
        return text

    for i in range(2, len(words) - 1):
        if words[i].lower() in {"the", "a", "an"}:
            left = " ".join(words[:i])
            right = " ".join(words[i:])
            return f"{left}. {right}"
    return text


def english_rescoring_candidates(text: str) -> list[str]:
    """为英文标题准备几种候选写法，让本地 ASR 自己挑更像原句的一版"""
    clean = re.sub(r"\s+", " ", text).strip()
    title_case = normalize_sovits_text(clean, "en")
    plain_title = " ".join(word.capitalize() for word in clean.split(" "))
    if len(clean.split(" ")) > 3:
        small_words = {"a", "an", "and", "as", "at", "for", "in", "of", "on", "or", "the", "to"}
        title_words = plain_title.split(" ")
        for i in range(1, len(title_words) - 1):
            if title_words[i].lower() in small_words:
                title_words[i] = title_words[i].lower()
        plain_title = " ".join(title_words)

    candidates = [
        clean,
        clean.upper(),
        plain_title,
        split_english_title_case(plain_title),
    ]

    deduped = []
    for item in candidates:
        if item and item not in deduped:
            deduped.append(item)
    return deduped


def normalize_compare_text(text: str) -> str:
    """把文本压到更适合做 ASR 近似匹配的形态"""
    normalized = re.sub(r"[^a-zA-Z0-9]+", " ", text).strip().lower()
    return re.sub(r"\s+", " ", normalized)


def mixed_text_prefers_english(text: str) -> bool:
    """判断中英混合文本是否本质上更像“中文提示词 + 英文标题”"""
    chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
    english_chars = len(re.findall(r"[a-zA-Z]", text))
    english_words = len(re.findall(r"[a-zA-Z]+", text))
    return english_words >= 2 and (english_chars >= chinese_chars * 2 or chinese_chars <= 4)


def score_asr_match(target_text: str, recognized_text: str) -> float:
    """按字符和词覆盖率综合评估生成结果和目标文本的接近程度"""
    target = normalize_compare_text(target_text)
    recognized = normalize_compare_text(recognized_text)
    if not target or not recognized:
        return 0.0

    char_score = SequenceMatcher(None, target, recognized).ratio()
    target_words = target.split()
    recognized_words = recognized.split()
    overlap = sum(1 for word in target_words if word in recognized_words) / max(len(target_words), 1)
    len_ratio = min(len(target_words), len(recognized_words)) / max(len(target_words), len(recognized_words), 1)
    return char_score * 0.55 + overlap * 0.35 + len_ratio * 0.10


def get_sovits_asr_model():
    """按需加载本地 English ASR，用于英文标题候选打分"""
    global SOVITS_ASR_MODEL
    if SOVITS_ASR_MODEL is not None:
        return SOVITS_ASR_MODEL
    if not SOVITS_ENGLISH_RESCORING or WhisperModel is None:
        return None
    if not os.path.exists(SOVITS_ENGLISH_ASR_MODEL_PATH):
        print(f"  ⚠️ 未找到本地 English ASR 模型: {SOVITS_ENGLISH_ASR_MODEL_PATH}")
        return None

    print("  🎧 加载本地 English ASR 进行候选打分...")
    SOVITS_ASR_MODEL = WhisperModel(
        SOVITS_ENGLISH_ASR_MODEL_PATH,
        device="cpu",
        compute_type=SOVITS_ENGLISH_ASR_COMPUTE_TYPE,
    )
    return SOVITS_ASR_MODEL


def transcribe_english_audio_for_score(audio_path: str) -> str:
    """用本地 large ASR 转写生成样本，用于自动选最佳英文候选"""
    model = get_sovits_asr_model()
    if model is None:
        return ""
    segments, _info = model.transcribe(
        audio_path,
        beam_size=5,
        vad_filter=True,
        language="en",
    )
    return "".join(segment.text for segment in segments).strip()


def tail_text(path: str, max_chars: int = 1200) -> str:
    """读取日志尾部，方便定位 API 启动失败原因"""
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return content[-max_chars:]


def resolve_ffmpeg_exe() -> str | None:
    """寻找可用的 ffmpeg，可用于生成后降噪"""
    global FFMPEG_EXE
    if FFMPEG_EXE:
        return FFMPEG_EXE

    candidates = [
        os.environ.get("FFMPEG_EXE", "").strip(),
        "ffmpeg",
    ]
    if IS_WINDOWS:
        candidates.extend([
            r"C:\Users\BERN7P\GPT-SoVITS\runtime\ffmpeg\bin\ffmpeg.exe",
            r"C:\Users\BERN7P\miniconda3\envs\GPTSoVits\Library\bin\ffmpeg.exe",
        ])
    for candidate in candidates:
        if not candidate:
            continue
        try:
            result = subprocess.run(
                [candidate, "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
            )
            if result.returncode == 0:
                FFMPEG_EXE = candidate
                return FFMPEG_EXE
        except Exception:
            continue
    return None


def get_wav_duration(path: Path) -> float:
    """读取 wav 时长"""
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def percentile(values: list[float], q: float) -> float:
    """计算简单分位数，避免引入额外依赖"""
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    low = int(pos)
    high = min(low + 1, len(ordered) - 1)
    frac = pos - low
    return ordered[low] * (1 - frac) + ordered[high] * frac


def inspect_wav(path: Path | str):
    """读取 wav 的基本统计信息，便于做参考音/输出音频校验"""
    with wave.open(str(path), "rb") as wf:
        nchannels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        frames = wf.getnframes()
        raw = wf.readframes(frames)

    if sampwidth != 2:
        raise RuntimeError(f"unsupported wav sample width: {sampwidth}")

    import array

    samples = array.array("h")
    samples.frombytes(raw)
    if not samples:
        raise RuntimeError("wav contains no samples")

    abs_samples = [abs(sample) for sample in samples]
    peak = max(abs_samples)
    mean_abs = sum(abs_samples) / len(abs_samples)
    duration = frames / float(framerate)
    chunk_size = max(1, int(framerate * 0.05))
    edge_chunk_count = max(1, int(0.35 / 0.05))
    peak_safe = max(peak, 1)
    rms_values = []
    zcr_values = []

    for start in range(0, len(samples), chunk_size):
        chunk = samples[start:start + chunk_size]
        if len(chunk) < max(1, chunk_size // 2):
            continue
        mean_sq = sum((sample / peak_safe) * (sample / peak_safe) for sample in chunk) / len(chunk)
        rms_values.append(math.sqrt(mean_sq))

        zero_crossings = 0
        prev = chunk[0]
        for current in chunk[1:]:
            if (prev < 0 <= current) or (prev >= 0 > current):
                zero_crossings += 1
            prev = current
        zcr_values.append(zero_crossings / max(len(chunk) - 1, 1))

    mean_rms = sum(rms_values) / max(len(rms_values), 1)
    rms_variance = sum((value - mean_rms) ** 2 for value in rms_values) / max(len(rms_values), 1)
    speech_level = max(percentile(rms_values, 0.85), 1e-6)
    noise_floor = percentile(rms_values, 0.15)
    edge_rms_values = rms_values[:edge_chunk_count] + rms_values[-edge_chunk_count:]
    edge_zcr_values = zcr_values[:edge_chunk_count] + zcr_values[-edge_chunk_count:]
    edge_rms = sum(edge_rms_values) / max(len(edge_rms_values), 1)
    edge_zcr = sum(edge_zcr_values) / max(len(edge_zcr_values), 1)

    return {
        "channels": nchannels,
        "sample_width": sampwidth,
        "framerate": framerate,
        "frames": frames,
        "duration": duration,
        "peak": peak,
        "mean_abs": mean_abs,
        "noise_floor": noise_floor,
        "speech_level": speech_level,
        "noise_floor_ratio": noise_floor / speech_level,
        "edge_rms_ratio": edge_rms / speech_level,
        "edge_zcr": edge_zcr,
        "energy_cv": math.sqrt(rms_variance) / max(mean_rms, 1e-6),
    }


def is_reference_duration_valid(duration: float) -> bool:
    """GPT-SoVITS 要求参考音频时长在 3~10 秒"""
    return SOVITS_MIN_REF_DURATION <= duration <= SOVITS_MAX_REF_DURATION


def validate_reference_entry(audio_path: str, prompt_text: str, prompt_lang: str):
    """检查参考音频是否可被 GPT-SoVITS 稳定使用"""
    if not audio_path or not os.path.exists(audio_path):
        print(f"  ⚠️ 参考音频不存在: {audio_path}")
        return None
    if not prompt_text.strip():
        print(f"  ⚠️ 参考音频缺少提示词: {audio_path}")
        return None

    try:
        stats = inspect_wav(audio_path)
    except Exception as e:
        print(f"  ⚠️ 参考音频无法读取: {audio_path} ({e})")
        return None

    if not is_reference_duration_valid(stats["duration"]):
        print(
            "  ⚠️ 参考音频时长不符合要求: "
            f"{os.path.basename(audio_path)} = {stats['duration']:.2f}s "
            f"(需 {SOVITS_MIN_REF_DURATION:.0f}~{SOVITS_MAX_REF_DURATION:.0f}s)"
        )
        return None

    if stats["noise_floor_ratio"] > SOVITS_REFERENCE_WARN_NOISE_FLOOR_RATIO:
        print(
            "  ⚠️ 参考音频底噪偏高: "
            f"{os.path.basename(audio_path)} noise_floor_ratio={stats['noise_floor_ratio']:.3f}"
        )

    return {
        "audio_path": str(audio_path),
        "prompt_text": prompt_text.strip(),
        "prompt_lang": prompt_lang,
        "stats": stats,
    }


def build_reference_audio(experiment_key: str, lang: str, items: list[dict]):
    """把多个短切片拼成 3~10 秒的参考音频"""
    if not items:
        return None

    selected = []
    total_duration = 0.0
    for item in items:
        selected.append(item)
        total_duration += item["duration"]
        if total_duration >= SOVITS_MIN_REF_DURATION:
            break

    if total_duration < SOVITS_MIN_REF_DURATION:
        return None

    ref_dir = Path(OUTPUT_DIR) / "sovits_refs"
    ref_dir.mkdir(parents=True, exist_ok=True)
    output_path = ref_dir / f"{experiment_key}_{lang}_ref.wav"

    with wave.open(str(items[0]["audio_path"]), "rb") as first_wav:
        nchannels = first_wav.getnchannels()
        sampwidth = first_wav.getsampwidth()
        framerate = first_wav.getframerate()

    silence_frames = int(framerate * 0.18)
    silence = b"\x00" * silence_frames * nchannels * sampwidth

    with wave.open(str(output_path), "wb") as out_wav:
        out_wav.setnchannels(nchannels)
        out_wav.setsampwidth(sampwidth)
        out_wav.setframerate(framerate)

        for index, item in enumerate(selected):
            with wave.open(str(item["audio_path"]), "rb") as in_wav:
                out_wav.writeframes(in_wav.readframes(in_wav.getnframes()))
            if index != len(selected) - 1:
                out_wav.writeframes(silence)

    prompt_text = " ".join(item["prompt_text"] for item in selected)
    return {
        "audio_path": str(output_path),
        "prompt_text": prompt_text,
        "prompt_lang": lang,
    }


def normalize_weight_key(path: Path) -> str:
    """把 GPT/SoVITS 权重名归一到同一实验 key"""
    stem = path.stem
    stem = re.sub(r"[-_]e\d+(?:[_-]s\d+)?$", "", stem, flags=re.IGNORECASE)
    stem = re.sub(r"[_-]s\d+$", "", stem, flags=re.IGNORECASE)
    return stem


def version_from_weight_dir(dir_name: str, prefix: str) -> str:
    suffix = dir_name[len(prefix):].lstrip("_")
    return suffix or "v1"


def pick_latest_weight_pair(root: Path):
    """尽量挑出同一实验下最新的 GPT/SoVITS 权重对"""
    gpt_weights = list(root.glob("GPT_weights*/*.ckpt"))
    sovits_weights = list(root.glob("SoVITS_weights*/*.pth"))

    if not gpt_weights or not sovits_weights:
        return None, None, None

    gpt_groups = {}
    sovits_groups = {}

    for path in gpt_weights:
        gpt_groups.setdefault(normalize_weight_key(path), []).append(path)
    for path in sovits_weights:
        sovits_groups.setdefault(normalize_weight_key(path), []).append(path)

    shared_keys = set(gpt_groups) & set(sovits_groups)
    if shared_keys:
        best_key = max(
            shared_keys,
            key=lambda key: max(
                max(item.stat().st_mtime for item in gpt_groups[key]),
                max(item.stat().st_mtime for item in sovits_groups[key]),
            ),
        )
        best_gpt = max(gpt_groups[best_key], key=lambda item: item.stat().st_mtime)
        best_sovits = max(sovits_groups[best_key], key=lambda item: item.stat().st_mtime)
        return best_gpt, best_sovits, best_key

    best_gpt = max(gpt_weights, key=lambda item: item.stat().st_mtime)
    best_sovits = max(sovits_weights, key=lambda item: item.stat().st_mtime)
    return best_gpt, best_sovits, normalize_weight_key(best_gpt)


def discover_gpt_sovits_root() -> Path | None:
    """寻找本机 GPT-SoVITS 根目录"""
    env_root = os.environ.get("GPT_SOVITS_ROOT", "").strip()
    candidates = []
    if env_root:
        candidates.append(Path(env_root))

    home = Path.home()
    if IS_WINDOWS:
        candidates.extend([
            home / "GPT-SoVITS",
            Path("C:/GPT-SoVITS"),
            Path("D:/GPT-SoVITS"),
        ])
    else:
        candidates.extend([
            home / "GPT-SoVITS",
            home / "projects" / "GPT-SoVITS",
            Path("/opt/GPT-SoVITS"),
        ])

    for candidate in candidates:
        if (candidate / "api_v2.py").exists() and (candidate / "GPT_SoVITS" / "configs" / "tts_infer.yaml").exists():
            return candidate
    return None


def discover_gpt_sovits_python(root: Path) -> str:
    """寻找可用于启动 api_v2.py 的 Python"""
    env_python = os.environ.get("GPT_SOVITS_PYTHON", "").strip()
    candidates = []
    if env_python:
        candidates.append(Path(env_python))

    home = Path.home()
    if IS_WINDOWS:
        candidates.extend([
            home / "miniconda3" / "envs" / "GPTSoVits" / "python.exe",
            root / ".venv" / "Scripts" / "python.exe",
            Path(sys.executable),
        ])
    else:
        candidates.extend([
            home / "miniconda3" / "envs" / "GPTSoVits" / "bin" / "python",
            root / ".venv" / "bin" / "python",
            Path(sys.executable),
        ])

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return sys.executable


def discover_reference_entries(root: Path, experiment_key: str):
    """从训练日志自动挑选中英文参考音频和提示词"""
    manual_entries = {}
    for lang, audio_path, prompt_text, prompt_lang in [
        ("zh", SOVITS_REF_AUDIO_ZH, SOVITS_PROMPT_TEXT_ZH, SOVITS_PROMPT_LANG_ZH),
        ("en", SOVITS_REF_AUDIO_EN, SOVITS_PROMPT_TEXT_EN, SOVITS_PROMPT_LANG_EN),
    ]:
        if not any([audio_path, prompt_text, prompt_lang]):
            continue
        if not all([audio_path, prompt_text, prompt_lang]):
            print(f"  ⚠️ {lang} 手工参考音配置不完整，已忽略。")
            continue
        validated = validate_reference_entry(audio_path, prompt_text, prompt_lang)
        if validated is None:
            continue
        manual_entries[lang] = validated

    if manual_entries:
        if "zh" not in manual_entries and "en" in manual_entries:
            manual_entries["zh"] = manual_entries["en"]
        if "en" not in manual_entries and "zh" in manual_entries:
            manual_entries["en"] = manual_entries["zh"]
        return manual_entries

    overrides_complete = all([SOVITS_REF_AUDIO, SOVITS_PROMPT_TEXT, SOVITS_PROMPT_LANG])
    if overrides_complete:
        validated = validate_reference_entry(SOVITS_REF_AUDIO, SOVITS_PROMPT_TEXT, SOVITS_PROMPT_LANG)
        if validated is None:
            return {}
        return {"zh": validated, "en": validated}

    log_dir = root / "logs" / experiment_key
    name2text_path = log_dir / "2-name2text.txt"
    wav_dir = log_dir / "5-wav32k"

    if not name2text_path.exists() or not wav_dir.exists():
        return {}

    by_lang = {"zh": [], "en": []}
    with open(name2text_path, "r", encoding="utf-8", errors="ignore") as f:
        for raw_line in f:
            line = raw_line.strip()
            if not line:
                continue
            parts = line.split("\t")
            if len(parts) < 4:
                continue
            filename = parts[0].strip()
            prompt_text = parts[-1].strip()
            audio_path = wav_dir / filename
            if not audio_path.exists() or not prompt_text:
                continue
            duration = get_wav_duration(audio_path)
            lang = detect_language(prompt_text)
            by_lang.setdefault(lang, []).append(
                {
                    "audio_path": audio_path,
                    "prompt_text": prompt_text,
                    "prompt_lang": lang,
                    "duration": duration,
                }
            )

    selected = {}
    for lang, items in by_lang.items():
        if not items:
            continue

        valid_single = [
            item
            for item in items
            if is_reference_duration_valid(item["duration"])
        ]
        if valid_single:
            chosen = max(valid_single, key=lambda item: item["duration"])
            validated = validate_reference_entry(
                str(chosen["audio_path"]),
                chosen["prompt_text"],
                chosen["prompt_lang"],
            )
            if validated:
                selected[lang] = validated
            continue

        if not SOVITS_ALLOW_STITCHED_REFERENCE:
            print(
                f"  ⚠️ 未找到可直接使用的 {lang} 参考音频。"
                " 当前已禁用自动拼接短切片，请手工指定一段 3~10 秒连续参考音。"
            )
            continue

        stitched = build_reference_audio(experiment_key, lang, items)
        if stitched:
            validated = validate_reference_entry(
                stitched["audio_path"],
                stitched["prompt_text"],
                stitched["prompt_lang"],
            )
            if validated:
                selected[lang] = validated

    if "zh" not in selected and "en" in selected:
        selected["zh"] = selected["en"]
    if "en" not in selected and "zh" in selected:
        selected["en"] = selected["zh"]
    return selected


def discover_sovits_runtime():
    """自动发现 GPT-SoVITS 安装、权重和参考音频"""
    global SOVITS_RUNTIME
    if SOVITS_RUNTIME is not None:
        return SOVITS_RUNTIME

    root = discover_gpt_sovits_root()
    if root is None:
        print("  ⚠️ 未找到 GPT-SoVITS 安装目录，回退到 Edge-TTS")
        return None

    gpt_weight, sovits_weight, experiment_key = pick_latest_weight_pair(root)
    if gpt_weight is None or sovits_weight is None:
        print("  ⚠️ 未找到成对的 GPT/SoVITS 权重，回退到 Edge-TTS")
        return None

    version = version_from_weight_dir(gpt_weight.parent.name, "GPT_weights")
    references = discover_reference_entries(root, experiment_key)

    runtime = {
        "root": str(root),
        "python_exe": discover_gpt_sovits_python(root),
        "version": version,
        "experiment_key": experiment_key,
        "gpt_weight": str(gpt_weight),
        "sovits_weight": str(sovits_weight),
        "bert_base_path": str(root / "GPT_SoVITS" / "pretrained_models" / "chinese-roberta-wwm-ext-large"),
        "cnhuhbert_base_path": str(root / "GPT_SoVITS" / "pretrained_models" / "chinese-hubert-base"),
        "references": references,
    }
    SOVITS_RUNTIME = runtime

    print(f"  🎯 GPT-SoVITS 实验: {experiment_key}")
    print(f"     版本: {version}")
    print(f"     GPT: {gpt_weight.name}")
    print(f"     SoVITS: {sovits_weight.name}")
    if references:
        langs = ", ".join(sorted(references.keys()))
        print(f"     参考音频: {langs}")
    else:
        print("     参考音频: 未找到可直接使用的 3~10 秒连续参考音")

    return runtime


def yaml_path(path_str: str) -> str:
    """统一 YAML 中的路径写法，避免 Windows 反斜杠歧义"""
    return Path(path_str).as_posix()


def write_sovits_config(runtime: dict) -> str:
    """生成适配当前模型的 tts_infer.yaml"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    yaml_content = f"""custom:
  bert_base_path: {yaml_path(runtime["bert_base_path"])}
  cnhuhbert_base_path: {yaml_path(runtime["cnhuhbert_base_path"])}
  device: cpu
  is_half: false
  t2s_weights_path: {yaml_path(runtime["gpt_weight"])}
  version: {runtime["version"]}
  vits_weights_path: {yaml_path(runtime["sovits_weight"])}
"""
    current = ""
    if os.path.exists(SOVITS_CONFIG_PATH):
        with open(SOVITS_CONFIG_PATH, "r", encoding="utf-8", errors="ignore") as f:
            current = f.read()
    if current != yaml_content:
        with open(SOVITS_CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(yaml_content)
    return SOVITS_CONFIG_PATH


def api_is_ready(timeout: float = 3.0) -> bool:
    """检测本地 GPT-SoVITS API 是否可访问"""
    try:
        with request.urlopen(f"http://{GPT_SOVITS_HOST}:{GPT_SOVITS_PORT}/openapi.json", timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="ignore"))
        return "/tts" in payload.get("paths", {})
    except Exception:
        return False


def call_json_api(url: str, timeout: float = 15.0):
    """调用 JSON API 并返回响应"""
    with request.urlopen(url, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
    if not body:
        return {}
    return json.loads(body)


def ensure_sovits_api(runtime: dict) -> bool:
    """确保 api_v2.py 已按当前权重启动"""
    global SOVITS_API_PROCESS
    global SOVITS_API_LOG_HANDLE

    if api_is_ready():
        return True

    config_path = write_sovits_config(runtime)
    print("  🚀 启动 GPT-SoVITS API...")

    if SOVITS_API_LOG_HANDLE is None:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        SOVITS_API_LOG_HANDLE = open(SOVITS_LOG_PATH, "a", encoding="utf-8", buffering=1)

    cmd = [
        runtime["python_exe"],
        "api_v2.py",
        "-a",
        GPT_SOVITS_HOST,
        "-p",
        str(GPT_SOVITS_PORT),
        "-c",
        config_path,
    ]
    SOVITS_API_PROCESS = subprocess.Popen(
        cmd,
        cwd=runtime["root"],
        stdout=SOVITS_API_LOG_HANDLE,
        stderr=subprocess.STDOUT,
    )

    deadline = time.time() + SOVITS_START_TIMEOUT
    while time.time() < deadline:
        if api_is_ready():
            print("  ✅ GPT-SoVITS API 已就绪")
            return True
        if SOVITS_API_PROCESS.poll() is not None:
            break
        time.sleep(2)

    print("  ❌ GPT-SoVITS API 启动失败")
    log_tail = tail_text(SOVITS_LOG_PATH)
    if log_tail:
        print("  📄 API 日志尾部:")
        print(log_tail)
    return False


def ensure_sovits_models(runtime: dict) -> bool:
    """如果 API 已运行，显式切到当前最新权重"""
    global SOVITS_ACTIVE_MODEL_KEY

    target_key = (runtime["gpt_weight"], runtime["sovits_weight"])
    if SOVITS_ACTIVE_MODEL_KEY == target_key:
        return True

    try:
        gpt_url = (
            f"http://{GPT_SOVITS_HOST}:{GPT_SOVITS_PORT}/set_gpt_weights"
            f"?weights_path={parse.quote(runtime['gpt_weight'])}"
        )
        sovits_url = (
            f"http://{GPT_SOVITS_HOST}:{GPT_SOVITS_PORT}/set_sovits_weights"
            f"?weights_path={parse.quote(runtime['sovits_weight'])}"
        )
        gpt_resp = call_json_api(gpt_url, timeout=30)
        sovits_resp = call_json_api(sovits_url, timeout=30)
        if gpt_resp.get("message") != "success":
            raise RuntimeError(f"set_gpt_weights failed: {gpt_resp}")
        if sovits_resp.get("message") != "success":
            raise RuntimeError(f"set_sovits_weights failed: {sovits_resp}")
        SOVITS_ACTIVE_MODEL_KEY = target_key
        return True
    except Exception as e:
        print(f"  ❌ GPT-SoVITS 切换权重失败: {e}")
        return False


def get_reference_for_text(runtime: dict, text: str):
    """根据题目语言选择对应参考音频"""
    references = runtime.get("references", {})
    if not references:
        return None

    lang = detect_language(text)
    if lang == "mixed":
        if mixed_text_prefers_english(text):
            ref = references.get("en") or references.get("zh")
        else:
            ref = references.get("zh") or references.get("en")
    else:
        ref = references.get(lang) or references.get("zh") or references.get("en")
    return ref


def expected_min_duration(text: str) -> float:
    """按文本长度估算最低可接受时长，用于拦截明显异常的弱音频"""
    units = len(re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]", text))
    return max(0.7, min(4.0, units * 0.08))


def noise_floor_limit(reference_stats: dict | None) -> float:
    """基于参考音频估算可接受的输出底噪上限"""
    reference_floor = 0.0
    if reference_stats:
        reference_floor = reference_stats.get("noise_floor_ratio", 0.0)
    return max(SOVITS_OUTPUT_NOISE_FLOOR_RATIO, reference_floor * 4.0)


def noise_severity(stats: dict, reference_stats: dict | None = None) -> float:
    """给输出噪声程度一个粗略分数，便于比较处理前后谁更干净"""
    floor_norm = stats["noise_floor_ratio"] / max(noise_floor_limit(reference_stats), 1e-6)
    cv_penalty = max(0.0, SOVITS_OUTPUT_CONSTANT_NOISE_CV - stats["energy_cv"]) / max(SOVITS_OUTPUT_CONSTANT_NOISE_CV, 1e-6)
    return floor_norm + cv_penalty * 0.35


def describe_noise_issues(stats: dict, reference_stats: dict | None = None) -> list[str]:
    """判断当前音频是否带有明显底噪"""
    issues = []
    floor_limit = noise_floor_limit(reference_stats)
    if (
        stats["noise_floor_ratio"] > floor_limit
        and stats["energy_cv"] < SOVITS_OUTPUT_CONSTANT_NOISE_CV
    ):
        issues.append(
            "底噪偏高 "
            f"(floor_ratio={stats['noise_floor_ratio']:.3f}, cv={stats['energy_cv']:.3f})"
        )
    elif stats["noise_floor_ratio"] > floor_limit * 1.35:
        issues.append(
            "底噪偏高 "
            f"(floor_ratio={stats['noise_floor_ratio']:.3f})"
        )
    return issues


def validate_generated_audio(output_path: str, text: str, reference: dict) -> None:
    """落盘后快速校验生成结果，避免把明显坏音频继续注入页面"""
    generated = inspect_wav(output_path)
    issues = []

    if generated["duration"] <= 0.3:
        issues.append(f"时长过短 ({generated['duration']:.2f}s)")

    min_duration = expected_min_duration(text) * SOVITS_MIN_DURATION_RATIO
    if generated["duration"] < min_duration:
        issues.append(
            f"时长明显偏短 ({generated['duration']:.2f}s < {min_duration:.2f}s)"
        )

    reference_stats = reference.get("stats")
    if reference_stats:
        mean_abs_ratio = generated["mean_abs"] / max(reference_stats["mean_abs"], 1)
        peak_ratio = generated["peak"] / max(reference_stats["peak"], 1)
        if (
            mean_abs_ratio < SOVITS_MIN_MEAN_ABS_RATIO
            and peak_ratio < SOVITS_MIN_PEAK_RATIO
        ):
            issues.append(
                "能量明显低于参考音频 "
                f"(mean_abs={mean_abs_ratio:.2f}, peak={peak_ratio:.2f})"
            )
        issues.extend(describe_noise_issues(generated, reference_stats))

    if issues:
        raise RuntimeError("；".join(issues))


def _fft_inplace(values: list[complex], invert: bool = False) -> None:
    """小型纯 Python FFT，作为没有 ffmpeg 时的降噪兜底。"""
    n = len(values)
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j ^= bit
        if i < j:
            values[i], values[j] = values[j], values[i]

    length = 2
    while length <= n:
        angle = (2 * math.pi / length) * (1 if invert else -1)
        wlen = complex(math.cos(angle), math.sin(angle))
        for i in range(0, n, length):
            w = 1 + 0j
            half = length // 2
            for k in range(i, i + half):
                u = values[k]
                v = values[k + half] * w
                values[k] = u + v
                values[k + half] = u - v
                w *= wlen
        length <<= 1

    if invert:
        for i in range(n):
            values[i] /= n


def _write_mono_wav(path: Path, samples: list[float], sample_rate: int) -> None:
    import array

    ints = array.array("h")
    for sample in samples:
        value = max(-1.0, min(1.0, sample))
        ints.append(int(round(value * 32767)))

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(ints.tobytes())


def pure_python_spectral_denoise(input_path: Path, output_path: Path) -> bool:
    """无 ffmpeg 时使用频谱减法降噪；主要处理 GPT-SoVITS 常见的恒定底噪。"""
    try:
        import array

        with wave.open(str(input_path), "rb") as wf:
            nchannels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            sample_rate = wf.getframerate()
            frames = wf.getnframes()
            raw = wf.readframes(frames)

        if sampwidth != 2 or frames <= 0:
            return False

        pcm = array.array("h")
        pcm.frombytes(raw)
        if nchannels > 1:
            mono = []
            for index in range(0, len(pcm), nchannels):
                chunk = pcm[index:index + nchannels]
                mono.append(sum(chunk) / max(len(chunk), 1) / 32768.0)
        else:
            mono = [sample / 32768.0 for sample in pcm]

        if len(mono) < sample_rate * 0.25:
            return False

        frame_size = 1024
        hop_size = 256
        if sample_rate <= 16000:
            frame_size = 512
            hop_size = 128

        window = [0.5 - 0.5 * math.cos(2 * math.pi * i / (frame_size - 1)) for i in range(frame_size)]
        frames_data = []
        starts = list(range(0, len(mono), hop_size))
        for start in starts:
            frame = mono[start:start + frame_size]
            if len(frame) < frame_size:
                frame = frame + [0.0] * (frame_size - len(frame))
            rms = math.sqrt(sum(sample * sample for sample in frame) / frame_size)
            spectrum = [complex(frame[i] * window[i], 0.0) for i in range(frame_size)]
            _fft_inplace(spectrum, invert=False)
            frames_data.append((start, rms, spectrum))

        if not frames_data:
            return False

        sorted_frames = sorted(frames_data, key=lambda item: item[1])
        noise_count = max(3, min(len(sorted_frames), int(len(sorted_frames) * 0.22)))
        noise_frames = sorted_frames[:noise_count]
        noise_profile = [0.0] * frame_size
        for _, _, spectrum in noise_frames:
            for index, value in enumerate(spectrum):
                noise_profile[index] += abs(value)
        noise_profile = [value / noise_count for value in noise_profile]

        out = [0.0] * (len(mono) + frame_size)
        norm = [0.0] * (len(mono) + frame_size)
        strength = 1.18
        min_gain = 0.075

        for start, _, spectrum in frames_data:
            cleaned = []
            for index, value in enumerate(spectrum):
                mag = abs(value)
                if mag <= 1e-12:
                    cleaned.append(0j)
                    continue
                noise_mag = noise_profile[index]
                gain = 1.0 - strength * noise_mag / mag
                if mag < noise_mag * 1.8:
                    gain = min(gain, min_gain)
                gain = max(min_gain, min(1.0, gain))

                freq = min(index, frame_size - index) * sample_rate / frame_size
                if freq < 70 or freq > 13500:
                    gain *= 0.20
                cleaned.append(value * gain)

            _fft_inplace(cleaned, invert=True)
            for i in range(frame_size):
                pos = start + i
                weighted = cleaned[i].real * window[i]
                out[pos] += weighted
                norm[pos] += window[i] * window[i]

        processed = []
        for i in range(len(mono)):
            if norm[i] > 1e-8:
                processed.append(out[i] / norm[i])
            else:
                processed.append(out[i])

        # 轻量下扩展：把明显低于语音能量的片段压低，减少句首句尾沙沙声。
        gate_frame = max(1, int(sample_rate * 0.025))
        rms_values = []
        for start in range(0, len(processed), gate_frame):
            chunk = processed[start:start + gate_frame]
            if chunk:
                rms_values.append(math.sqrt(sum(x * x for x in chunk) / len(chunk)))
        floor = percentile(rms_values, 0.20)
        speech = max(percentile(rms_values, 0.82), 1e-6)
        gate_threshold = max(floor * 2.2, speech * 0.035)
        for start in range(0, len(processed), gate_frame):
            chunk = processed[start:start + gate_frame]
            if not chunk:
                continue
            rms = math.sqrt(sum(x * x for x in chunk) / len(chunk))
            if rms < gate_threshold:
                factor = 0.18 + 0.82 * (rms / max(gate_threshold, 1e-9))
                for i in range(start, min(start + gate_frame, len(processed))):
                    processed[i] *= factor

        original_peak = max(max(abs(x) for x in mono), 1e-9)
        peak = max(max(abs(x) for x in processed), 1e-9)
        # 频谱减法会降低整体音量；这里按峰值补回，避免后续“人声受损”校验误判。
        target_peak = min(0.92, original_peak * 0.98)
        if peak < target_peak:
            gain = min(3.0, target_peak / peak)
            processed = [x * gain for x in processed]
            peak = max(max(abs(x) for x in processed), 1e-9)
        if peak > 0.98:
            processed = [x * (0.98 / peak) for x in processed]

        _write_mono_wav(output_path, processed, sample_rate)
        return True
    except Exception as exc:
        print(f"  ⚠️ 内置频谱降噪失败: {exc}")
        return False


def postprocess_generated_audio(output_path: str, reference_stats: dict | None = None) -> None:
    """对生成结果做一层降噪，降低背景底噪"""
    if not SOVITS_POSTPROCESS_GENERATED_AUDIO:
        return

    raw_stats = inspect_wav(output_path)
    if raw_stats["noise_floor_ratio"] <= max(SOVITS_POSTPROCESS_TRIGGER_NOISE_FLOOR_RATIO, noise_floor_limit(reference_stats) * 0.75):
        return

    src = Path(output_path)
    tmp = src.with_name(f"{src.stem}.post.wav")

    ffmpeg = resolve_ffmpeg_exe()
    if ffmpeg:
        cmd = [
            ffmpeg,
            "-y",
            "-i",
            str(src),
            "-af",
            SOVITS_POSTPROCESS_FILTER,
            "-ac",
            "1",
            "-ar",
            "32000",
            str(tmp),
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            timeout=180,
        )
        if result.returncode != 0 or not tmp.exists():
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            err = result.stderr[-400:].strip() if result.stderr else "unknown ffmpeg error"
            print(f"  ⚠️ ffmpeg 降噪失败，改用内置频谱降噪: {err}")
            if not pure_python_spectral_denoise(src, tmp):
                return
    else:
        print("  ⚠️ 未找到 ffmpeg，使用内置频谱降噪。")
        if not pure_python_spectral_denoise(src, tmp):
            print("  ⚠️ 内置降噪失败，保留原音频。")
            return

    processed_stats = inspect_wav(tmp)
    raw_noise = noise_severity(raw_stats, reference_stats)
    processed_noise = noise_severity(processed_stats, reference_stats)
    speech_keep_ratio = processed_stats["mean_abs"] / max(raw_stats["mean_abs"], 1)

    if (
        processed_noise <= raw_noise * (1 - SOVITS_POSTPROCESS_MIN_NOISE_IMPROVEMENT)
        and speech_keep_ratio >= SOVITS_POSTPROCESS_KEEP_MEAN_ABS_RATIO
        and processed_stats["duration"] >= raw_stats["duration"] * 0.98
    ):
        os.replace(tmp, src)
        print(
            "     已应用生成后降噪 "
            f"(noise {raw_stats['noise_floor_ratio']:.3f} -> {processed_stats['noise_floor_ratio']:.3f})"
        )
    else:
        tmp.unlink(missing_ok=True)
        print("     跳过生成后降噪: 降噪收益不够或人声受损风险偏高")


def request_sovits_wav(req_data: dict, output_path: str) -> None:
    """向本地 GPT-SoVITS 请求一条 wav 并落盘"""
    req = request.Request(
        SOVITS_API_URL,
        data=json.dumps(req_data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with request.urlopen(req, timeout=SOVITS_API_TIMEOUT) as response:
        audio_bytes = response.read()
        content_type = response.headers.get("Content-Type", "")

    if not audio_bytes:
        raise RuntimeError("empty response body")

    if "application/json" in content_type:
        raise RuntimeError(audio_bytes.decode("utf-8", errors="ignore"))

    with open(output_path, "wb") as f:
        f.write(audio_bytes)


async def generate_audio_edge(text: str, output_path: str) -> float:
    """备用 Edge-TTS"""
    if edge_tts is None:
        print("  ❌ edge-tts not installed. Run: python3 -m pip install edge-tts")
        return 0
    voice = get_voice(text)
    print(f"  🔊 TTS (Edge): {voice}")
    communicate = edge_tts.Communicate(text, voice, rate=RATE)
    await communicate.save(output_path)
    return max(2.0, len(text) * 0.15)


async def generate_audio_sovits(text: str, output_path: str) -> float:
    """调用本地 GPT-SoVITS 生成克隆声音"""
    runtime = discover_sovits_runtime()
    if runtime is None:
        return 0

    reference = get_reference_for_text(runtime, text)
    if reference is None:
        print("  ❌ 未找到参考音频/提示词，本地模型无法发音")
        return 0

    if not ensure_sovits_api(runtime):
        return 0
    if not ensure_sovits_models(runtime):
        return 0

    text_lang = detect_language(text)
    sovits_text_lang = to_sovits_lang(text_lang)
    sovits_prompt_lang = to_sovits_lang(reference["prompt_lang"])
    print(f"  🔊 TTS (GPT-SoVITS): {runtime['version']} / {sovits_text_lang}")
    print(f"     参考音: {os.path.basename(reference['audio_path'])}")
    req_base = {
        "text_lang": sovits_text_lang,
        "ref_audio_path": reference["audio_path"],
        "prompt_text": reference["prompt_text"],
        "prompt_lang": sovits_prompt_lang,
        "text_split_method": "cut5",
        "batch_size": 1,
        "media_type": "wav",
        "streaming_mode": False,
    }

    try:
        english_word_count = len(re.findall(r"[a-zA-Z]+", text))
        if (
            text_lang == "en"
            and english_word_count >= SOVITS_ENGLISH_RESCORING_MIN_WORDS
            and get_sovits_asr_model() is not None
        ):
            candidates = english_rescoring_candidates(text)
            print(f"     English 候选打分: {len(candidates)} 个")
            best = None
            output_path_obj = Path(output_path)
            for index, candidate_text in enumerate(candidates, 1):
                candidate_path = output_path_obj.with_name(f"{output_path_obj.stem}.cand{index}.wav")
                req_data = {**req_base, "text": candidate_text}
                print(f"       候选 {index}: {candidate_text}")
                request_sovits_wav(req_data, str(candidate_path))
                recognized = transcribe_english_audio_for_score(str(candidate_path))
                score = score_asr_match(text, recognized)
                print(f"         ASR: {recognized!r}")
                print(f"         分数: {score:.3f}")
                if best is None or score > best["score"]:
                    best = {
                        "score": score,
                        "candidate_text": candidate_text,
                        "candidate_path": candidate_path,
                        "recognized": recognized,
                    }

            if best is None:
                raise RuntimeError("english rescoring produced no candidates")

            for index, candidate_text in enumerate(candidates, 1):
                candidate_path = output_path_obj.with_name(f"{output_path_obj.stem}.cand{index}.wav")
                if candidate_path == best["candidate_path"]:
                    continue
                candidate_path.unlink(missing_ok=True)

            print(f"     采用候选: {best['candidate_text']}")
            print(f"     候选转写: {best['recognized']!r}")
            os.replace(best["candidate_path"], output_path)
        else:
            normalized_text = normalize_sovits_text(text, text_lang)
            if normalized_text != text:
                print(f"     文本标准化: {normalized_text}")
            req_data = {**req_base, "text": normalized_text}
            request_sovits_wav(req_data, output_path)

        postprocess_generated_audio(output_path, reference.get("stats"))

        if SOVITS_VALIDATE_OUTPUT:
            validate_generated_audio(output_path, text, reference)

        return max(3.0, len(text) * 0.25)
    except error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        print(f"  ❌ GPT-SoVITS HTTP 错误: {e.code} {error_body}")
        return 0
    except Exception as e:
        print(f"  ❌ GPT-SoVITS 失败: {e}")
        return 0


async def generate_audio(text: str, output_path: str) -> float:
    """直接调用本地 GPT-SoVITS"""
    dur = await generate_audio_sovits(text, output_path)
    if dur <= 0:
        print("  ❌ 本地生成彻底失败。")
        return 0
    return dur


def audio_to_base64(audio_path: str) -> str:
    """音频文件编码为 base64"""
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


# ============================
# 💉 JavaScript 注入
# ============================

JS_INSTALL_HOOK = """
    if (!window._gumHookInstalled) {
        window._gumHookInstalled = true;
        window._originalGUM = navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices);
        window._injectedDuration = 0;

        // Pre-create AudioContext (may start suspended - that's OK)
        const AudioCtxParams = window.AudioContext || window.webkitAudioContext;
        window._sharedAudioContext = new AudioCtxParams();
        window._sharedAudioDest = window._sharedAudioContext.createMediaStreamDestination();
        console.log('[Hook] AudioContext pre-created, state: ' + window._sharedAudioContext.state);

        window._playInjectedAudio = async (base64string) => {
            try {
                // Resume if needed (requires user gesture from Record click)
                if (window._sharedAudioContext.state === 'suspended') {
                    console.log('[Hook] Resuming suspended AudioContext...');
                    await window._sharedAudioContext.resume();
                }

                const binaryString = atob(base64string);
                const bytes = new Uint8Array(binaryString.length);
                for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }

                const audioBuffer = await window._sharedAudioContext.decodeAudioData(bytes.buffer.slice(0));
                window._injectedDuration = audioBuffer.duration;
                console.log('[Hook] Playing audio: ' + audioBuffer.duration.toFixed(1) + 's');

                const source = window._sharedAudioContext.createBufferSource();
                source.buffer = audioBuffer;
                source.connect(window._sharedAudioDest);
                source.start(0);
                source.onended = () => console.log('[Hook] Audio playback finished.');

                return audioBuffer.duration;
            } catch (err) {
                console.error('[Hook Play] Error decoding/playing:', err);
                return 0;
            }
        };

        navigator.mediaDevices.getUserMedia = async (constraints) => {
            console.log('[Hook] App requested getUserMedia, returning shared injected stream');
            if (constraints && constraints.audio) {
                return window._sharedAudioDest.stream;
            }
            return window._originalGUM(constraints);
        };

        console.log('[Hook] Successfully installed over navigator.mediaDevices.getUserMedia');
    }
"""

JS_SET_AUDIO = """
async (audioBase64) => {
    return await window._playInjectedAudio(audioBase64);
}
"""

JS_READ_UTTERANCE = """
() => {
    const iframes = document.querySelectorAll('iframe');
    for (const iframe of iframes) {
        try {
            const doc = iframe.contentDocument || iframe.contentWindow.document;
            if (doc && doc.body) {
                const myText = doc.querySelector('.my_text');
                if (myText && myText.textContent.trim()) {
                    return myText.textContent.trim();
                }
                const text = doc.body.innerText.trim();
                if (text && text.length > 0 && text.length < 500) {
                    return text;
                }
            }
        } catch (e) {
        }
    }

    const bodyText = document.body.innerText;
    const match = bodyText.match(/Utterance:\\s*\\n([^\\n]+)/);
    if (match && !match[1].trim().startsWith('Recording')) {
        return match[1].trim();
    }

    return null;
}
"""

JS_FILL_VALIDATION = """
() => {
    const groups = new Map();
    const radios = Array.from(document.querySelectorAll('input[type="radio"]'));

    for (const radio of radios) {
        const key = radio.name || `group-${groups.size}`;
        if (!groups.has(key)) {
            groups.set(key, []);
        }
        groups.get(key).push(radio);
    }

    const results = [];
    for (const [groupName, items] of groups.entries()) {
        const yesRadio = items.find((radio) => (radio.value || '').trim().toLowerCase() === 'yes');
        if (!yesRadio) {
            continue;
        }

        yesRadio.checked = true;
        yesRadio.click();
        yesRadio.dispatchEvent(new Event('change', { bubbles: true }));
        yesRadio.dispatchEvent(new Event('input', { bubbles: true }));
        results.push(groupName);
    }

    return results;
}
"""


# ============================
# 🤖 主流程
# ============================

async def click_button_by_text(page, text_pattern: str, timeout: int = 3000) -> bool:
    """通过多策略查找并点击按钮"""
    regex = re.compile(text_pattern, re.IGNORECASE)
    locators = [
        page.get_by_role("button", name=regex).first,
        page.locator("button").filter(has_text=regex).first,
        page.locator('[role="button"]').filter(has_text=regex).first,
    ]

    for locator in locators:
        try:
            await locator.wait_for(state="visible", timeout=timeout)
            await locator.click()
            return True
        except PlaywrightTimeoutError:
            continue
        except Exception:
            continue

    return await page.evaluate(
        """
        (pattern) => {
            const regex = new RegExp(pattern, 'i');
            const candidates = document.querySelectorAll(
                'button, [role="button"], input[type="button"], input[type="submit"]'
            );

            for (const el of candidates) {
                const text = (el.innerText || el.textContent || el.value || '').trim();
                if (!text || !regex.test(text)) {
                    continue;
                }
                el.click();
                return true;
            }
            return false;
        }
        """,
        text_pattern,
    )


async def wait_for_upload_success(page, timeout: int = 10000) -> bool:
    """等待上传完成的页面反馈"""
    try:
        await page.get_by_text("File uploaded successfully", exact=False).first.wait_for(
            state="visible",
            timeout=timeout,
        )
        return True
    except PlaywrightTimeoutError:
        pass

    try:
        await page.get_by_role("button", name=re.compile("delete", re.IGNORECASE)).first.wait_for(
            state="visible",
            timeout=2000,
        )
        return True
    except PlaywrightTimeoutError:
        return False


async def fill_validation(page):
    """填两个 Yes — 必须用 Playwright 真实点击，JS 直接改 checked 不会更新 React 状态。"""
    results = []
    try:
        radios = await page.locator('input[type="radio"]').all()
        clicked_names: set[str] = set()
        for radio in radios:
            value = (await radio.get_attribute("value") or "").strip().lower()
            name = await radio.get_attribute("name") or ""
            if value != "yes" or name in clicked_names:
                continue
            await radio.click(force=True)
            clicked_names.add(name)
            results.append(name)
            await asyncio.sleep(0.3)

        verified = await page.evaluate(
            """
            () => {
              const groups = new Map();
              for (const r of document.querySelectorAll('input[type="radio"]')) {
                const key = r.name || `group-${groups.size}`;
                if (!groups.has(key)) groups.set(key, false);
                if ((r.value || '').trim().toLowerCase() === 'yes' && r.checked) {
                  groups.set(key, true);
                }
              }
              return [...groups.values()].every(Boolean);
            }
            """
        )
        return results if verified else []
    except Exception:
        return []


async def run_single_task(page, task_count: int) -> bool:
    """执行单个任务"""
    print(f"\n{'=' * 50}")
    print(f"  Task #{task_count}")
    print(f"{'=' * 50}")

    body_text = await page.evaluate("document.body.innerText || ''")
    if "Speech Human Recording" not in body_text:
        print("  ⚠️ 当前页面不是 Speech Human Recording，停止，避免误操作其它 TryRating 题型。")
        return False

    utterance = await page.evaluate(JS_READ_UTTERANCE)
    if not utterance:
        print("  ⚠️ No Utterance found")
        return False

    print(f"  📝 Utterance: {utterance}")

    audio_path = os.path.join(OUTPUT_DIR, f"task_{task_count}.wav")
    print("  🔊 Generating audio...")
    duration_hint = await generate_audio(utterance, audio_path)

    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        print("  ❌ Audio generation failed")
        return False

    size_kb = os.path.getsize(audio_path) / 1024
    print(f"  ✅ Audio ready ({size_kb:.1f} KB)")

    print("  🔴 Clicking Record...")
    clicked = await click_button_by_text(page, "record")
    if not clicked:
        print("  ❌ Record button not found")
        return False

    await asyncio.sleep(1.0)

    audio_b64 = audio_to_base64(audio_path)
    duration = await page.evaluate(JS_SET_AUDIO, audio_b64)
    if duration <= 0:
        duration = duration_hint

    print(f"  💉 Audio injected and playing ({duration:.1f}s)")
    print(f"  ⏳ Recording... ({duration:.1f}s + buffer)")
    await asyncio.sleep(duration + 2.0)

    try:
        stop_btn = page.get_by_role("button", name=re.compile("stop", re.IGNORECASE)).first
        if await stop_btn.is_visible():
            await stop_btn.click()
            print("  ⏹️ Stopped")
            await asyncio.sleep(1)
    except Exception:
        pass

    print("  📤 Uploading...")
    upload_clicked = await click_button_by_text(page, "upload")
    if not upload_clicked:
        print("  ❌ Upload button not found")
        return False

    if await wait_for_upload_success(page):
        print("  ✅ Upload success")
    else:
        print("  ⚠️ 未检测到明确的上传成功提示，继续尝试填写 validation")

    print("  📝 Filling validation...")
    results = await fill_validation(page)
    if results:
        print(f"     ✅ Selected Yes for {len(results)} group(s)")
    else:
        print("     ⚠️ Validation radios not confirmed by script")

    print(f"\n  ✅ Task #{task_count} DONE!")
    return True


async def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print()
    print("=" * 50)
    print("  🎙️  Speech Recording Automation")
    print("=" * 50)
    print()
    print(f"  Chrome Profile : {CHROME_PROFILE}")
    print(f"  Auto Submit    : {'ON ⚠️' if AUTO_SUBMIT else 'OFF (safe)'}")
    print()

    if USE_GPT_SOVITS:
        runtime = discover_sovits_runtime()
        if runtime is not None:
            if not runtime.get("references"):
                print("  ❌ 未找到可用参考音频。请在配置区手工填写 SOVITS_REF_AUDIO / SOVITS_PROMPT_TEXT / SOVITS_PROMPT_LANG。")
                return
            ensure_sovits_api(runtime)
            ensure_sovits_models(runtime)
        else:
            print("  ⚠️ 本地 GPT-SoVITS 不可用！由于已禁用 Edge-TTS，脚本将无法生成语音。")

    if SPEECH_CDP_URL:
        print(f"  ✅ 使用现有浏览器 CDP: {SPEECH_CDP_URL}")
    elif not is_port_in_use(CHROME_DEBUG_PORT):
        launch_chrome()
        print("  ⏳ Waiting for Chrome debug port to open...")
        if not wait_for_port(CHROME_DEBUG_PORT, timeout=15):
            print(f"\n  ❌ Chrome 启动后端口 {CHROME_DEBUG_PORT} 未开放！")
            print("     可能原因: Chrome 后台僵尸进程残留、防火墙拦截、或 Chrome 安装损坏。")
            print("     请手动在任务管理器里结束所有 chrome.exe 后重试。")
            return
        print(f"  ✅ Chrome debug port {CHROME_DEBUG_PORT} is ready!")
    else:
        print(f"  ✅ Chrome is already running on port {CHROME_DEBUG_PORT}, skipping launch")

    print("  📡 Connecting via Playwright...")
    async with async_playwright() as p:
        browser = None
        for attempt in range(5):
            try:
                browser = await p.chromium.connect_over_cdp(SPEECH_CDP_URL or f"http://localhost:{CHROME_DEBUG_PORT}")
                break
            except Exception as e:
                if attempt < 4:
                    print(f"  ⏳ Retry {attempt + 1}/5...")
                    await asyncio.sleep(2)
                else:
                    print(f"\n  ❌ Cannot connect to Chrome: {e}")
                    print("  Please make sure ALL Chrome windows are closed first!")
                    return

        print("  ✅ Connected to Chrome")

        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()

        print("  🌐 Navigating to task page...")
        await page.goto(TASK_URL, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        print(f"  📄 Page: {page.url}")

        if "login" in page.url.lower() or "auth" in page.url.lower():
            print("\n  ⚠️ Login required! Please log in manually in the Chrome window.")
            print("  After logging in and reaching the task page, press Enter here.")
            input("  >>> Press Enter to continue...")
            await asyncio.sleep(2)

        print("  🔧 Installing audio hook (Init Script)...")
        await context.add_init_script(JS_INSTALL_HOOK)

        print("  🔄 Reloading page so the audio hook takes effect...")
        await page.reload(wait_until="domcontentloaded")
        await asyncio.sleep(4)
        print("  ✅ Hook is active.")

        task_count = 0

        while True:
            task_count += 1

            try:
                success = await run_single_task(page, task_count)
            except Exception as e:
                print(f"\n  ❌ Error: {e}")
                import traceback
                traceback.print_exc()
                success = False

            if not success:
                retry = input("\n  Retry? (y/n): ").strip().lower()
                if retry == "y":
                    task_count -= 1
                    continue
                break

            if AUTO_SUBMIT:
                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                print(f"  ⏳ Submitting in {delay:.1f}s...")
                await asyncio.sleep(delay)
                await click_button_by_text(page, "submit rating")
                print("  🚀 Submitted!")
                await asyncio.sleep(3)
            else:
                print()
                print("  ⏸️  Check result, then click Submit Rating manually")
                user_input = input("  >>> Press Enter for next task (q = quit): ").strip()
                if user_input.lower() == "q":
                    break

                print("  ⏳ Loading next task...")
                await asyncio.sleep(3)

    print("\n🏁 Done!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted (Ctrl+C)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
