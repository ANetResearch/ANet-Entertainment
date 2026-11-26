#!/usr/bin/env python3
"""Audio QC for an episode: transcribe every take, compare with the scripted line.
usage: qc_episode.py EP [--workers 4]   -> episodes/epNN/qc.json  (resumable)"""
import base64, json, os, re, subprocess, sys, time, difflib
from concurrent.futures import ThreadPoolExecutor
import requests
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "tools", "config.json")))["gravitex"]
FF = os.path.join(ROOT, "tools", "ffmpeg")
MODELS = ("gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash")
Q = ('Listen to this audio clip from a film shot. Reply with JSON only: {"speech": "exact transcript of all spoken words '
     'in the original language, empty string if none", "music": "none, or describe precisely which instruments/melody/score '
     'you hear (a steady machine hum, wind, drone or room tone is NOT music)", "ambience": "short description of non-speech sounds"}')
norm = lambda s: re.sub(r"[^一-鿿A-Za-z0-9]", "", s or "")

def listen(mp4):
    audio = subprocess.run([FF, "-loglevel", "error", "-i", mp4, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k", "-f", "mp3", "-"],
                           capture_output=True).stdout
    body = {"messages": [{"role": "user", "content": [{"type": "text", "text": Q},
            {"type": "input_audio", "input_audio": {"data": base64.b64encode(audio).decode(), "format": "mp3"}}]}]}
    for i, model in enumerate(MODELS * 3):
        body["model"] = model
        try:
            r = requests.post(CFG["url"] + "/v1/chat/completions", headers={"Authorization": "Bearer " + CFG["key"]}, json=body, timeout=60)
            txt = r.json()["choices"][0]["message"]["content"]
            m = re.search(r"\{.*\}", txt, re.S)
            return json.loads(m.group(0))
        except Exception:
            time.sleep(2 + i)
    return None

def main():
    ep = int(sys.argv[1]); name = f"ep{ep:02d}"
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    script = {s["id"]: s for s in json.load(open(f"{ROOT}/series/{name}.json"))["shots"]}
    out_f = f"{ROOT}/episodes/{name}/qc.json"
    res = json.load(open(out_f)) if os.path.exists(out_f) else {}
    vids = sorted(f for f in os.listdir(f"{ROOT}/episodes/{name}/video") if f.endswith(".mp4") and f[:-4] not in res)
    def one(f):
        key = f[:-4]; sid = key.split("_")[0]
        st_f = f"{ROOT}/episodes/{name}/tasks/{key}.json"
        prompt = json.load(open(st_f)).get("prompt", "") if os.path.exists(st_f) else ""
        want = "".join(re.findall(r"<d>\[Chinese\] (.*?)</d>", prompt))
        got = listen(f"{ROOT}/episodes/{name}/video/{f}")
        if got is None:
            return key, None
        w, g = norm(want), norm(got.get("speech"))
        ratio = difflib.SequenceMatcher(None, w, g).ratio() if (w or g) else 1.0
        flags = []
        if not w and len(g) > 3: flags.append("unexpected_speech")
        if w and len(g) < 0.5 * len(w): flags.append("speech_missing")
        if w and len(g) > 1.35 * len(w) + 3: flags.append("extra_speech")
        if w and ratio < 0.6 and "speech_missing" not in flags: flags.append("speech_mismatch")
        if str(got.get("music", "none")).strip().lower() not in ("none", "", "none."): flags.append("music?")
        return key, {"want": want, "heard": got.get("speech"), "ratio": round(ratio, 2), "music": got.get("music"), "flags": flags}
    with ThreadPoolExecutor(workers) as ex:
        for key, r in ex.map(one, vids):
            if r is not None:
                res[key] = r
                json.dump(res, open(out_f, "w"), ensure_ascii=False, indent=1)
            print(key, (r or {}).get("flags", "QC_FAILED"), flush=True)
    bad = {k: v["flags"] for k, v in res.items() if [x for x in v["flags"] if x != "music?"]}
    print(f"{name}: {len(res)} takes checked, {len(bad)} with speech problems, {sum('music?' in v['flags'] for v in res.values())} possible music")
if __name__ == "__main__":
    main()
