#!/usr/bin/env python3
"""Review sheet: for each listed shot, one row per take with 4 stills (10/40/70/95 %), labelled with QC flags.
usage: review_sheet.py OUT.jpg s01 s02 ...   (all takes of each shot)"""
import json, os, subprocess, sys, glob, tempfile
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EP = os.path.join(ROOT, "episodes", "sp01")
qc = json.load(open(f"{EP}/qc.json")) if os.path.exists(f"{EP}/qc.json") else {}
out, sids = sys.argv[1], sys.argv[2:]
w, h = int(os.environ.get("RW", 300)), int(int(os.environ.get("RW", 300)) * 0.571)
rows = []
tmp = tempfile.mkdtemp()
for sid in sids:
    for p in sorted(glob.glob(f"{EP}/video/{sid}_*.mp4")):
        k = os.path.basename(p)[:-4]
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                 capture_output=True, text=True).stdout)
        ims = []
        for j, f in enumerate((0.1, 0.4, 0.7, 0.95)):
            o = f"{tmp}/{k}_{j}.jpg"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{d*f:.2f}", "-i", p, "-frames:v", "1", "-vf", f"scale={w}:{h}", o])
            ims.append(o)
        q = qc.get(k, {})
        rows.append((f"{k}  {q.get('flags', '')}  r={q.get('ratio', '')}", ims))
sheet = Image.new("RGB", (w * 4 + 8, len(rows) * (h + 18)), (16, 16, 16))
dr = ImageDraw.Draw(sheet)
for r, (label, ims) in enumerate(rows):
    y = r * (h + 18)
    dr.text((4, y + 3), label, fill=(240, 240, 240))
    for j, f in enumerate(ims):
        if os.path.exists(f):
            sheet.paste(Image.open(f), (j * (w + 2), y + 16))
sheet.save(out, quality=82)
