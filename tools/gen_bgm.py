#!/usr/bin/env python3
"""BGM by filming musicians: the H3 video model has native audio, so a clip of a performance gives a reusable music stem.
For each cue: one still (gpt image) -> 15s H3 clip -> music/src/<id>_<n>.mp4 + music/<id>_<n>.wav
usage: gen_bgm.py [--only ids] [--n 1]"""
import json, os, sys, time, base64, io, subprocess, requests
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(f"{ROOT}/tools/config.json")); AD = CFG["autodl"]; GX = CFG["gravitex"]
H = {"Authorization": AD["token"], "Content-Type": "application/json"}
CUES = {
 "elegy_cello": ("A lone cellist, seen from behind in silhouette, playing on a bare dark stage under one soft overhead light, empty concert hall.",
   "a solo cello plays a very slow, mournful elegy in D minor: long sustained bowed notes, a simple descending melody of great sadness and dignity, natural hall reverb"),
 "hymn_strings": ("A string orchestra of thirty players in black on a dim stage, seen from the back of the hall, conductor's arms raised.",
   "a string orchestra plays a slow, solemn hymn that swells: warm low strings, a broad rising melody in the violins, noble, tragic and hopeful at once, like a requiem turning into an anthem"),
 "choir_requiem": ("A large mixed choir in dark robes standing in rows in a stone cathedral lit by candles, seen from the nave.",
   "a large mixed choir sings a slow wordless requiem on 'ah' and 'oh' vowels, deep basses and soaring sopranos, long chords that swell and fade, vast cathedral reverb"),
 "musicbox": ("Extreme close-up of an old brass music box mechanism on a workbench, the pinned cylinder turning slowly against the steel comb, warm lamp light.",
   "an old music box plays a simple, fragile lullaby melody, slightly out of tune, each note ringing, slow and tender"),
 "tension_drums": ("Three percussionists striking huge taiko drums and a row of double basses behind them in a dark rehearsal hall, hard side light.",
   "low taiko drums pound a steady driving pulse while double basses and cellos play a fast repeating ostinato; relentless, urgent, building tension, no melody"),
 "piano_embers": ("Close shot of an old upright piano in a dim empty room, a pianist's hands on the keys, dust in a shaft of light.",
   "a solo piano plays sparse, slow, quiet notes with long silences between them, a simple warm melody in a major key, intimate felt-piano tone, gentle and consoling"),
 "ignite_orchestra": ("A full symphony orchestra and choir on a grand stage at full intensity, brass raised, timpani player mid-strike, wide shot from the balcony.",
   "a full symphony orchestra with choir plays a triumphant, overwhelming climax: blazing brass chords, pounding timpani, soaring strings and choir rising to a huge sustained major chord"),
 "drone_cold": ("A wide shot of a huge empty dark industrial hall with a single musician bowing a large metal sheet and a standing bass drum, cold blue light.",
   "a deep, cold, sustained low drone with slow evolving overtones and distant metallic resonances, almost no rhythm, ominous and vast"),
}


def uri(p):
    im = Image.open(p).convert("RGB"); im.thumbnail((1344, 1344)); b = io.BytesIO(); im.save(b, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def still(cid):
    out = f"{ROOT}/music/src/{cid}.png"
    if not os.path.exists(out):
        r = requests.post(GX["url"] + "/v1/images/generations", headers={"Authorization": "Bearer " + GX["key"]}, timeout=600,
                          json={"model": GX["image_model"], "prompt": CUES[cid][0] + " Photorealistic film still, 16:9, moody low-key lighting. No text.", "size": "1536x1024", "n": 1})
        open(out, "wb").write(base64.b64decode(r.json()["data"][0]["b64_json"]))
    return out


def one(job):
    cid, n = job
    mp4 = f"{ROOT}/music/src/{cid}_{n}.mp4"
    if not os.path.exists(mp4):
        img = uri(still(cid)); scene, music = CUES[cid]
        prompt = (f"subject_definitions: <Subject 1> is the performance scene from <Picture 1>; <Subject 2> is the same scene from <Picture 2>. "
                  f"summary: A filmed live music performance. {scene} detailed_description: [Shot 1] At 0.0s, locked-off tripod camera, a single continuous take with no cut; "
                  f"the musicians play continuously from the first frame to the last without stopping. Nobody speaks, no applause, no audience noise. "
                  f"overall_soundscape: ONLY the live music, clean concert recording: {music}. The music plays without interruption for the whole 15 seconds, no speech, no sound effects.")
        r = requests.post(f"{AD['base']}/{AD['workflow']}", headers=H, timeout=180,
                          data=json.dumps({"prompt": prompt, "duration": 15, "resolution": "768p横", "seed": 1000 + n, "ref_image_0": img, "ref_image_1": img})).json()
        if r.get("code") != "Success": return cid, n, "submit " + json.dumps(r, ensure_ascii=False)[:200]
        tid = r["data"]["task_id"]
        with open(f"{ROOT}/ledger/videos.jsonl", "a") as f: f.write(json.dumps({"ep": "bgm", "shot": cid, "take": str(n), "task": tid, "dur": 15, "cost": 0.75, "status": "ok"}) + "\n")
        for _ in range(160):
            time.sleep(15)
            d = requests.get(f"{AD['base']}/result/{tid}", headers=H, timeout=60).json().get("data", {})
            if d.get("status") == "SUCCESS":
                open(mp4, "wb").write(requests.get(d["results"][0]["url"], timeout=600).content); break
            if d.get("status") == "FAILED": return cid, n, "FAILED"
        else: return cid, n, "timeout"
    subprocess.run([f"{ROOT}/tools/ffmpeg", "-y", "-loglevel", "error", "-i", mp4, "-vn", "-ar", "48000", "-ac", "2", f"{ROOT}/music/{cid}_{n}.wav"])
    return cid, n, "ok"


if __name__ == "__main__":
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(CUES)
    n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 1
    jobs = [(c, k) for c in only for k in range(1, n + 1)]
    with ThreadPoolExecutor(12) as ex:
        for r in ex.map(one, jobs): print(*r, flush=True)
