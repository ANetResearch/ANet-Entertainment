#!/usr/bin/env python3
"""Turn each music/<cue>_<n>.wav (15s stem) into a seamless loop music/loops/<cue>.wav (tail cross-faded into head, level-matched).
Take per cue from film/music_pick.json ({"cue": n}), default 1."""
import json, os, glob, wave, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pf = f"{ROOT}/film/music_pick.json"
pick = json.load(open(pf)) if os.path.exists(pf) else {}
os.makedirs(f"{ROOT}/music/loops", exist_ok=True)
for cue in sorted({os.path.basename(f).rsplit("_", 1)[0] for f in glob.glob(f"{ROOT}/music/*_[0-9].wav")}):
    src = f"{ROOT}/music/{cue}_{pick.get(cue, 1)}.wav"
    if not os.path.exists(src): continue
    w = wave.open(src); sr, ch = w.getframerate(), w.getnchannels()
    x = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32).reshape(-1, ch) / 32768
    x = x[int(0.3 * sr): len(x) - int(0.3 * sr)]
    c = int(2.5 * sr)
    ramp = np.linspace(0, 1, c, dtype=np.float32)[:, None]
    body = x[c: len(x) - c]
    tail = x[len(x) - c:] * np.sqrt(1 - ramp) + x[:c] * np.sqrt(ramp)     # equal-power: end melts into the beginning
    y = np.concatenate([body, tail])
    rms = float(np.sqrt((y ** 2).mean())) or 1e-6
    y = np.clip(y * (10 ** (-20 / 20) / rms), -0.98, 0.98)                # every loop at -20 dBFS RMS
    o = wave.open(f"{ROOT}/music/loops/{cue}.wav", "w"); o.setnchannels(ch); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes((y * 32767).astype(np.int16).tobytes()); o.close()
    print(cue, f"take {pick.get(cue, 1)}", f"{len(y) / sr:.1f}s loop")
