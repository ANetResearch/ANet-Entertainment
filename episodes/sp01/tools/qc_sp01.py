#!/usr/bin/env python3
"""Audio QC of sp01 takes (adapted from tools/qc_episode.py): transcribe every take with a Gemini flash model
through gravitex, compare with the scripted lines, and ask whether music can be heard.
usage: qc_sp01.py [--workers 4] [--force KEY,KEY]   -> episodes/sp01/qc.json (resumable)"""
import base64, json, os, re, subprocess, sys, time, difflib
from concurrent.futures import ThreadPoolExecutor
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg as _cfg
import music_check as MC

ROOT = _cfg.ROOT
CFG = _cfg.load()["gravitex"]
NAME = "sp01"
MODELS = ("gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash")
Q = ('Listen to this audio clip from a documentary film shot. Reply with JSON only: {"speech": "exact transcript of all '
     'spoken words in the original language (Mandarin Chinese expected), empty string if none", "music": "none, or '
     'describe precisely which instruments/melody/score you hear (a steady machine hum, wind, water, drone, alarm, beeps '
     'or room tone is NOT music)", "ambience": "short description of non-speech sounds", "voice": "short description of '
     'each speaker voice (gender, approximate age)"}')


def norm(s):
    s = (s or "").replace("五五零", "550").replace("五百五十", "550").replace("莫斯", "MOSS").replace("moss", "MOSS")
    return re.sub(r"[^一-鿿A-Za-z0-9]", "", s).upper()


def listen(mp4):
    audio = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp4, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k",
                            "-f", "mp3", "-"], capture_output=True).stdout
    body = {"messages": [{"role": "user", "content": [{"type": "text", "text": Q},
            {"type": "input_audio", "input_audio": {"data": base64.b64encode(audio).decode(), "format": "mp3"}}]}]}
    for i, model in enumerate(MODELS * 3):
        body["model"] = model
        try:
            r = requests.post(CFG["url"] + "/v1/chat/completions", headers={"Authorization": "Bearer " + CFG["key"]},
                              json=body, timeout=90)
            txt = r.json()["choices"][0]["message"]["content"]
            m = re.search(r"\{.*\}", txt, re.S)
            d = json.loads(m.group(0))
            d["_model"] = model
            return d
        except Exception:
            time.sleep(2 + i)
    return None


def main():
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    force = set(sys.argv[sys.argv.index("--force") + 1].split(",")) if "--force" in sys.argv else set()
    script = {s["id"]: s for s in json.load(open(f"{ROOT}/series/{NAME}.json"))["shots"]}
    out_f = f"{ROOT}/episodes/{NAME}/qc.json"
    res = json.load(open(out_f)) if os.path.exists(out_f) else {}
    vdir = f"{ROOT}/episodes/{NAME}/video"
    vids = sorted(f for f in os.listdir(vdir) if f.endswith(".mp4") and (f[:-4] not in res or f[:-4] in force))

    def one(f):
        key = f[:-4]
        sid = key.split("_")[0]
        want = "".join(d["line"] for d in script[sid]["dialogue"])
        got = listen(f"{vdir}/{f}")
        if got is None:
            return key, None
        w, g = norm(want), norm(got.get("speech"))
        ratio = difflib.SequenceMatcher(None, w, g).ratio() if (w or g) else 1.0
        flags = []
        if not w and len(g) > 3: flags.append("unexpected_speech")
        if w and len(g) < 0.5 * len(w): flags.append("speech_missing")
        if w and len(g) > 1.35 * len(w) + 3: flags.append("extra_speech")
        if w and ratio < 0.6 and "speech_missing" not in flags: flags.append("speech_mismatch")
        mv = MC.check(f"{vdir}/{f}")                 # three-model vote, 2 of 3 = music
        if mv["music"]: flags.append("music?")
        return key, {"want": want, "heard": got.get("speech"), "ratio": round(ratio, 2), "music": got.get("music"),
                     "music_vote": mv,
                     "ambience": got.get("ambience"), "voice": got.get("voice"), "flags": flags, "model": got.get("_model")}

    with ThreadPoolExecutor(workers) as ex:
        for key, r in ex.map(one, vids):
            if r is not None:
                res[key] = r
                json.dump(res, open(out_f, "w"), ensure_ascii=False, indent=1)
            print(key, (r or {}).get("flags", "QC_FAILED"), (r or {}).get("ratio"), flush=True)
    bad = {k: v["flags"] for k, v in res.items() if [x for x in v["flags"] if x != "music?"]}
    print(f"{NAME}: {len(res)} takes checked, {len(bad)} with speech problems, "
          f"{sum('music?' in v['flags'] for v in res.values())} possible music")


if __name__ == "__main__":
    main()
