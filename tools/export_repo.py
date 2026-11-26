#!/usr/bin/env python3
"""Export finished material into the GitHub working tree (repo/).
usage: export_repo.py EP [EP ...]
Per episode: clips/ (best take per shot, original files), alt/ (other takes), storyboard/ (JPEG), prompts/ (exact prompt sent), script.json"""
import glob, json, os, shutil, sys
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import package as PK
ROOT = PK.ROOT
REPO = os.path.join(ROOT, "repo")

def cp(src, dst):
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True); shutil.copy2(src, dst)

def episode(ep):
    name = f"ep{ep:02d}"; d = json.load(open(f"{ROOT}/series/{name}.json")); out = f"{REPO}/episodes/{name}"
    n = 0
    for s in d["shots"]:
        s.pop("_amu_male", None)
        best = PK.pick(name, s["id"])
        for take in sorted(glob.glob(f"{ROOT}/episodes/{name}/video/{s['id']}_*.mp4")):
            key = os.path.basename(take)[:-4]
            assert os.path.getsize(take) < 95 * 2**20, take          # GitHub hard limit is 100 MB per file
            if take == best:
                cp(take, f"{out}/clips/{name}_{s['id']}.mp4"); n += 1
                for stale in glob.glob(f"{out}/alt/{name}_{key}.mp4"): os.remove(stale)
            else:
                cp(take, f"{out}/alt/{name}_{key}.mp4")
            st = f"{ROOT}/episodes/{name}/tasks/{key}.json"
            if os.path.exists(st):
                t = json.load(open(st)); os.makedirs(f"{out}/prompts", exist_ok=True)
                open(f"{out}/prompts/{name}_{key}.txt", "w").write(
                    f"# {name} {key}  duration={t.get('duration')}s  seed={t.get('seed')}\n# input images: {t.get('images')}\n\n{t.get('prompt','')}\n")
        fr = f"{ROOT}/episodes/{name}/storyboard/{s['id']}.png"; jpg = f"{out}/storyboard/{name}_{s['id']}.jpg"
        if os.path.exists(fr) and not os.path.exists(jpg):
            os.makedirs(os.path.dirname(jpg), exist_ok=True); Image.open(fr).convert("RGB").save(jpg, quality=88)
    json.dump(d, open(f"{out}/script.json", "w"), ensure_ascii=False, indent=1)
    qc = f"{ROOT}/episodes/{name}/qc.json"
    if os.path.exists(qc): shutil.copy2(qc, f"{out}/audio_qc.json")
    print(name, n, "/", len(d["shots"]), "clips", flush=True)

if __name__ == "__main__":
    for a in sys.argv[1:]: episode(int(a))
