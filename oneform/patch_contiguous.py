import os
import sys
import re

sys.path.append(os.path.dirname(__file__))
from auto_speech import discover_gpt_sovits_root

root = discover_gpt_sovits_root()
if not root:
    print('Failed to find GPT-SoVITS root')
    sys.exit(1)

tts_path = root / 'GPT_SoVITS' / 'TTS_infer_pack' / 'TTS.py'
if not tts_path.exists():
    print('Failed to find TTS.py at', tts_path)
    sys.exit(1)

with open(tts_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix non-contiguous memory issue on torch.from_numpy which causes 
# torch.stft to output pure static/NaNs.
pattern = re.compile(r'raw_audio\s*=\s*torch\.from_numpy\(raw_audio\.T\)')
fixed_line = 'raw_audio = torch.from_numpy(raw_audio.T.copy())'

if pattern.search(content):
    content = pattern.sub(fixed_line, content)
    with open(tts_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ 成功为您修复了 TTS.py！已解决由于 Numpy 倒置导致张量内存不连续，进而在 CPU Inference 中产生纯电流声的底层 BUG。")
else:
    print("⚠️ 未找到匹配的 .T 倒置代码。可能已经修复或者位置变动。")

