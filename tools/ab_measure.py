#!/usr/bin/env python3
"""Measure container/stream facts and per-frame sharpness for A/B clip pairs.  usage: ab_measure.py DIR EP  -> DIR/metrics.json"""
import json, os, re, subprocess, sys, glob
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d, ep = sys.argv[1], sys.argv[2]


def probe(f):
    e = subprocess.run([FF, "-hide_banner", "-i", f], capture_output=True, text=True).stderr
    v = re.search(r"Video: (\w+) \(([^)]*)\).*?, (yuv\w+).*?, (\d+)x(\d+).*?, (\d+) kb/s, ([\d.]+) fps", e)
    a = re.search(r"Audio: (\w+).*?(\d+) Hz, (\w+).*?(\d+) kb/s", e)
    du = re.search(r"Duration: (\d+):(\d+):([\d.]+)", e)
    return {"w": int(v[4]), "h": int(v[5]), "fps": float(v[7]), "vcodec": v[1], "profile": v[2], "pix": v[3], "v_kbps": int(v[6]),
            "dur": round(int(du[1]) * 3600 + int(du[2]) * 60 + float(du[3]), 2), "size_mb": round(os.path.getsize(f) / 1e6, 2),
            "acodec": a and a[1], "a_hz": a and int(a[2]), "a_ch": a and a[3], "a_kbps": a and int(a[4])}


def sharp(f, w, h):
    raw = subprocess.run([FF, "-v", "0", "-i", f, "-vf", "fps=4", "-pix_fmt", "gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    lap = fr[:, 1:-1, 1:-1] * 4 - fr[:, :-2, 1:-1] - fr[:, 2:, 1:-1] - fr[:, 1:-1, :-2] - fr[:, 1:-1, 2:]
    gx = np.abs(np.diff(fr, axis=2)); gy = np.abs(np.diff(fr, axis=1))
    # share of spectral energy above 1/4 Nyquist (detail actually present, independent of contrast)
    F = np.abs(np.fft.fftshift(np.fft.fft2(fr - fr.mean(axis=(1, 2), keepdims=True)), axes=(1, 2))) ** 2
    yy, xx = np.mgrid[-h // 2:h - h // 2, -w // 2:w - w // 2]; r = np.sqrt((yy / (h / 2)) ** 2 + (xx / (w / 2)) ** 2)
    hf = F[:, r > 0.25].sum(axis=1) / F.sum(axis=(1, 2))
    return {"lap_var": round(float(np.median(lap.var(axis=(1, 2)))), 1), "grad_mean": round(float(np.median((gx.mean(axis=(1, 2)) + gy.mean(axis=(1, 2))) / 2)), 2),
            "hf_share_pct": round(float(np.median(hf)) * 100, 3), "edge_p99": round(float(np.median(np.percentile(gx, 99, axis=(1, 2)))), 1)}


res = {}
for nf in sorted(glob.glob(f"{d}/{ep}_s*.mp4")):
    sid = os.path.basename(nf)[len(ep) + 1:-4]
    st = json.load(open(nf[:-4] + ".json")); bf = f"{ROOT}/{st['baseline_video']}"
    row = {}
    for k, f in (("adl_int8", bf), (os.path.basename(d), nf)):
        p = probe(f); row[k] = {**p, **sharp(f, p["w"], p["h"])}
    res[sid] = row; print(sid, json.dumps(row, ensure_ascii=False))
json.dump(res, open(f"{d}/metrics.json", "w"), ensure_ascii=False, indent=1)
