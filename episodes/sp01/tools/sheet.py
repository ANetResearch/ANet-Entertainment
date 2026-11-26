#!/usr/bin/env python3
"""contact sheet: sheet.py out.jpg img1 img2 ... [--cols 4] [--w 480]"""
import sys, os
from PIL import Image, ImageDraw
args = sys.argv[1:]
cols, w = 4, 480
if "--cols" in args: i = args.index("--cols"); cols = int(args[i+1]); del args[i:i+2]
if "--w" in args: i = args.index("--w"); w = int(args[i+1]); del args[i:i+2]
out, files = args[0], args[1:]
h = int(w * 9 / 16) + 4
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (cols * w, rows * (h + 18)), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for n, f in enumerate(files):
    im = Image.open(f).convert("RGB"); im.thumbnail((w - 4, h - 4))
    x, y = (n % cols) * w, (n // cols) * (h + 18)
    sheet.paste(im, (x + 2, y + 18))
    d.text((x + 4, y + 3), os.path.basename(f), fill=(230, 230, 230))
sheet.save(out, quality=85)
