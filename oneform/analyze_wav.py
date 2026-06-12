import wave
import numpy as np

def is_static_noise(wav_path):
    with wave.open(wav_path, 'rb') as wf:
        frames = wf.readframes(wf.getnframes())
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32)

    # Normalize
    audio = audio / np.max(np.abs(audio))

    # Split into chunks of 100ms
    sr = wf.getframerate()
    chunk_size = int(sr * 0.1)
    
    energies = []
    for i in range(0, len(audio), chunk_size):
        chunk = audio[i:i+chunk_size]
        if len(chunk) == chunk_size:
            energies.append(np.mean(chunk**2))
            
    # Characteristics of static noise from models:
    # 1. Extremely constant energy (low variance in volume across chunks)
    # 2. Or very high amplitude everywhere.
    
    mean_energy = np.mean(energies)
    std_energy = np.std(energies)
    
    energy_cv = std_energy / mean_energy  # Coefficient of Variation
    
    print(f"Energy CV (Coefficient of Variation): {energy_cv:.4f}")
    if energy_cv < 0.2:
        print("Verdict: This is highly likely CONSTANT NOISE (Static/Current noise).")
    elif energy_cv > 0.8:
        print("Verdict: This is highly likely SPEECH (high dynamic range, pauses).")
    else:
        print("Verdict: Ambiguous, but leaning towards noise with some variance.")
        
is_static_noise(r'd:\oneform\test_api.wav')
