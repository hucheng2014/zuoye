import os
import sys

# Get root from auto_speech
sys.path.append(os.path.dirname(__file__))
from auto_speech import discover_gpt_sovits_root

root = discover_gpt_sovits_root()
if not root:
    print('Failed to find GPT-SoVITS root')
    sys.exit(1)

tts_path = root / 'GPT_SoVITS' / 'TTS.py'
if not tts_path.exists():
    tts_path = root / 'TTS' / 'TTS.py'
if not tts_path.exists():
    import glob
    matches = glob.glob(str(root) + '/**/TTS.py', recursive=True)
    tts_path = matches[0] if matches else None

if not tts_path:
    print('Failed to find TTS.py')
    sys.exit(1)

print('Patching:', tts_path)

with open(tts_path, 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Look for soundfile read
pattern1 = re.compile(r'prompt_audio,\s*sr\s*=\s*soundfile\.read\([^)]+\)')
pattern2 = re.compile(r'prompt_audio,\s*sr\s*=\s*sf\.read\([^)]+\)')

new_code = '''
            import soundfile as sf
            import torch
            prompt_audio_np, sr = sf.read(ref_audio_path)
            prompt_audio = torch.FloatTensor(prompt_audio_np)
            if len(prompt_audio.shape) == 1:
                prompt_audio = prompt_audio.unsqueeze(0)
            else:
                prompt_audio = prompt_audio.T
'''

if pattern1.search(content):
    content = pattern1.sub(new_code, content, count=1)
    print("Patched soundfile.read!")
elif pattern2.search(content):
    content = pattern2.sub(new_code, content, count=1)
    print("Patched sf.read!")
else:
    print("Could not find the soundfile.read line. The file might already be fixed or looks different.")

with open(tts_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Success.')
