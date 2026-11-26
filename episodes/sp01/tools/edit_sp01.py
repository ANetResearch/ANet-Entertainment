#!/usr/bin/env python3
"""Rough cut of sp01 《第一页》: no music, no subtitles. Per-era grade, trimmed takes, transitions (hard cut, dissolve,
white flash, dip to black), sound bridges (J/L cuts, the child's question under the flash montage), loudness
levelling and an end card with the two logos only.

usage: edit_sp01.py OUT.mp4 [--picks work/picks.json] [--repo OUT_repo.mp4]
The take of every shot is the best QC take (director takes c/d first) unless work/picks.json names one.
"""
import json, os, re, subprocess, sys, glob, shutil, tempfile
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EP = os.path.join(ROOT, "episodes", "sp01")
W, H, FPS = 1344, 768, 24
VENC = ["-c:v", "libx264", "-crf", "18", "-preset", "fast", "-pix_fmt", "yuv420p", "-r", str(FPS)]
VENC_SEG = ["-c:v", "libx264", "-crf", "15", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-r", str(FPS)]
AENC = ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]
# intermediate segments carry PCM sound (no AAC priming, which would shift the sound by ~21 ms per segment)
AENC_SEG = ["-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2"]
GRADE = {
    "home48": "eq=saturation=0.86:gamma=1.02,colorbalance=rs=0.03:gs=0.01:bs=-0.04,gblur=sigma=0.45,noise=alls=4:allf=t,vignette=PI/5",
    "lab50s": "eq=saturation=0.8:contrast=1.04,noise=alls=6:allf=t",
    "arch58": "eq=saturation=0.72:contrast=1.07,rgbashift=rh=2:bh=-2,gblur=sigma=0.5,noise=alls=8:allf=t",
    "v75": "eq=contrast=1.05:saturation=0.93,noise=alls=4:allf=t",
    "int78": "eq=saturation=0.9",
}

# ------------------------------------------------------------------ the cut
# Every entry is one segment. mode "io": explicit in/out points (a, b) in seconds of the chosen take, set by hand from the
# phrase timings (work/speech_times.json) and the clip's speech-band energy; mode "tail": the last `len` seconds;
# mode "dlg": automatic in/out around the detected speech (fallback). t = transition into the next segment:
# ("cut",) ("dissolve", d) ("white", d) ("black", d). j = J-cut: the segment's sound starts j seconds before its picture.
# afx = extra audio filter (e.g. a television or a crowd muffled behind a wall); gain in dB; mute = picture only.
EDL = [
    # 序 · 一个问题
    dict(shot="s01", mode="io", a=0.3, b=7.98, t=("white", 0.16)),
    dict(shot="s31", mode="io", a=0.85, b=3.95, t=("black", 0.7), tag="hook_moss"),
    dict(shot="s02", mode="io", a=0.0, b=10.1, t=("cut",)),
    dict(shot="s03", mode="tail", len=6.5, t=("dissolve", 0.5)),
    # 第一幕 · 种子
    dict(shot="s04", mode="io", a=0.0, b=6.3, t=("cut",)),
    dict(shot="s05", mode="io", a=0.0, b=6.0, t=("dissolve", 0.6)),
    dict(shot="s06", mode="tail", len=7.6, t=("cut",)),
    dict(shot="s07", mode="io", a=2.0, b=10.1, t=("cut",), j=0.5),
    dict(shot="s08", mode="tail", len=5.8, t=("cut",)),
    dict(shot="s09", mode="io", a=1.0, b=8.2, t=("cut",)),
    dict(shot="s10", mode="tail", len=6.2, t=("cut",)),
    dict(shot="s11", mode="io", a=0.5, b=9.4, t=("white", 0.12)),
    dict(shot="s12", mode="io", a=0.6, b=6.7, t=("cut",)),
    dict(shot="s13", mode="io", a=0.0, b=6.6, t=("cut",)),
    dict(shot="s14", mode="io", a=1.6, b=7.98, t=("cut",)),
    dict(shot="s15", mode="io", a=0.0, b=6.8, t=("cut",)),
    dict(shot="s16", mode="tail", len=5.6, t=("black", 0.8)),
    # 第二幕 · 钥匙
    dict(shot="s17", mode="tail", len=5.8, t=("cut",)),
    dict(shot="s18", mode="tail", len=5.6, t=("cut",), gain=-3),
    dict(shot="s19", mode="io", a=1.2, b=10.2, t=("cut",)),
    dict(shot="s20", mode="tail", len=5.6, t=("cut",), gain=-6, afx="lowpass=f=700,lowpass=f=700"),
    dict(shot="s21", mode="io", a=0.1, b=4.6, t=("white", 0.14)),
    dict(shot="s22", mode="io", a=0.3, b=6.2, t=("cut",)),
    dict(shot="s23", mode="tail", len=6.6, t=("black", 1.0)),
    dict(shot="s24", mode="io", a=0.0, b=9.4, t=("dissolve", 0.5)),
    dict(shot="s25", mode="io", a=0.8, b=9.3, t=("cut",)),
    dict(shot="s26", mode="tail", len=5.0, t=("cut",)),
    dict(shot="s27", mode="io", a=0.0, b=10.1, t=("cut",)),
    # 第三幕 · 应验
    dict(shot="s28", mode="io", a=0.0, b=7.8, t=("black", 0.6)),
    dict(shot="s29", mode="tail", len=6.3, t=("cut",)),
    dict(shot="s30", mode="tail", len=6.0, t=("cut",), gain=-4, afx="lowpass=f=550,lowpass=f=550"),
    dict(shot="s31", mode="io", a=0.6, b=8.6, t=("cut",)),
    dict(shot="s32", mode="tail", len=6.8, t=("cut",)),
    dict(shot="s33", mode="io", a=2.9, b=9.3, t=("white", 0.12)),
    # flash montage: the three questions, picture only; the child's question runs underneath (BRIDGES)
    dict(shot="s01", mode="io", a=2.4, b=3.4, t=("white", 0.12), mute=True, tag="m1"),
    dict(shot="s13", mode="io", a=1.9, b=2.9, t=("white", 0.12), mute=True, tag="m2"),
    dict(shot="s05", mode="io", a=1.0, b=1.9, t=("white", 0.12), mute=True, tag="m3"),
    dict(shot="s31", mode="io", a=2.0, b=3.0, t=("black", 0.5), mute=True, tag="m4"),
    dict(shot="s34", mode="tail", len=7.0, t=("cut",)),
    dict(shot="s35", mode="io", a=0.0, b=6.8, t=("cut",)),
    dict(shot="s36", mode="io", a=1.2, b=9.4, t=("cut",)),
    dict(shot="s37", mode="io", a=0.0, b=2.3, t=("dissolve", 0.25)),          # interview jump cut over a long pause
    dict(shot="s37", mode="io", a=5.6, b=9.4, t=("cut",)),
    dict(shot="s38", mode="tail", len=6.3, t=("cut",)),
    dict(shot="s39", mode="tail", len=9.5, t=("dissolve", 0.8)),
    # 尾声 · 属于所有人
    dict(shot="s40", mode="io", a=2.9, b=11.5, t=("cut",)),
    dict(shot="s41", mode="io", a=1.2, b=7.98, t=("dissolve", 0.8)),
    dict(shot="s42", mode="io", a=0.6, b=9.4, t=("white", 1.2)),
    dict(card="end", len=5.0, t=("cut",)),
]
# sound bridges: (shot, source in-point, length, placed under the segment with this tag, offset in it, gain dB)
BRIDGES = [
    ("s01", 0.5, 7.4, "m1", 0.0, -1.0),        # the child's question under the flash montage, running on into s34
]

def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def probe(p, stream=False):
    """duration of the file, or (stream=True) of its picture, counted in frames (Matroska has no stream duration)"""
    if stream:
        out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets", "-show_entries",
                              "stream=nb_read_packets", "-of", "csv=p=0", p], capture_output=True, text=True).stdout
        return int(out.strip().split("\n")[0]) / FPS
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                         capture_output=True, text=True).stdout
    return float(out.strip().split("\n")[0])


def speech_bounds(p, dur):
    """first and last instants of speech: speech-band (300-3400 Hz) energy against a threshold set between the
    clip's own noise floor and its peak, so that quiet and loud clips are treated alike."""
    import numpy as np
    sr, n = 16000, 512
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", p, "-vn", "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, dtype=np.float32)
    if len(x) < n * 4:
        return 0.0, dur
    fr = x[: len(x) // n * n].reshape(-1, n) * np.hanning(n)
    spec = np.abs(np.fft.rfft(fr, axis=1)) ** 2
    f = np.fft.rfftfreq(n, 1 / sr)
    e = 10 * np.log10(spec[:, (f > 300) & (f < 3400)].sum(axis=1) + 1e-12)
    floor, peak = np.percentile(e, 20), np.percentile(e, 98)
    thr = max(floor + 8, floor + 0.45 * (peak - floor))
    act = e > thr
    k = max(1, int(0.12 * sr / n))                     # ignore blips shorter than 0.12 s
    runs, t = [], 0
    while t < len(act):
        if act[t]:
            u = t
            while u < len(act) and act[u]:
                u += 1
            if u - t >= k:
                runs.append((t, u))
            t = u
        else:
            t += 1
    if not runs:
        return 0.0, dur
    hop = n / sr
    return runs[0][0] * hop, min(dur, runs[-1][1] * hop)


def load_script():
    return {s["id"]: s for s in json.load(open(os.path.join(ROOT, "series", "sp01.json")))["shots"]}


def pick(sid, picks):
    if sid in picks:
        return os.path.join(EP, "video", f"{sid}_{picks[sid]}.mp4")
    qc = json.load(open(os.path.join(EP, "qc.json"))) if os.path.exists(os.path.join(EP, "qc.json")) else {}
    takes = sorted(glob.glob(os.path.join(EP, "video", f"{sid}_*.mp4")))

    def score(p):
        k = os.path.basename(p)[:-4]
        fl = qc.get(k, {}).get("flags", [])
        bad = [f for f in fl if f != "music?"]
        tk = k.split("_")[1]
        pref = 0 if tk in ("c", "d", "e", "f", "g") else 1
        return (len(bad), "music?" in fl, pref, -qc.get(k, {}).get("ratio", 0), k)
    return min(takes, key=score) if takes else None


def end_card(png):
    im = Image.new("RGB", (W, H), (0, 0, 0))
    sm = Image.open(os.path.join(ROOT, "assets", "logos", "anet-smiley.png")).convert("RGBA")
    sm = sm.resize((170, 170), Image.LANCZOS)
    wd = Image.open(os.path.join(ROOT, "assets", "logos", "agent-network-logo.png")).convert("RGBA")
    ww = 560
    wd = wd.resize((ww, int(wd.height * ww / wd.width)), Image.LANCZOS)
    gap = 44
    top = (H - (sm.height + gap + wd.height)) // 2
    im.paste(sm, ((W - sm.width) // 2, top), sm)
    im.paste(wd, ((W - wd.width) // 2, top + sm.height + gap), wd)
    im.save(png)


def render(job):
    i, e, src, ss, length, out, era, talk = job
    if os.environ.get("EDIT_TMP") and os.path.exists(out) and (not e.get("j") or os.path.exists(out[:-4] + "_pre.wav")):
        try:
            if round(probe(out, stream=True) * FPS) == round(length * FPS):
                return i, probe(out, stream=True)          # reuse a segment rendered by an interrupted run
        except Exception:
            pass
    # exact frame count by filter (an output frame limit would stop before loudnorm's look-ahead is flushed)
    vf = [f"scale={W}:{H}:flags=lanczos,setsar=1,fps={FPS}", GRADE[era],
          "tpad=stop_mode=clone:stop_duration=0.2", f"trim=end_frame={round(length * FPS)},setpts=PTS-STARTPTS"]
    gain = e.get("gain", 0)
    level = [f"loudnorm=I={-19 if talk else -26}:TP=-2:LRA=11", e.get("afx", "anull"),
             f"volume={gain}dB" if gain else "anull", "aresample=48000"]
    fades = ["afade=t=in:d=0.03", f"afade=t=out:st={max(0, length - 0.04):.3f}:d=0.04"]
    jl = min(e.get("j", 0), ss)
    # sound: timestamps restarted (the AAC source starts a few ms late after a seek), padded and cut to the exact sample
    n_a = round(length * 48000)
    tail = ["apad", f"atrim=end_sample={n_a}"]
    inp = ["-ss", f"{ss:.3f}", "-t", f"{length + 0.6:.3f}", "-i", src]
    if e.get("mute"):
        ff(*inp, "-vf", ",".join(vf), "-af", ",".join(["asetpts=PTS-STARTPTS", "volume=0", "aresample=48000"] + tail),
           *VENC_SEG, *AENC_SEG, out)
    elif jl:
        # J-cut: level the sound from (ss - j) on, keep the first j seconds as the pre-lap, the rest as the segment's sound
        wav = out[:-4] + "_pre.wav"
        ff("-ss", f"{ss - jl:.3f}", "-t", f"{length + jl + 0.6:.3f}", "-i", src, "-vn", "-af",
           ",".join(["asetpts=PTS-STARTPTS"] + level + ["apad", f"atrim=end_sample={round((length + jl) * 48000)}"]),
           "-ac", "2", "-c:a", "pcm_s16le", wav)
        ff(*inp, "-ss", f"{jl:.3f}", "-i", wav, "-map", "0:v", "-map", "1:a", "-vf", ",".join(vf),
           "-af", ",".join(["asetpts=PTS-STARTPTS"] + fades + tail), *VENC_SEG, *AENC_SEG, out)
    else:
        ff(*inp, "-vf", ",".join(vf), "-af", ",".join(["asetpts=PTS-STARTPTS"] + level + fades + tail),
           *VENC_SEG, *AENC_SEG, out)
    return i, probe(out, stream=True)


def main():
    out = sys.argv[1]
    opt = lambda k: sys.argv[sys.argv.index(k) + 1] if k in sys.argv else None
    picks = json.load(open(opt("--picks"))) if opt("--picks") else {}
    script = load_script()
    tmp = os.environ.get("EDIT_TMP") or tempfile.mkdtemp(prefix="cut_", dir=os.path.dirname(os.path.abspath(out)))
    jobs, segs, used = [], [], {}
    speech = {}
    for i, e in enumerate(EDL):
        if "card" in e:
            png = os.path.join(tmp, "end.png")
            end_card(png)
            o = os.path.join(tmp, f"{i:02d}_end.mkv")
            ff("-loop", "1", "-t", str(e["len"]), "-i", png, "-f", "lavfi", "-t", str(e["len"]), "-i",
               "anullsrc=r=48000:cl=stereo", "-vf", f"scale={W}:{H},setsar=1,fps={FPS},format=yuv420p,fade=t=in:d=1.0,fade=t=out:st={e['len']-1.2}:d=1.2",
               *VENC_SEG, *AENC_SEG, "-shortest", o)
            segs.append(dict(e, file=o, length=probe(o, stream=True), edl=i))
            continue
        sid = e["shot"]
        src = pick(sid, picks)
        if not src:
            print("MISSING", sid)
            continue
        used.setdefault(sid, os.path.basename(src))
        dur = probe(src)
        s0, s1 = speech_bounds(src, dur)
        speech[sid] = (src, s0, s1)
        sh = script[sid]
        if e["mode"] == "io":
            ss, end = e["a"], min(dur - 0.02, e["b"])
        elif e["mode"] == "dlg":
            ss = max(0.0, s0 - e.get("pre", 0.5))
            end = min(dur - 0.05, s1 + e.get("hold", 1.0))
        elif e["mode"] == "tail":
            end = dur - 0.15
            ss = max(0.0, end - e["len"])
        else:                                     # seg: a fixed excerpt; a=None -> around the speech start
            a = e.get("a")
            ss = max(0.0, (s0 - 0.15) if a is None else a)
            end = min(dur - 0.05, ss + e["len"])
        length = int((end - ss) * FPS + 1e-6) / FPS     # whole frames, so that picture and sound stay the same length
        o = os.path.join(tmp, f"{i:02d}_{sid}.mkv")
        jobs.append((i, e, src, ss, length, o, sh["era"], bool(sh["dialogue"]) and not e.get("mute")))
        segs.append(dict(e, file=o, src=src, ss=ss, edl=i))
    with ThreadPoolExecutor(6) as ex:
        lens = dict(ex.map(render, jobs))
    for s in segs:
        if "card" not in s:
            s["length"] = lens[s["edl"]]
    # transitions: xfade chain with cumulative offsets
    n = len(segs)
    args = []
    for s in segs:
        args += ["-i", s["file"]]
    fc, vlab, alab, t = [], "[0:v]", "[0:a]", segs[0]["length"]
    starts = [0.0]
    for k in range(1, n):
        kind = segs[k - 1]["t"]
        d = {"cut": 1.0 / FPS}.get(kind[0], kind[1] if len(kind) > 1 else 0.5)
        tr = {"cut": "fade", "dissolve": "dissolve", "white": "fadewhite", "black": "fadeblack"}[kind[0]]
        off = t - d
        starts.append(off)
        fc.append(f"{vlab}[{k}:v]xfade=transition={tr}:duration={d:.4f}:offset={off:.4f}[v{k}]")
        fc.append(f"{alab}[{k}:a]acrossfade=d={d:.4f}:c1=tri:c2=tri[a{k}]")
        vlab, alab = f"[v{k}]", f"[a{k}]"
        t = off + segs[k]["length"]
    # sound bridges and J-cuts (pre-laps): extra sound placed at absolute times and mixed in
    lays = []
    for sid, b_in, b_len, under, at, gdb in BRIDGES:
        k = next(j for j, s in enumerate(segs) if s.get("tag") == under)
        lays.append((pick(sid, picks), b_in, b_len, starts[k] + at, gdb, True))
    for k, s in enumerate(segs):
        if s.get("j") and k:
            jl = min(s["j"], s["ss"])
            lays.append((s["file"][:-4] + "_pre.wav", 0.0, jl, starts[k] - jl, 0.0, False))
    extra = []
    for src, b_in, b_len, place, gdb, norm in lays:
        args += ["-ss", f"{b_in:.3f}", "-t", f"{b_len:.3f}", "-i", src]
        idx = n + len(extra)
        lv = "loudnorm=I=-21:TP=-2," if norm else ""
        fo = 0.25 if norm else 0.02
        fc.append(f"[{idx}:a]aresample=48000,{lv}volume={gdb}dB,aresample=48000,afade=t=in:d=0.08,"
                  f"afade=t=out:st={max(0.0, b_len - fo):.3f}:d={fo},adelay={int(place * 1000)}|{int(place * 1000)}[b{idx}]")
        extra.append(f"[b{idx}]")
    if extra:
        fc.append(f"{alab}{''.join(extra)}amix=inputs={1 + len(extra)}:normalize=0:duration=first[afinal]")
        alab = "[afinal]"
    fc.append(f"{alab}loudnorm=I=-20:TP=-1.5:LRA=13[aout]")
    graph = ";".join(fc)
    gfile = os.path.join(tmp, "graph.txt")
    open(gfile, "w").write(graph)
    ff(*args, "-filter_complex_script", gfile, "-map", vlab, "-map", "[aout]", *VENC, *AENC, "-movflags", "+faststart", out)
    total = probe(out)
    a_out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=duration", "-of",
                            "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    print(f"picture {probe(out, stream=True):.3f}s, sound {a_out}s")
    json.dump({"takes": used, "segments": [{k: v for k, v in s.items() if k in ("shot", "ss", "length", "t", "tag", "card")}
                                           | {"start": round(st, 3)} for s, st in zip(segs, starts)], "duration": total},
              open(out[:-4] + ".edl.json", "w"), ensure_ascii=False, indent=1)
    if opt("--repo"):
        # two-pass to a size target well under the 95 MB per-file limit of the repository
        kbps = int(88 * 2**20 * 8 / total / 1000 * 0.98) - 128
        log = os.path.join(tmp, "x264pass")
        ff("-i", out, "-c:v", "libx264", "-b:v", f"{kbps}k", "-preset", "slow", "-pix_fmt", "yuv420p", "-pass", "1",
           "-passlogfile", log, "-an", "-f", "null", "/dev/null")
        ff("-i", out, "-c:v", "libx264", "-b:v", f"{kbps}k", "-preset", "slow", "-pix_fmt", "yuv420p", "-pass", "2",
           "-passlogfile", log, "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", opt("--repo"))
        print(f"{opt('--repo')}: {os.path.getsize(opt('--repo')) / 2**20:.1f} MiB at {kbps} kb/s video")
    shutil.rmtree(tmp)
    print(f"{out}: {total:.1f}s, {os.path.getsize(out) / 2**20:.0f} MiB, {len(used)} shots")


if __name__ == "__main__":
    main()
