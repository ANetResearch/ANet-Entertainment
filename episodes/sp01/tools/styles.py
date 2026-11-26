#!/usr/bin/env python3
"""Style presets of the director console (a product feature: "fixed aesthetic" mode).

A preset is data: id, names, the locked look fields (camera body, film stock or video format, lens, aperture,
filter, grade, light system, texture), key terms the validator checks for, and a short English suffix written in
our own words.  With style=<preset id> the director locks the whole combination into every call, so the look is
identical across calls and shots while content and seed vary.  With no style, the director only enriches craft.

Sources: our own presets (the era looks of the film sp01, written by us) and presets reduced from the mini-RAG
sources (15 look presets, 15 director grading styles, 37 styles), each rewritten by the LLM into our own words and
checked for verbatim overlap with its source before it is accepted.

usage: styles.py build [--workers 8]     -> tools/style_presets.json (ours + reduced presets)
       styles.py list
"""
import json, os, re, sys, time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRESETS = os.path.join(ROOT, "tools", "style_presets.json")
FIELDS = ("camera", "stock", "lens", "aperture", "filter", "grade", "light", "texture")

OURS = [
    {"id": "sp01-home48", "name_zh": "2040年代家庭录像", "name_en": "2040s family home video", "source": "ours",
     "camera": "a 2040s consumer handheld family camera on full auto", "stock": "low-bitrate consumer digital video",
     "lens": "fixed wide-normal zoom around 28mm equivalent", "aperture": "automatic, deep but soft focus",
     "filter": "none", "grade": "warm faded beige, lifted greyish blacks, low saturation",
     "light": "available window daylight, auto-exposure pumping, highlights blooming",
     "texture": "macroblocking on motion, chroma noise in shadows, slight motion blur, focus hunting",
     "key_terms": ["consumer handheld family camera", "low-bitrate"],
     "suffix": "remembered family footage: warm, soft, imperfect, held by a parent's hand"},
    {"id": "sp01-lab50s", "name_zh": "2050年代研究院档案", "name_en": "2050s institute film archive", "source": "ours",
     "camera": "an Arriflex 416 Super 16 camera", "stock": "Kodak Vision3 500T 7219 pushed one stop",
     "lens": "a 12-120mm documentary zoom", "aperture": "f/2.8", "filter": "none",
     "grade": "muted, desaturated, a green-cyan fluorescent cast with one warm practical",
     "light": "cold fluorescent tubes plus one warm desk lamp, deep shadows",
     "texture": "lively Super 16 grain, slightly soft resolution",
     "key_terms": ["Super 16", "Vision3 500T"],
     "suffix": "the institute's own observational record, watching people work from across the room"},
    {"id": "sp01-arch58", "name_zh": "2058年新闻资料", "name_en": "2058 broadcast news archive", "source": "ours",
     "camera": "a shoulder-mounted 2/3-inch ENG broadcast camera", "stock": "broadcast tape, later dubbed",
     "lens": "an 18x broadcast zoom", "aperture": "auto iris", "filter": "none",
     "grade": "hot clipped whites, crushed murky shadows, chroma smear on reds",
     "light": "floodlights, emergency strobes and whatever is there",
     "texture": "interlaced softness, faint scan lines, compression noise, an occasional tape dropout",
     "key_terms": ["ENG broadcast camera", "scan lines"],
     "suffix": "urgent news footage of a disaster operation, the operator running with the crew"},
    {"id": "sp01-v75", "name_zh": "2075年危机现场纪实", "name_en": "2075 crisis verite", "source": "ours",
     "camera": "a Sony FX6 full-frame documentary camera handheld", "stock": "S-Cinetone at high ISO",
     "lens": "a 24mm prime", "aperture": "f/4", "filter": "UV only",
     "grade": "deep solid blacks, true-to-life skin, colour only from the practical sources",
     "light": "available light only: alarm red, monitor glow, flashlights; volumetric haze and silhouettes",
     "texture": "visible high-ISO noise, focus occasionally hunting",
     "key_terms": ["Sony FX6", "S-Cinetone"],
     "suffix": "raw verite in a city that has lost its light; faces and key objects readable, the rest dark"},
    {"id": "sp01-int78", "name_zh": "2078年口述史采访", "name_en": "2078 oral-history interview", "source": "ours",
     "camera": "a Sony FX6 on a locked tripod", "stock": "S-Cinetone", "lens": "a 50mm prime", "aperture": "f/2.8",
     "filter": "Black Pro-Mist 1/8",
     "grade": "neutral, gently warm skin, background one to two stops under the face",
     "light": "one large soft key 45 degrees from frame left, negative fill on the right, a small warm practical in the background",
     "texture": "clean, fine detail, real skin texture",
     "key_terms": ["Sony FX6", "50mm"],
     "suffix": "a calm, restrained oral-history interview, the subject looking past the lens"},
]

SYS = """You turn one entry of a cinematography style reference into a style preset for a video-prompt tool.
Return JSON only with these string fields: name_zh, name_en, camera, stock, lens, aperture, filter, grade, light,
texture, suffix, and key_terms (a list of 2 short exact terms that must appear in any prompt using this preset,
normally the camera body and the stock or format).
Rules: equipment names (camera bodies, film stocks, lenses, filters) may be named as facts. Every descriptive field
(grade, light, texture, suffix) must be written in your own words in English, concise (under 25 words each); never
copy more than four consecutive words from the source. Director or film names may only appear in name_zh/name_en.
If the source does not give a field, choose one consistent with the rest of the look. The combination must be
physically consistent (one camera, one stock or format, one lens)."""


def _ds(messages):
    import requests
    key = open(os.path.expanduser("~/.config/deepseek/key")).read().strip()
    for attempt in range(4):
        try:
            r = requests.post("https://api.deepseek.com/chat/completions", timeout=300,
                              headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
                              data=json.dumps({"model": "deepseek-flash", "messages": messages, "max_tokens": 8000}))
            return r.json()["choices"][0]["message"]["content"]
        except Exception:
            time.sleep(5 + 5 * attempt)
    return None


def _overlap(src, text, n_zh=10, n_en=6):
    """longest verbatim overlap check: any Chinese run of n_zh chars or English run of n_en words copied."""
    s = re.sub(r"\s+", " ", src.lower())
    for run in re.findall(r"[一-鿿]{%d,}" % n_zh, text):
        for i in range(len(run) - n_zh + 1):
            if run[i:i + n_zh] in s:
                return run[i:i + n_zh]
    w = re.findall(r"[a-z0-9'\-/]+", text.lower())
    for i in range(len(w) - n_en + 1):
        g = " ".join(w[i:i + n_en])
        if g in s:
            return g
    return None


def sources():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import rag
    docs = [json.loads(l) for l in open(rag.CORPUS)]
    out = []
    for d in docs:
        if d["kind"] in ("director", "look_preset"):
            out.append((("dir-" if d["kind"] == "director" else "look-") + d["id"].split("/")[1], d["title"], d["text"]))
    by_style = {}
    for d in docs:
        if d["source"] == "aigc":
            sid = d["id"].split("/")[1]
            by_style.setdefault(sid, {"title": d["title"].split(" · ")[0], "parts": []})["parts"].append(d["text"])
    for sid, v in sorted(by_style.items()):
        out.append((f"style-{sid}", v["title"], "\n".join(v["parts"])[:3500]))
    return out


def build(workers=8):
    srcs = sources()

    def one(item):
        pid, title, text = item
        for _ in range(2):
            out = _ds([{"role": "system", "content": SYS},
                       {"role": "user", "content": f"Entry title: {title}\nEntry text:\n{text}"}])
            if not out:
                continue
            try:
                p = json.loads(re.search(r"\{.*\}", out, re.S).group(0))
            except Exception:
                continue
            body = " ".join(str(p.get(k, "")) for k in ("grade", "light", "texture", "suffix"))
            hit = _overlap(text, body)
            if hit or not all(isinstance(p.get(k), str) and p[k] for k in FIELDS + ("suffix", "name_en")):
                continue
            p = {k: p[k] for k in ("name_zh", "name_en") + FIELDS + ("suffix",) if k in p} | {
                "key_terms": [t for t in p.get("key_terms", []) if isinstance(t, str)][:3]}
            p.update(id=pid, source=pid.split("-")[0] + " (reduced from the reference PDFs, rewritten)")
            return p
        return None

    with ThreadPoolExecutor(workers) as ex:
        reduced = [p for p in ex.map(one, srcs) if p]
    data = {"version": 1, "fields": list(FIELDS), "presets": OURS + reduced}
    json.dump(data, open(PRESETS, "w"), ensure_ascii=False, indent=1)
    print(len(OURS), "ours +", len(reduced), "reduced of", len(srcs))


def load():
    if os.path.exists(PRESETS):
        return {p["id"]: p for p in json.load(open(PRESETS))["presets"]}
    return {p["id"]: p for p in OURS}


def lock_line(p):
    return (f"Locked look \"{p['name_en']}\" (style preset {p['id']}): {p['camera']}; {p['stock']}; {p['lens']} at "
            f"{p['aperture']}; filter {p['filter']}; grade: {p['grade']}; light: {p['light']}; texture: {p['texture']}; "
            f"{p['suffix']}.")


def look_terms(presets=None):
    """terms that signal a film look (for the enrich-only check)."""
    ts = set()
    for p in (presets or load()).values():
        for t in p.get("key_terms", []):
            if len(t) >= 4:
                ts.add(t.lower())
    return sorted(ts)


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 8)
    else:
        for p in load().values():
            print(p["id"], "|", p["name_en"], "|", p["camera"], "|", p["stock"], "|", p.get("key_terms"))
