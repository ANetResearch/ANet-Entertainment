#!/usr/bin/env python3
"""Export sp01 material into the GitHub working tree (repo/), new paths only.
usage: export_sp01.py [--picks work/picks.json] [--cut work/cut/sp01-roughcut-repo.mp4]
  repo/series/sp01.json
  repo/refs/sp01/                 new reference images + refs.json + generation prompts
  repo/episodes/sp01/clips/       chosen take per shot (sp01_sNN.mp4)
  repo/episodes/sp01/alt/         every other take (sp01_sNN_X.mp4)
  repo/episodes/sp01/storyboard/  storyboard frames (JPEG) and superseded versions
  repo/episodes/sp01/prompts/     the exact prompt of every take, the director records (retrieved ids and titles only),
                                  the MiniMax-IR documents (A/B reference) and the director v1 outputs
  repo/episodes/sp01/tools/       the pipeline, director harness, RAG code, style presets, edit script
  repo/episodes/sp01/{script.json, audio_qc.json, takes.json, TREATMENT.md, sp01-roughcut.mp4}
The extracted PDF corpus (rag/) and the private exemplar prompt are never exported."""
import glob, json, os, re, shutil, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.join(ROOT, "repo")
EP = os.path.join(ROOT, "episodes", "sp01")
OUT = os.path.join(REPO, "episodes", "sp01")
LIMIT = 95 * 2**20
TOOLS = ["cfg.py", "pipeline_sp01.py", "director.py", "director_system.md", "rag.py", "rag_vocab_sp01.jsonl", "styles.py",
         "style_presets.json", "qc_sp01.py", "music_check.py", "edit_sp01.py", "build_sp01.py", "build_refs_sp01.py", "ir.py",
         "review_sheet.py", "task_status.py", "gen_image.py", "export_sp01.py", "sheet.py", "speech_times.py"]


def cp(src, dst):
    assert os.path.getsize(src) < LIMIT, src
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def sanitize_record(rec):
    """keep the retrieved ids and titles; drop retrieved snippet text (third-party PDF text stays local)."""
    r = dict(rec)
    req = r.get("request", "")
    i = req.find("参考词汇")
    if i >= 0:
        tail = req[i:].split("\n")
        keep = [tail[0]] + [re.sub(r"^(\[[^\]]+\] [^:]+):.*$", r"\1", l) for l in tail[1:] if l.startswith("[")]
        rest = [l for l in tail[1:] if not l.startswith("[")]
        r["request"] = req[:i] + "\n".join(keep + rest)
    for a in r.get("attempts", []):
        a.pop("reasoning", None)
    return r


def main():
    picks = json.load(open(sys.argv[sys.argv.index("--picks") + 1])) if "--picks" in sys.argv else {}
    cut = sys.argv[sys.argv.index("--cut") + 1] if "--cut" in sys.argv else None
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import edit_sp01 as E
    d = json.load(open(os.path.join(ROOT, "series", "sp01.json")))
    takes = {}
    for s in d["shots"]:
        sid = s["id"]
        best = E.pick(sid, picks)
        for t in sorted(glob.glob(f"{EP}/video/{sid}_*.mp4")):
            k = os.path.basename(t)[:-4]
            if t == best:
                cp(t, f"{OUT}/clips/sp01_{sid}.mp4")
                takes[sid] = k
                stale = f"{OUT}/alt/sp01_{k}.mp4"
                if os.path.exists(stale):
                    os.remove(stale)
            else:
                cp(t, f"{OUT}/alt/sp01_{k}.mp4")
            st = f"{EP}/tasks/{k}.json"
            if os.path.exists(st):
                j = json.load(open(st))
                os.makedirs(f"{OUT}/prompts", exist_ok=True)
                open(f"{OUT}/prompts/sp01_{k}.txt", "w").write(
                    f"# sp01 {k}  duration={j.get('duration')}s  seed={j.get('seed')}  prompt_source={j.get('prompt_source', 'ir')}"
                    f"  cost={j.get('cost')}\n# input images: {j.get('images')}\n\n{j.get('prompt', '')}\n")
        fr = f"{EP}/storyboard/{sid}.png"
        if os.path.exists(fr):
            jpg = f"{OUT}/storyboard/sp01_{sid}.jpg"
            if not os.path.exists(jpg) or os.path.getmtime(jpg) < os.path.getmtime(fr):
                os.makedirs(os.path.dirname(jpg), exist_ok=True)
                Image.open(fr).convert("RGB").save(jpg, quality=88)
    for old in glob.glob(f"{EP}/storyboard/old/*.png"):
        jpg = f"{OUT}/storyboard/superseded/sp01_{os.path.basename(old)[:-4]}.jpg"
        if not os.path.exists(jpg):
            os.makedirs(os.path.dirname(jpg), exist_ok=True)
            Image.open(old).convert("RGB").save(jpg, quality=85)
    # prompt records
    for sub, dst in (("director", "director"), ("director_v1_norag", "director_v1_norag"),
                     ("director_superseded", "director_superseded"), ("director_enrich", "director_enrich")):
        for f in glob.glob(f"{EP}/{sub}/*"):
            o = f"{OUT}/prompts/{dst}/{os.path.basename(f)}"
            os.makedirs(os.path.dirname(o), exist_ok=True)
            if f.endswith(".record.json"):
                json.dump(sanitize_record(json.load(open(f))), open(o, "w"), ensure_ascii=False, indent=1)
            else:
                shutil.copy2(f, o)
    for f in glob.glob(f"{EP}/ir/*"):
        cp(f, f"{OUT}/prompts/minimax_ir/{os.path.basename(f)}")
    # script, qc, treatment, tools
    json.dump(d, open(f"{OUT}/script.json", "w"), ensure_ascii=False, indent=1)
    cp(os.path.join(ROOT, "series", "sp01.json"), os.path.join(REPO, "series", "sp01.json"))
    if os.path.exists(f"{EP}/qc.json"):
        shutil.copy2(f"{EP}/qc.json", f"{OUT}/audio_qc.json")
    json.dump(takes, open(f"{OUT}/takes.json", "w"), indent=1)
    shutil.copy2(f"{EP}/TREATMENT.md", f"{OUT}/TREATMENT.md")
    for t in TOOLS:
        cp(os.path.join(ROOT, "tools", t), f"{OUT}/tools/{t}")
    cfg = json.load(open(os.path.join(ROOT, "tools", "config.json")))
    json.dump(cfg, open(f"{OUT}/tools/config.example.json", "w"), indent=1)
    # refs
    for f in glob.glob(os.path.join(ROOT, "refs", "sp01", "*")):
        if f.endswith(".png") or f.endswith(".json"):
            cp(f, os.path.join(REPO, "refs", "sp01", os.path.basename(f)))
    for f, dst in (("work/ab_validate.json", "prompts/ab_validate.json"), ("work/speech_times.json", "roughcut_speech_times.json")):
        if os.path.exists(os.path.join(ROOT, f)):
            shutil.copy2(os.path.join(ROOT, f), f"{OUT}/{dst}")
    if cut:
        cp(cut, f"{OUT}/sp01-roughcut.mp4")
        edl = cut[:-4] + ".edl.json"
        if os.path.exists(edl):
            shutil.copy2(edl, f"{OUT}/roughcut_edl.json")
    n = sum(1 for _ in glob.glob(f"{OUT}/clips/*.mp4"))
    print(f"exported: {n} clips, {len(glob.glob(f'{OUT}/alt/*.mp4'))} alt takes")


if __name__ == "__main__":
    main()
