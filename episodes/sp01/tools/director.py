#!/usr/bin/env python3
"""导演台 (director console): a small prompt-compiler harness for MiniMax H3 reference-to-video.

For each shot an LLM (DeepSeek, OpenAI-compatible chat API) turns the natural-language intent of the shooting
script into the six-section H3 document; a deterministic validator checks it; on errors one repair call is made
with the error list; if the document is still invalid, the deterministic template (pipeline build_prompt) is used.

usage: director.py [--only s01,s02] [--workers 6] [--force] [--model deepseek-flash]
  -> episodes/sp01/director/<shot>.txt           final prompt (used by pipeline_sp01.py videos)
     episodes/sp01/director/<shot>.record.json   input, every model output, validator results, final source

Design notes (reference design for an IR stage):
- the system prompt (director_system.md) holds the H3 spec, the film's fixed constraints and one exemplar of
  form (director_exemplar.txt, a private reference prompt that is not published);
- the request carries everything the model cannot see: the ordered pictures with their roles and descriptions,
  the storyboard frame description, the era look, the exact dialogue (already in spoken form), the duration;
- validation is deterministic and explains each error in one line, so that the repair call is targeted.
"""
import argparse, json, os, re, sys, time, threading
from concurrent.futures import ThreadPoolExecutor
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_sp01 as P
import rag as RAG
import styles as ST

ROOT = P.ROOT
OUTD = os.path.join(P.OUT, "director")
DS_BASE = "https://api.deepseek.com"
SECTIONS = P.SECTIONS
lock = threading.Lock()
ERA_STYLE = {"home48": "sp01-home48", "lab50s": "sp01-lab50s", "arch58": "sp01-arch58", "v75": "sp01-v75",
             "int78": "sp01-int78"}
_INDEX = None


def index():
    global _INDEX
    with lock:
        if _INDEX is None:
            _INDEX = RAG.Index()
    return _INDEX


def resolve_style(shot, style):
    """style: 'auto' (the film: one fixed preset per era), 'none' (enrich only) or a preset id."""
    if style in (None, "", "none"):
        return None
    pid = ERA_STYLE[shot["era"]] if style == "auto" else style
    return ST.load()[pid]


def retrieve(shot, preset, k=5):
    tp = shot["tpl"]
    q = " ".join([shot["video"], tp["mood"], tp["camera"], P.TYPE_ZH[shot["type"]], P.TYPE_EN[shot["type"]],
                  preset["name_zh"] + " " + preset["name_en"] if preset else ""])
    return index().query(q, "fixed" if preset else "enrich", k)


def ds_key():
    return open(os.path.expanduser("~/.config/deepseek/key")).read().strip()


def system_prompt():
    here = os.path.dirname(os.path.abspath(__file__))
    sp = open(os.path.join(here, "director_system.md")).read()
    ex_f = os.path.join(here, "director_exemplar.txt")
    ex = open(ex_f).read().strip() if os.path.exists(ex_f) else "(exemplar not available)"
    return sp.replace("{EXEMPLAR}", ex)


# ------------------------------------------------------------------ request
def request_text(shot, chosen, preset=None, refs=()):
    tp = shot["tpl"]
    pics = ["Picture 1: the storyboard keyframe of this shot (opening frame). It shows: " + shot["frame"].strip()
            + " " + tp["blocking"].strip()]
    for i, r in enumerate(chosen):
        ref = P.REFS[r]
        pics.append(f"Picture {i + 2}: {ref['en_name']} ({ref['kind']} reference; role: {ref['role']}). {ref['en']}")
    lines = shot.get("dialogue") or []
    if lines:
        dl = "\n".join(f"{k + 1}. {P.SPEAKER.get(d['who'], 'an extra')} — {P.SPEAKER_ZH.get(d['who'], '')}: "
                       f"{P.spoken(d['line'])}" for k, d in enumerate(lines))
        dl = "台词（逐字照抄，按顺序，每句放进一个 <d>[Chinese] ...</d>）：\n" + dl
    else:
        dl = "本镜头没有台词。"
    return "\n".join([
        f"镜头 {shot['id']}：{P.TYPE_ZH[shot['type']]}，时长 {shot['dur']} 秒，16:9 横屏，24fps，单镜头一镜到底（只写 [Shot 1]）。",
        (f"风格模式：固定风格（style preset {preset['id']}）。锁定外观 / Locked look（detailed_description 第一行必须照此书写，"
         f"并逐字包含 {preset.get('key_terms')}）：{ST.lock_line(preset)}") if preset else
        "风格模式：只做专业化补全（没有选择风格预设）。保持导演意图里写到的外观，不添加任何胶片、机身、调色或导演风格。",
        f"该类型的纪录片默认机位：{P.TYPE_EN[shot['type']]}",
        f"导演意图（自然语言）：{shot['video']}",
        f"情绪：{tp['mood']}",
        f"建议的景别与运镜（只做一个主要运镜）：{tp['camera']}",
        f"景深与虚实：{tp['blur']}",
        "输入图片（按发送顺序；Subject N 对应 Picture N）：",
        *pics,
        dl,
        (f"服装锁定（本镜头，优先于参考图里的服装）/ Costume lock for this shot: {shot['costume']}") if shot.get("costume") else "",
        f"现场环境声：{tp['soundscape']}",
        ("参考词汇（检索所得，只借用术语与思路，不要整段照抄，不得改变锁定外观）：\n" + "\n".join(
            f"[{r['id']}] {r['title']}: {r['text'][:220]}" for r in refs)) if refs else "",
        "画面中没有字幕、文字、数字和水印；没有任何音乐和旁白；只说普通话。",
    ])


# ------------------------------------------------------------------ model
def call_model(messages, model):
    body = {"model": model, "messages": messages, "max_tokens": 12000, "stream": False}
    last = None
    for attempt in range(4):
        try:
            r = requests.post(DS_BASE + "/chat/completions", headers={"Authorization": "Bearer " + ds_key(),
                              "Content-Type": "application/json"}, data=json.dumps(body), timeout=600)
            d = r.json()
            if "choices" not in d:
                last = f"http {r.status_code} {str(d.get('error'))[:200]}"
                time.sleep(5 + 10 * attempt)
                continue
            m = d["choices"][0]["message"]
            return (m.get("content") or "").strip(), d.get("usage"), (m.get("reasoning_content") or "")
        except Exception as e:
            last = type(e).__name__
            time.sleep(5 + 10 * attempt)
    raise RuntimeError(f"model call failed: {last}")


def clean(text):
    t = text.strip()
    t = re.sub(r"^```[a-zA-Z]*\n", "", t)
    t = re.sub(r"\n```$", "", t)
    return t.strip()


# ------------------------------------------------------------------ validator
NEG = re.compile(r"\b(no|not|without|never|none|free of|devoid|absent|absence|zero|unscored)\b", re.I)
MUSIC = re.compile(r"\b(?:(?i:music|musical|melod\w*|score|soundtrack|singing|piano|violin|cello|guitar|synthesizers?|"
                   r"synth pad|orchestra\w*|percussion|drums?|chords?)|songs?|sings)\b")   # "Song" (capital) is a name
TEXT = re.compile(r"\b(subtitles?|captions?|on-screen text|title card|lettering|watermark|logo overlay|text overlay|"
                  r"timestamp)\b", re.I)


def nz(s):
    return re.sub(r"[^一-鿿A-Za-z0-9]", "", s)


def validate(doc, shot, n_images, preset=None, request=""):
    errs = []
    heads = [m.group(1) for m in re.finditer(r"(?m)^(%s):\s*$" % "|".join(SECTIONS), doc)]
    if heads != list(SECTIONS):
        errs.append(f"sections must be exactly {list(SECTIONS)} in this order, each header alone on its line; found {heads}")
        return errs
    sec = P.split_sections(doc)
    # subjects <-> pictures
    sd = [l.strip() for l in sec["subject_definitions"].splitlines() if l.strip()]
    nums = []
    for l in sd:
        m = re.match(r"<Subject (\d+)> is .*?\bfrom <Picture (\d+)>", l)
        if not m:
            errs.append(f"subject_definitions line does not start with '<Subject N> is ... from <Picture N>': {l[:80]}")
            continue
        if m.group(1) != m.group(2):
            errs.append(f"<Subject {m.group(1)}> must come from <Picture {m.group(1)}>, not <Picture {m.group(2)}>")
        nums.append(int(m.group(1)))
    if nums != list(range(1, n_images + 1)):
        errs.append(f"there must be exactly one subject line per picture, Subject 1..{n_images} in order; found {nums}")
    pics = [int(x) for x in re.findall(r"<Picture (\d+)>", doc)]
    if pics and max(pics) > n_images:
        errs.append(f"<Picture {max(pics)}> is referenced but only {n_images} pictures are sent")
    subs = [int(x) for x in re.findall(r"<Subject (\d+)>", doc)]
    if subs and max(subs) > n_images:
        errs.append(f"<Subject {max(subs)}> is referenced but only {n_images} subjects exist")
    # retention
    rl = [l.strip() for l in sec["retention_analysis"].splitlines() if l.strip()]
    rnums = [int(m.group(1)) for l in rl for m in [re.match(r"<Subject (\d+)> \(", l)] if m]
    if rnums != list(range(1, n_images + 1)):
        errs.append(f"retention_analysis needs one line per subject '<Subject N> (appears in ...): fully_preserved — ...', "
                    f"N = 1..{n_images} in order; found {rnums}")
    # shots and timestamps
    dd = sec["detailed_description"]
    shots = re.findall(r"\[Shot (\d+)\] At (\d+(?:\.\d+)?)s", dd)
    if not shots:
        errs.append("detailed_description has no '[Shot 1] At 0.0s, ...' paragraph")
    else:
        ks = [int(k) for k, _ in shots]
        ts = [float(t) for _, t in shots]
        if ks != list(range(1, len(ks) + 1)):
            errs.append(f"shot numbers must be 1..n in order; found {ks}")
        if ts[0] != 0.0:
            errs.append(f"the first shot must start 'At 0.0s'; found {ts[0]}")
        if any(b <= a for a, b in zip(ts, ts[1:])):
            errs.append(f"shot times must strictly increase; found {ts}")
        if any(t >= shot["dur"] for t in ts):
            errs.append(f"every shot time must be below the clip duration {shot['dur']}s; found {ts}")
    if len(re.findall(r"\[Shot \d+\]", dd)) != len(shots):
        errs.append("every [Shot N] tag must be followed by ' At X.Xs'")
    if "16:9" not in dd.split("\n")[0]:
        errs.append("the first line of detailed_description must state '16:9 horizontal, single clip ...'")
    # dialogue
    want = [P.spoken(d["line"]) for d in shot.get("dialogue") or []]
    got = re.findall(r"<d>\[([^\]]+)\]\s*(.*?)</d>", doc, re.S)
    if any(lang != "Chinese" for lang, _ in got):
        errs.append("every <d> tag must be '<d>[Chinese] ...</d>'")
    gtxt = [t.strip() for _, t in got]
    if not want and gtxt:
        errs.append(f"this shot has no dialogue, but the document makes someone say: {gtxt}")
    if want:
        if nz("".join(gtxt)) != nz("".join(want)):
            errs.append(f"the spoken lines must be exactly, in order and once each: {want}; found {gtxt}")
        for w in want:
            if nz("".join(gtxt)).count(nz(w)) != 1:
                errs.append(f"the line '{w}' must appear verbatim exactly once")
        chars = len(nz("".join(want)))
        if chars > 4.2 * shot["dur"]:
            errs.append(f"{chars} characters in {shot['dur']} s is faster than about 4 per second")
    if re.search(r"<d>", sec["overall_soundscape"] + sec["summary"]):
        errs.append("<d> tags belong only in detailed_description")
    # music and text
    if not re.match(r"^N/?A\b", sec["non_diegetic_music"].strip()):
        errs.append("non_diegetic_music must be exactly 'N/A'")
    for name in ("overall_soundscape", "detailed_description", "summary"):
        for sent in re.split(r"(?<=[.;!?])\s+", sec[name]):
            if MUSIC.search(sent) and not NEG.search(sent):
                errs.append(f"{name} mentions music: '{sent[:100]}' (only diegetic location sound; no music at all)")
            if TEXT.search(sent) and not NEG.search(sent):
                errs.append(f"{name} asks for on-screen text: '{sent[:100]}'")
    # style mode
    first = dd.split("\n")[0].lower()
    if preset:
        miss = [t for t in preset.get("key_terms", []) if t.lower() not in first]
        if miss:
            errs.append(f"fixed style {preset['id']}: the first line of detailed_description must name the locked look "
                        f"verbatim, including {miss}")
    else:
        req = request.lower()
        added = [t for t in ST.look_terms() if t in doc.lower() and t not in req]
        if added:
            errs.append(f"enrich-only mode: the document adds look terms the request did not ask for: {added[:5]}")
    return errs


# ------------------------------------------------------------------ orchestration
def direct(shot, model, force=False, style="auto", outd=None):
    outd = outd or OUTD
    os.makedirs(outd, exist_ok=True)
    fin_f, rec_f = f"{outd}/{shot['id']}.txt", f"{outd}/{shot['id']}.record.json"
    if os.path.exists(fin_f) and not force:
        return shot["id"], "skip"
    chosen = P.pick_refs(shot)
    n = 1 + len(chosen)
    preset = resolve_style(shot, style)
    refs = retrieve(shot, preset)
    req = request_text(shot, chosen, preset, refs)
    rec = {"shot": shot["id"], "model": model, "images": P.images_of(shot), "ref_ids": chosen,
           "style": {"mode": "fixed" if preset else "enrich", "preset": preset["id"] if preset else None},
           "retrieved": [{"id": r["id"], "title": r["title"], "kind": r["kind"], "score": r["score"]} for r in refs],
           "request": req, "attempts": [], "ts": time.strftime("%F %T")}
    msgs = [{"role": "system", "content": system_prompt()}, {"role": "user", "content": req}]
    final, source = None, None
    for attempt in range(2):
        try:
            out, usage, reasoning = call_model(msgs, model)
        except Exception as e:
            rec["attempts"].append({"error": str(e)})
            break
        doc = clean(out)
        errs = validate(doc, shot, n, preset, req)
        rec["attempts"].append({"output": doc, "errors": errs, "usage": usage, "reasoning_chars": len(reasoning)})
        if not errs:
            final, source = doc, "director" if attempt == 0 else "director_repaired"
            break
        msgs += [{"role": "assistant", "content": out},
                 {"role": "user", "content": "The document has these errors. Return the whole corrected document only, "
                  "with the same six sections:\n- " + "\n- ".join(errs)}]
    if final is None:
        final, source = P.build_prompt(shot, chosen), "template_fallback"
        rec["fallback_errors"] = validate(final, shot, n, None, final)
    rec.update(final=final, source=source)
    with lock:
        json.dump(rec, open(rec_f, "w"), ensure_ascii=False, indent=1)
        open(fin_f, "w").write(final + "\n")
    errs = [a.get("errors") for a in rec["attempts"]]
    return shot["id"], f"{source} attempts={len(rec['attempts'])} errors={[len(e) if e is not None else 'X' for e in errs]}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--model", default="deepseek-flash")
    ap.add_argument("--outdir", default="", help="output folder under episodes/sp01 (default: director)")
    ap.add_argument("--style", default="auto", help="auto = one fixed preset per era (the film); none = enrich only; "
                    "or a preset id from tools/style_presets.json")
    a = ap.parse_args()
    ep = P.load_ep()
    only = set(a.only.split(",")) if a.only else None
    work = [s for s in ep["shots"] if not only or s["id"] in only]
    with ThreadPoolExecutor(a.workers) as ex:
        for sid, st in ex.map(lambda s: direct(s, a.model, a.force, a.style, os.path.join(P.OUT, a.outdir) if a.outdir else None), work):
            print(time.strftime("%T"), sid, st, flush=True)


if __name__ == "__main__":
    main()
