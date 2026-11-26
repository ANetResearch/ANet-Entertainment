#!/usr/bin/env python3
"""QC of the assembled rough cut: every dialogue segment is cut out of the finished film (by the EDL written next to
it), transcribed and compared with the scripted line; the whole sound track is checked for music in 60-second
windows with the three-model vote. usage: qc_cut_sp01.py CUT.mp4  -> CUT.qc.json"""
import difflib, json, os, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg as _cfg
import qc_sp01 as Q
import music_check as MC

ROOT = _cfg.ROOT


def excerpt(cut, a, d, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{d:.3f}", "-i", cut, "-vn", "-c:a", "aac",
                    "-b:a", "128k", out], check=True)


def main():
    cut = sys.argv[1]
    edl = json.load(open(cut[:-4] + ".edl.json"))
    script = {s["id"]: s for s in json.load(open(f"{ROOT}/series/sp01.json"))["shots"]}
    tmp = tempfile.mkdtemp(prefix="qccut_")
    jobs = []
    for i, s in enumerate(edl["segments"]):
        sid = s.get("shot")
        if not sid or not script[sid]["dialogue"] or s.get("tag", "").startswith("m"):
            continue
        a, d = s["start"], s["length"]
        o = os.path.join(tmp, f"{i:02d}_{sid}.m4a")
        excerpt(cut, a, d, o)
        jobs.append((i, sid, a, d, o))

    def one(j):
        i, sid, a, d, o = j
        got = Q.listen(o) or {}
        want = "".join(x["line"] for x in script[sid]["dialogue"])
        w, g = Q.norm(want), Q.norm(got.get("speech"))
        return {"seg": i, "shot": sid, "start": round(a, 2), "len": round(d, 2), "want": want, "heard": got.get("speech"),
                "ratio": round(difflib.SequenceMatcher(None, w, g).ratio(), 2) if (w or g) else 1.0}
    with ThreadPoolExecutor(4) as ex:
        dl = list(ex.map(one, jobs))
    total = edl["duration"]
    win = []
    t = 0.0
    while t < total - 1:
        o = os.path.join(tmp, f"win_{int(t):03d}.m4a")
        excerpt(cut, t, min(60.0, total - t), o)
        win.append((t, o))
        t += 60.0
    with ThreadPoolExecutor(3) as ex:
        mv = list(ex.map(lambda w: {"from": w[0], **MC.check(w[1])}, win))
    res = {"duration": total, "dialogue": dl, "music_windows": mv}
    json.dump(res, open(cut[:-4] + ".qc.json", "w"), ensure_ascii=False, indent=1)
    for r in dl:
        print(r["shot"], r["start"], r["ratio"], r["heard"])
    print("music windows:", [(w["from"], w["votes"]) for w in mv])


if __name__ == "__main__":
    main()
