import wave
import sys
import os

ref_path = r'D:\oneform\generated_audio\sovits_refs\myvoice_cpu_v2pro_en_ref.wav'
try:
    with wave.open(ref_path, 'rb') as wf:
        print('Channels:', wf.getnchannels())
        print('SampWidth:', wf.getsampwidth())
        print('Framerate:', wf.getframerate())
        print('Frames:', wf.getnframes())
        
        # Read the first few bytes
        data = wf.readframes(10)
        print('First 10 bytes:', data)
except Exception as e:
    print('Wave module failed:', e)

try:
    import numpy as np
    # Check max and min to see if it's garbage
    with wave.open(ref_path, 'rb') as wf:
        raw = wf.readframes(1000)
        dt = np.int16 if wf.getsampwidth() == 2 else np.int32
        arr = np.frombuffer(raw, dtype=dt)
        print('Sample values array min/max:', arr.min(), arr.max())
except Exception as e:
    print('Numpy failed:', e)
