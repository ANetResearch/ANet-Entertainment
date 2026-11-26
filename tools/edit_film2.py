#!/usr/bin/env python3
"""Second-pass edit of the short film (ep13).
- take per shot: film/cut.json override {"s36": {"take": "c", "ss": 0.5, "t": 7}} else best QC take
- any cut the model put inside a clip is detected and trimmed away
- shots run from their first frame (action starts there); non-dialogue shots capped, narrated shots long enough for the line
- audio: per-clip gain (no pumping), soft fades at every cut, a very low room-tone bed across the film
- optional narration from film/vo/<shot>.wav
usage: edit_film2.py OUT.mp4 [--vo] [--title card.png] [--end card.png]"""
import json, os, re, subprocess, sys, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from package import pick, FF
from concurrent.futures import ThreadPoolExecutor
EP = "ep13"
CAP = {"macro": 7.0, "establishing": 7.5, "verite": 8.5}
VENC = ["-c:v", "libx264", "-crf", os.environ.get("CRF", "18"), "-preset", os.environ.get("PRESET", "medium"), "-pix_fmt", "yuv420p",
        "-r", "24", "-video_track_timescale", "12288"]
AENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]


def run(args):
    return subprocess.run([FF, "-hide_banner"] + args, capture_output=True, text=True).stderr


def dur_of(p):
    h, m, s = run(["-i", p]).split("Duration: ")[1].split(",")[0].split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def scene_cuts(p):
    out = run(["-i", p, "-vf", "select='gt(scene,0.5)',showinfo", "-an", "-f", "null", "-"])
    return [float(x) for x in re.findall(r"pts_time:([\d.]+)", out)]


def mean_db(p, ss, t):
    out = run(["-ss", f"{ss}", "-t", f"{t}", "-i", p, "-vn", "-af", "volumedetect", "-f", "null", "-"])
    m = re.search(r"mean_volume: (-?[\d.]+)", out)
    return float(m.group(1)) if m else -60.0


def plan(shot, cut):
    o = cut.get(shot["id"], {})
    src = f"{ROOT}/episodes/{EP}/video/{shot['id']}_{o['take']}.mp4" if o.get("take") else pick(EP, shot["id"])
    d = dur_of(src)
    ss, end = 0.12, d - 0.15
    for c in scene_cuts(src):            # the model sometimes cuts to another angle inside a clip
        if c >= 0.45 * d: end = min(end, c - 0.12)
        else: ss = max(ss, c + 0.12)
    talk = bool(shot.get("dialogue"))
    vo = f"{ROOT}/film/vo/{shot['id']}.wav"
    need = dur_of(vo) + 1.3 if os.path.exists(vo) else 0
    if not talk and not o.get("full"):
        end = min(end, ss + max(CAP.get(shot["type"], 8.0), need))
    if "ss" in o: ss = o["ss"]
    if "t" in o: end = ss + o["t"]
    return {"id": shot["id"], "src": src, "ss": round(ss, 2), "t": round(end - ss, 2), "talk": talk, "type": shot["type"]}


def seg(job):
    p, out, fin, fout = job
    gain = max(-12.0, min(14.0, (-21.0 if p["talk"] else -31.0) - mean_db(p["src"], p["ss"], p["t"])))
    t = p["t"]
    vf = ["scale=1344:768,setsar=1,fps=24"]
    if p["type"] == "interview":
        vf.append("eq=saturation=0.86:contrast=1.03")
    af = [f"volume={gain:.1f}dB", "alimiter=limit=0.8", "afade=t=in:d=0.12", f"afade=t=out:st={t - 0.15:.2f}:d=0.15"]
    if fin:
        vf.append("fade=t=in:d=0.7"); af.append("afade=t=in:d=0.7")
    if fout:
        vf.append(f"fade=t=out:st={t - 0.9:.2f}:d=0.9"); af.append(f"afade=t=out:st={t - 0.9:.2f}:d=0.9")
    subprocess.run([FF, "-y", "-loglevel", "error", "-ss", f"{p['ss']}", "-t", f"{t}", "-i", p["src"],
                    "-vf", ",".join(vf), "-af", ",".join(af)] + VENC + AENC + [out], check=True)
    return dur_of(out)


def card(out, secs, png=None):
    src = ["-loop", "1", "-t", str(secs), "-i", png] if png else ["-f", "lavfi", "-t", str(secs), "-i", "color=c=black:s=1344x768:r=24"]
    vf = "scale=1344:768,setsar=1,fps=24" + (f",fade=t=in:d=0.8,fade=t=out:st={secs - 0.8}:d=0.8" if png else "")
    subprocess.run([FF, "-y", "-loglevel", "error"] + src + ["-f", "lavfi", "-t", str(secs), "-i", "anullsrc=r=48000:cl=stereo",
                    "-vf", vf, "-shortest"] + VENC + AENC + [out], check=True)
    return dur_of(out)


def main():
    out = sys.argv[1]
    opt = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    use_vo = "--vo" in sys.argv
    shots = json.load(open(f"{ROOT}/series/{EP}.json"))["shots"]
    cf = f"{ROOT}/film/cut.json"
    cut = json.load(open(cf)) if os.path.exists(cf) else {}
    tmp = tempfile.mkdtemp(prefix="edit_", dir=os.path.dirname(os.path.abspath(out)))
    with ThreadPoolExecutor(4) as ex:
        plans = list(ex.map(lambda s: plan(s, cut), shots))
    jobs, order = [], []      # order: (path, shot id or None)
    if opt("--title"):
        order.append((f"{tmp}/title.mp4", "title"))
    for i, (s, p) in enumerate(zip(shots, plans)):
        first = i == 0 or s.get("act") != shots[i - 1].get("act")
        last = i == len(shots) - 1 or s.get("act") != shots[i + 1].get("act")
        if first and i:
            order.append((f"{tmp}/black.mp4", "black"))
        jobs.append((p, f"{tmp}/{s['id']}.mp4", first, last)); order.append((f"{tmp}/{s['id']}.mp4", s["id"]))
    if opt("--end"):
        order.append((f"{tmp}/end.mp4", "end"))
    lens = {"title": card(f"{tmp}/title.mp4", 4, opt("--title")) if opt("--title") else 0, "black": card(f"{tmp}/black.mp4", 0.7),
            "end": card(f"{tmp}/end.mp4", 5, opt("--end")) if opt("--end") else 0}
    with ThreadPoolExecutor(4) as ex:
        for (p, o, _, _), L in zip(jobs, ex.map(seg, jobs)):
            lens[p["id"]] = L
    open(f"{tmp}/list.txt", "w").write("".join(f"file '{p}'\n" for p, _ in order))
    raw = f"{tmp}/raw.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy", raw], check=True)
    # final audio: scene sound + room-tone bed (+ narration)
    total = dur_of(raw)
    ins = ["-i", raw, "-f", "lavfi", "-t", f"{total}", "-i", "anoisesrc=c=brown:r=48000:a=0.5"]
    fc = [f"[1:a]lowpass=f=180,volume=-34dB,afade=t=in:d=3,afade=t=out:st={total - 6:.1f}:d=5,aformat=channel_layouts=stereo[bed]"]
    mix, tpos, marks = ["[0:a]", "[bed]"], 0.0, []
    for path, key in order:
        vo = f"{ROOT}/film/vo/{key}.wav"
        if use_vo and os.path.exists(vo):
            n = len(ins) // 2 if False else None
            ins += ["-i", vo]
            idx = sum(1 for x in ins if x == "-i") - 1
            ms = int((tpos + 0.7) * 1000)
            fc.append(f"[{idx}:a]aresample=48000,loudnorm=I=-17:TP=-2:LRA=7,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{idx}]")
            mix.append(f"[v{idx}]"); marks.append((key, round(tpos + 0.7, 2)))
        tpos += lens[key]
    fc.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,alimiter=limit=0.9[a]")
    subprocess.run([FF, "-y", "-loglevel", "error"] + ins + ["-filter_complex", ";".join(fc), "-map", "0:v", "-map", "[a]", "-c:v", "copy"]
                   + AENC + ["-movflags", "+faststart", out], check=True)
    json.dump({"shots": plans, "narration_at": marks}, open(out[:-4] + ".edl.json", "w"), ensure_ascii=False, indent=1)
    shutil.rmtree(tmp)
    print(len(jobs), "shots", f"{dur_of(out):.0f}s", f"{os.path.getsize(out) / 1e6:.0f}MB", "narration lines:", len(marks), flush=True)


if __name__ == "__main__":
    main()
