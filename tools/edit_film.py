#!/usr/bin/env python3
"""Edited cut of an episode / the short film: best take per shot, tightened non-dialogue shots,
levelled audio, fades at act breaks, optional title and end cards. No subtitles, no music.
usage: edit_film.py EP OUT.mp4 [--title card.png] [--end card.png]"""
import json, os, subprocess, sys, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from package import pick, FF
from concurrent.futures import ThreadPoolExecutor
CAP = {"macro": 6.0, "establishing": 6.0, "verite": 7.0, "archival": 7.0}
VENC = ["-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", "24", "-video_track_timescale", "12288"]
AENC = ["-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]


def probe(p):
    out = subprocess.run([FF, "-i", p], capture_output=True, text=True).stderr
    h, m, s = out.split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def seg(job):
    src, out, shot, fin, fout = job
    dur = probe(src)
    talk = bool(shot.get("dialogue"))
    if talk:
        ss, length = 0.2, dur - 0.3
    else:
        length = min(dur - 0.5, CAP.get(shot["type"], 7.0))
        ss = dur - 0.15 - length          # keep the pay-off at the end of the shot
    vf = ["scale=1344:768,setsar=1,fps=24"]
    if shot["type"] == "interview":
        vf.append("eq=saturation=0.86:contrast=1.03")   # interviews are 2078, the events 2075
    af = [f"loudnorm=I={-19 if talk else -27}:TP=-2:LRA=11", f"afade=t=in:d=0.04", f"afade=t=out:st={length - 0.06:.2f}:d=0.06"]
    if fin:
        vf.append("fade=t=in:d=0.6"); af.append("afade=t=in:d=0.6")
    if fout:
        vf.append(f"fade=t=out:st={length - 0.7:.2f}:d=0.7"); af.append(f"afade=t=out:st={length - 0.7:.2f}:d=0.7")
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", f"{ss:.2f}", "-t", f"{length:.2f}", "-i", src,
                    "-vf", ",".join(vf), "-af", ",".join(af)] + VENC + AENC + [out], check=True)
    return length


def card(out, secs, png=None):
    src = ["-loop", "1", "-t", str(secs), "-i", png] if png else ["-f", "lavfi", "-t", str(secs), "-i", "color=c=black:s=1344x768:r=24"]
    vf = "scale=1344:768,setsar=1,fps=24" + (f",fade=t=in:d=0.8,fade=t=out:st={secs - 0.8}:d=0.8" if png else "")
    subprocess.run([FF, "-y", "-loglevel", "error"] + src + ["-f", "lavfi", "-t", str(secs), "-i", "anullsrc=r=48000:cl=stereo",
                    "-vf", vf, "-shortest"] + VENC + AENC + [out], check=True)


def main():
    ep, out = int(sys.argv[1]), sys.argv[2]
    opt = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    name = f"ep{ep:02d}"
    shots = json.load(open(f"{ROOT}/series/{name}.json"))["shots"]
    tmp = tempfile.mkdtemp(prefix="edit_", dir=os.path.dirname(os.path.abspath(out)))
    jobs, order, takes = [], [], {}
    if opt("--title"):
        card(f"{tmp}/title.mp4", 4, opt("--title")); order.append(f"{tmp}/title.mp4")
    for i, s in enumerate(shots):
        src = pick(name, s["id"])
        if not src:
            print("missing", s["id"]); continue
        takes[s["id"]] = os.path.basename(src)
        first = i == 0 or s.get("act") != shots[i - 1].get("act")
        last = i == len(shots) - 1 or s.get("act") != shots[i + 1].get("act")
        if first and i and s.get("act"):
            if not os.path.exists(f"{tmp}/black.mp4"): card(f"{tmp}/black.mp4", 0.8)
            order.append(f"{tmp}/black.mp4")
        jobs.append((src, f"{tmp}/{s['id']}.mp4", s, first, last)); order.append(f"{tmp}/{s['id']}.mp4")
    with ThreadPoolExecutor(6) as ex:
        total = sum(ex.map(seg, jobs))
    if opt("--end"):
        card(f"{tmp}/end.mp4", 5, opt("--end")); order.append(f"{tmp}/end.mp4")
    open(f"{tmp}/list.txt", "w").write("".join(f"file '{p}'\n" for p in order))
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy",
                    "-movflags", "+faststart", out], check=True)
    json.dump(takes, open(out[:-4] + ".takes.json", "w"), indent=1)
    shutil.rmtree(tmp)
    print(name, len(jobs), "shots", f"{probe(out):.0f}s", f"{os.path.getsize(out) / 1e6:.0f}MB", flush=True)


if __name__ == "__main__":
    main()
