#!/usr/bin/env python3
"""Music detection for unscored documentary takes: three-model vote (Gemini flash family through gravitex, strict
question) plus an objective tonality measure (sustained spectral peaks that start and stop at different pitches,
as notes do; constant hum and speech harmonics do not count).
usage: music_check.py file.mp4 [...]   (prints JSON per file)"""
import base64, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg as _cfg

G = _cfg.load()["gravitex"]
MODELS = ("gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash")
Q = ('You are an audio engineer checking a documentary location recording. Is there any NON-DIEGETIC MUSIC (score, '
     'instruments playing a melody or chords, synth pads, guitar, piano, strings) anywhere in this clip? Machine hum, '
     'room tone, wind, water, breath, alarms, beeps and voices are NOT music. Answer JSON only: {"music": true/false, '
     '"confidence": 0-1, "where": "time range in seconds or empty", "what": "short description"}')


def _audio(mp4, rate=16000):
    return subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp4, "-vn", "-ac", "1", "-ar", str(rate), "-b:a", "48k",
                           "-f", "mp3", "-"], capture_output=True).stdout


def vote(mp4):
    a = base64.b64encode(_audio(mp4)).decode()

    def ask(model):
        body = {"model": model, "messages": [{"role": "user", "content": [{"type": "text", "text": Q},
                {"type": "input_audio", "input_audio": {"data": a, "format": "mp3"}}]}]}
        for _ in range(3):
            try:
                r = requests.post(G["url"] + "/v1/chat/completions", headers={"Authorization": "Bearer " + G["key"]},
                                  json=body, timeout=90)
                d = json.loads(re.search(r"\{.*\}", r.json()["choices"][0]["message"]["content"], re.S).group(0))
                return {"model": model, "music": bool(d.get("music")), "what": d.get("what", "")}
            except Exception:
                continue
        return {"model": model, "music": None}
    with ThreadPoolExecutor(3) as ex:
        return list(ex.map(ask, MODELS))


def tonality(mp4, sr=16000):
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp4, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    n, hop = 4096, 512
    if len(x) < n * 2:
        return {"notes": 0, "notes_per_10s": 0.0}
    win = np.hanning(n)
    frames = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * win
    S = 20 * np.log10(np.abs(np.fft.rfft(frames, axis=1)) + 1e-9)
    f = np.fft.rfftfreq(n, 1 / sr)
    band = (f > 120) & (f < 3000)
    S = S[:, band]
    # local prominence over +-40 bins
    from numpy.lib.stride_tricks import sliding_window_view as sw
    pad = np.pad(S, ((0, 0), (40, 40)), mode="edge")
    med = np.median(sw(pad, 81, axis=1), axis=2)
    peak = (S - med > 14) & (S > S.max() - 60)
    # sustained: same bin (+-1) for >= 0.3 s
    need = int(0.3 * sr / hop)
    pk = peak | np.roll(peak, 1, axis=1) | np.roll(peak, -1, axis=1)
    T = pk.shape[0]
    run = np.zeros_like(pk, dtype=np.int32)
    segs = []
    for t in range(T):
        run[t] = (run[t - 1] + 1) * pk[t] if t else pk[t]
        if t:
            ended = (run[t - 1] >= need) & (run[t] == 0)
            for b in np.nonzero(ended)[0]:
                segs.append((t - run[t - 1][b], t, b))
    for b in np.nonzero(run[-1] >= need)[0]:
        segs.append((T - run[-1][b], T, b))
    # constant tones (hum) span most of the clip: not notes
    notes = [s for s in segs if (s[1] - s[0]) < 0.7 * T]
    # merge duplicates of the same note on neighbouring bins
    keys = {(s[0] // 4, s[2] // 3) for s in notes}
    dur = len(x) / sr
    return {"notes": len(keys), "notes_per_10s": round(len(keys) * 10 / dur, 1)}


def check(mp4):
    # tonality() is kept as an experiment only: speech harmonics make it unreliable, so it does not decide.
    v = vote(mp4)
    yes = sum(1 for r in v if r["music"])
    return {"votes": f"{yes}/{sum(1 for r in v if r['music'] is not None)}", "what": [r.get("what") for r in v if r["music"]],
            "music": yes >= 2}


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(os.path.basename(p), json.dumps(check(p), ensure_ascii=False), flush=True)
