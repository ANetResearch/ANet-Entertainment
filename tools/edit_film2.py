#!/usr/bin/env python3
"""Second-pass editor (short film and series episodes; EP env picks the episode, default ep13).
- take per shot: film/cut_<EP>.json override {"s36": {"take": "c", "ss": 0.5, "t": 7, "full": true}} else best QC take
- any cut the model put inside a clip is detected and trimmed away
- shots run from their first frame; non-dialogue shots capped, narrated shots long enough for the line
- audio: per-clip gain (no pumping), soft fades at every cut, a very low room-tone bed
- --vo     narration from film/vo/ep13_<shot>.wav
- --music  score from film/cues.json + music/loops/<cue>.wav (looped, ducked under speech)
- --scope  2.39:1 letterbox
- always writes OUT.srt (narration + dialogue + act titles) and OUT.edl.json; --subs also muxes the SRT as a soft subtitle track
usage: edit_film2.py OUT.mp4 [--vo] [--music] [--scope] [--subs] [--title card.png] [--end card.png]"""
import json, os, re, subprocess, sys, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from package import pick, FF
from concurrent.futures import ThreadPoolExecutor
EP = os.environ.get("EP", "ep13")
FILM = EP in ("ep13", "ep14")
CAP = {"macro": 7.0, "establishing": 7.5, "verite": 8.5}
VENC = ["-c:v", "libx264", "-crf", os.environ.get("CRF", "18"), "-preset", os.environ.get("PRESET", "medium"), "-pix_fmt", "yuv420p",
        "-r", "24", "-video_track_timescale", "12288"]
AENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
SCOPE = "--scope" in sys.argv
BLACK = 1.8 if FILM else 0.7


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


def vo_file(sid):
    p = f"{ROOT}/film/vo/ep13_{sid}.wav"
    return p if FILM and os.path.exists(p) else None


def plan(shot, cut):
    o = cut.get(shot["id"], {})
    src = f"{ROOT}/episodes/{EP}/video/{shot['id']}_{o['take']}.mp4" if o.get("take") else pick(EP, shot["id"])
    d = dur_of(src)
    ss, end = 0.12, d - 0.15
    for c in scene_cuts(src):            # the model sometimes cuts to another angle inside a clip
        if c >= 0.45 * d: end = min(end, c - 0.12)
        else: ss = max(ss, c + 0.12)
    talk = bool(shot.get("dialogue"))
    vo = vo_file(shot["id"]) if "--vo" in sys.argv else None
    need = dur_of(vo) + 1.5 if vo else 0
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
    if SCOPE: vf.append("crop=1344:562,pad=1344:768:0:103:black")
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


def ts(x):
    ms = int(round(x * 1000)); return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main():
    out = [a for a in sys.argv[1:] if a.endswith(".mp4")][0]
    opt = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    use_vo, use_music = "--vo" in sys.argv, "--music" in sys.argv
    shots = json.load(open(f"{ROOT}/series/{EP}.json"))["shots"]
    cf = f"{ROOT}/film/cut_{EP}.json"
    cut = json.load(open(cf)) if os.path.exists(cf) else {}
    tmp = tempfile.mkdtemp(prefix="edit_", dir=os.path.dirname(os.path.abspath(out)))
    with ThreadPoolExecutor(4) as ex:
        plans = list(ex.map(lambda s: plan(s, cut), shots))
    jobs, order = [], []
    if opt("--title"):
        order.append((f"{tmp}/title.mp4", "title"))
    for i, (s, p) in enumerate(zip(shots, plans)):
        first = i == 0 or s.get("act") != shots[i - 1].get("act")
        last = i == len(shots) - 1 or s.get("act") != shots[i + 1].get("act")
        if first and i:
            order.append((f"{tmp}/black.mp4", "black:" + s["id"]))
        jobs.append((p, f"{tmp}/{s['id']}.mp4", first, last)); order.append((f"{tmp}/{s['id']}.mp4", s["id"]))
    if opt("--end"):
        order.append((f"{tmp}/end.mp4", "end"))
    lens = {"title": card(f"{tmp}/title.mp4", 4, opt("--title")) if opt("--title") else 0, "black": card(f"{tmp}/black.mp4", BLACK),
            "end": card(f"{tmp}/end.mp4", 6, opt("--end")) if opt("--end") else 0}
    with ThreadPoolExecutor(4) as ex:
        for (p, o, _, _), L in zip(jobs, ex.map(seg, jobs)):
            lens[p["id"]] = L
    open(f"{tmp}/list.txt", "w").write("".join(f"file '{p}'\n" for p, _ in order))
    raw = f"{tmp}/raw.mp4"
    subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{tmp}/list.txt", "-c", "copy", raw], check=True)
    total = dur_of(raw)
    # timeline
    start, tpos = {}, 0.0
    for _, key in order:
        start[key] = tpos; tpos += lens[key.split(":")[0]]
    by = {s["id"]: s for s in shots}
    # subtitles
    subs = []
    for _, key in order:
        if key.startswith("black:") and by[key[6:]].get("act"):
            subs.append((start[key] + 0.15, start[key] + BLACK - 0.15, "— " + by[key[6:]]["act"] + " —"))
        if key not in by: continue
        s, t0, L = by[key], start[key], lens[key]
        vo = vo_file(key) if use_vo else None
        if vo:
            subs.append((t0 + 0.7, min(t0 + 0.7 + dur_of(vo) + 0.3, t0 + L - 0.05), s["vo"]))
        dl = s.get("dialogue") or []
        if dl:
            n = sum(len(d["line"]) for d in dl); a = t0 + 0.5; span = L - 1.0
            for d in dl:
                b = a + span * len(d["line"]) / n
                subs.append((a, b - 0.08, d["line"])); a = b
    subs.sort()
    srt = out[:-4] + ".srt"
    open(srt, "w").write("".join(f"{i}\n{ts(a)} --> {ts(b)}\n{txt}\n\n" for i, (a, b, txt) in enumerate(subs, 1)))
    # audio mix: scene sound + room tone (+ narration) (+ music ducked under speech)
    ins = ["-i", raw, "-f", "lavfi", "-t", f"{total}", "-i", "anoisesrc=c=brown:r=48000:a=0.5"]
    nin = 2
    fc = [f"[1:a]lowpass=f=180,volume=-36dB,afade=t=in:d=3,afade=t=out:st={total - 6:.1f}:d=5,aformat=channel_layouts=stereo[bed]"]
    speech, marks = ["[0:a]"], []
    if use_vo:
        for _, key in order:
            vo = vo_file(key)
            if not vo: continue
            ins += ["-i", vo]; ms = int((start[key] + 0.7) * 1000)
            fc.append(f"[{nin}:a]aresample=48000,highpass=f=70,loudnorm=I=-16:TP=-2:LRA=7,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{nin}]")
            speech.append(f"[v{nin}]"); marks.append((key, round(start[key] + 0.7, 2))); nin += 1
    fc.append("".join(speech) + f"amix=inputs={len(speech)}:normalize=0:duration=first[sp]")
    cues = json.load(open(f"{ROOT}/film/cues.json")) if use_music and FILM else []
    mus = []
    for c in cues:
        a = (start[c["from"]] if c["from"] in start else 0) + c.get("offset", 0)
        b = (start[c["to"]] + lens[c["to"]] if c["to"] in start else total) + c.get("tail", 0)
        b = min(b, total); L = b - a
        ins += ["-stream_loop", "-1", "-i", f"{ROOT}/music/loops/{c['cue']}.wav"]; ms = int(a * 1000)
        fi, fo = c.get("fade_in", 2.0), c.get("fade_out", 3.0)
        fc.append(f"[{nin}:a]atrim=0:{L:.2f},asetpts=PTS-STARTPTS,volume={c.get('gain', -16)}dB,afade=t=in:d={fi},afade=t=out:st={max(0, L - fo):.2f}:d={fo},"
                  f"aformat=channel_layouts=stereo,adelay={ms}|{ms}[m{nin}]")
        mus.append(f"[m{nin}]"); nin += 1
    if mus:
        fc.append("".join(mus) + f"amix=inputs={len(mus)}:normalize=0:duration=longest,apad=whole_dur={total:.2f}[mraw]")
        fc.append("[sp]asplit=2[sp1][sp2]")
        fc.append("[mraw][sp2]sidechaincompress=threshold=0.035:ratio=5:attack=120:release=900[mduck]")
        fc.append("[sp1][bed][mduck]amix=inputs=3:normalize=0:duration=first,alimiter=limit=0.89[a]")
    else:
        fc.append("[sp][bed]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.89[a]")
    cmd = [FF, "-y", "-loglevel", "error"] + ins
    maps = ["-map", "0:v", "-map", "[a]"]
    if "--subs" in sys.argv:
        cmd += ["-i", srt]; maps += ["-map", f"{nin}:0", "-c:s", "mov_text", "-metadata:s:s:0", "language=chi"]
    subprocess.run(cmd + ["-filter_complex", ";".join(fc)] + maps + ["-c:v", "copy"] + AENC + ["-t", f"{total:.2f}", "-movflags", "+faststart", out], check=True)
    json.dump({"shots": plans, "start": {k: round(v, 2) for k, v in start.items()}, "narration_at": marks, "cues": cues},
              open(out[:-4] + ".edl.json", "w"), ensure_ascii=False, indent=1)
    shutil.rmtree(tmp)
    print(EP, len(jobs), "shots", f"{dur_of(out):.0f}s", f"{os.path.getsize(out) / 1e6:.0f}MB", "narration:", len(marks), "cues:", len(cues), "subs:", len(subs), flush=True)


if __name__ == "__main__":
    main()
