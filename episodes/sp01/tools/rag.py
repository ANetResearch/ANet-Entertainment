#!/usr/bin/env python3
"""Mini RAG of the director console: cinematic vocabulary retrieval (BM25 over Chinese character bigrams plus
English words), small, deterministic and dependency-light.

Sources (the corpus and its index stay local, under rag/, and are never committed):
- three reference PDFs of the owner (director grading styles, look presets, a 37-style collection), extracted and
  split by director, by look preset, and by style x dimension (image and video prompts as separate entries);
- the camera / light / texture rules lexicon from our earlier H3 IR research (JSON files, one entry per term,
  about 1,700 entries over 20 axes);
- our own enrichment vocabulary for this film (tools/rag_vocab_sp01.jsonl, committed).

usage: rag.py build                       -> rag/corpus.jsonl
       rag.py query "<text>" [--mode fixed|enrich] [-k 5]
"""
import json, math, os, re, sys, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAG = os.path.join(ROOT, "rag")
CORPUS = os.path.join(RAG, "corpus.jsonl")
PDF_DIR = os.environ.get("SP01_RAG_PDF_DIR", os.path.join(RAG, "pdf"))
PDFS = {"directors": "15 位电影导演调色风格 AI 提示词模板.pdf", "looks": "15 种影视视觉风格 AI 提示词模板.pdf",
        "aigc": "AIGC电影风格提示词合集（196页）.pdf"}
RULES_DIR = os.environ.get("SP01_RAG_RULES_DIR", os.path.join(RAG, "rules"))
OURS = os.path.join(ROOT, "tools", "rag_vocab_sp01.jsonl")

# kinds that may be retrieved per shot. Whole-film looks (director grades, look presets, colour/grade dimensions)
# are never retrieved per shot: a look is chosen once, as a style preset, and locked (see styles.py).
CRAFT_KINDS = {
    "fixed": {"aigc:composition", "aigc:texture", "aigc:action", "aigc:scene", "aigc:video", "aigc:light",
              "rules:move", "rules:angle", "rules:size", "rules:position", "rules:comp", "rules:light", "rules:mood",
              "rules:sound", "rules:pacing", "rules:lens", "rules:texture", "rules:weather", "rules:time",
              "ours:camera", "ours:light", "ours:emotion", "ours:sound", "ours:pacing", "ours:focus", "ours:texture",
              "ours:archival", "ours:transition"},
    # enrich-only: craft without any look, grade, stock or texture
    "enrich": {"aigc:composition", "aigc:action", "aigc:video", "rules:move", "rules:angle", "rules:size",
               "rules:position", "rules:comp", "rules:mood", "rules:sound", "rules:pacing", "ours:camera",
               "ours:emotion", "ours:sound", "ours:pacing", "ours:focus", "ours:transition"},
}
CAPS = {"aigc": 2, "rules": 2, "ours": 3}


# ------------------------------------------------------------------ extraction
def pdf_text(path):
    import warnings
    warnings.filterwarnings("ignore")
    import fitz
    return "\n".join(p.get_text() for p in fitz.open(path))


def _split_numbered(text, src, kind):
    out = []
    parts = re.split(r"\n(?=\d{1,2}\s*[\.．]\s*\S)", "\n" + text)
    for p in parts:
        m = re.match(r"\s*(\d{1,2})\s*[\.．]\s*(.+)", p)
        if not m:
            continue
        title = m.group(2).split("\n")[0].strip()
        out.append({"id": f"{src}/{int(m.group(1)):02d}", "source": src, "kind": kind, "title": title,
                    "text": re.sub(r"\s*\n\s*", " ", p).strip()})
    return out


DIMS = {"构图与镜头": "composition", "色彩与光影": "light", "质感与氛围": "texture", "经典场景": "scene",
        "角色与动作": "action", "色彩色调": "grade", "色彩风格": "grade", "视觉风格": "grade", "色调细节": "grade"}


def _is_ascii_line(l):
    l = l.strip()
    return bool(l) and sum(c.isascii() for c in l) / len(l) > 0.85


def split_aigc(text):
    lines = text.split("\n")
    title_rx = re.compile(r"(影像风格提示词|风格提示词|风提示词)\s*$")
    styles, cur = [], None
    for l in lines:
        if title_rx.search(l.strip()) and len(l.strip()) <= 40:
            cur = {"title": l.strip(), "lines": []}
            styles.append(cur)
        elif cur:
            cur["lines"].append(l)
    out = []
    for si, st in enumerate(styles, 1):
        sid = f"aigc/{si:02d}"
        body = st["lines"]
        # dimension sections
        cur_dim, buf, n = None, [], 0
        def flush():
            nonlocal buf, n
            if cur_dim and buf:
                t = re.sub(r"\s*\n\s*", "", "\n".join(buf)).strip()
                if t:
                    n += 1
                    out.append({"id": f"{sid}/{DIMS[cur_dim]}{n}", "source": "aigc", "kind": f"aigc:{DIMS[cur_dim]}",
                                "title": f"{st['title']} · {cur_dim}", "text": t[:500]})
            buf = []
        for l in body:
            s = l.strip()
            key = s.split("：")[0].split(":")[0]
            if key in DIMS:
                flush(); cur_dim = key
                rest = s[len(key):].lstrip("：:").strip()
                if rest:
                    buf.append(rest)
                continue
            if cur_dim and (s.startswith("提示词") or s.startswith("细节补充") or s.startswith("运镜") or _is_ascii_line(s)):
                flush(); cur_dim = None
                continue
            if cur_dim:
                buf.append(s)
        flush()
        joined = "\n".join(body)
        # video prompts: "运镜：..." followed by Chinese text
        for vi, m in enumerate(re.finditer(r"运镜[：:]", joined), 1):
            seg, chars = [], 0
            for l in joined[m.start():].split("\n"):
                if _is_ascii_line(l):
                    if chars > 30:
                        break
                    continue
                seg.append(l.strip()); chars += len(l.strip())
                if chars > 60 and l.strip().endswith("。"):
                    break
                if chars > 220:
                    break
            t = "".join(seg)
            out.append({"id": f"{sid}/video{vi}", "source": "aigc", "kind": "aigc:video",
                        "title": f"{st['title']} · 视频提示词 {vi}", "text": t[:300]})
        # English image prompts: runs of ASCII lines
        run, ii = [], 0
        for l in body + [""]:
            if _is_ascii_line(l):
                run.append(l.strip())
            else:
                t = " ".join(run)
                if len(t) > 200:
                    ii += 1
                    out.append({"id": f"{sid}/image_en{ii}", "source": "aigc", "kind": "aigc:image_en",
                                "title": f"{st['title']} · image prompt {ii}", "text": t[:700]})
                run = []
    return out


def rules_entries():
    out = []
    for f in sorted(glob.glob(os.path.join(RULES_DIR, "*.json"))):
        axis = os.path.basename(f)[:-5]
        d = json.load(open(f))
        if not isinstance(d, list):
            continue
        for e in d:
            on = [t.lstrip("~") for t in e.get("on", [])]
            out.append({"id": f"rules/{axis}/{e['id']}", "source": "rules", "kind": f"rules:{axis}",
                        "title": f"{axis}: {e['id']}", "text": " / ".join(on) + " — " + e.get("text", ""),
                        "tags": e.get("tags", [])})
    return out


def ours_entries():
    out = []
    for l in open(OURS):
        e = json.loads(l)
        out.append({"id": e["id"], "source": "ours", "kind": f"ours:{e['kind']}", "title": e["title"],
                    "text": e["text"], "tags": e.get("tags", [])})
    return out


def build():
    os.makedirs(os.path.join(RAG, "src"), exist_ok=True)
    texts = {}
    for k, fn in PDFS.items():
        cache = os.path.join(RAG, "src", k + ".txt")
        if not os.path.exists(cache):
            open(cache, "w").write(pdf_text(os.path.join(PDF_DIR, fn)))
        texts[k] = open(cache).read()
    ents = (_split_numbered(texts["directors"], "directors", "director") +
            _split_numbered(texts["looks"], "looks", "look_preset") +
            split_aigc(texts["aigc"]) + rules_entries() + ours_entries())
    with open(CORPUS, "w") as f:
        for e in ents:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    c = collections.Counter(e["kind"] for e in ents)
    print(len(ents), "entries", dict(sorted(c.items())))


# ------------------------------------------------------------------ BM25
STOP = set("the a an and or of to in on at with from by for is are be as it its this that into over under then "
           "very more most one two only each all any no not".split())


def tokens(text):
    t = text.lower()
    out = [w for w in re.findall(r"[a-z][a-z0-9\-]{1,}", t) if w not in STOP]
    for run in re.findall(r"[一-鿿]+", t):
        out += [run[i:i + 2] for i in range(len(run) - 1)] or [run]
    return out


class Index:
    def __init__(self, path=CORPUS):
        self.docs = [json.loads(l) for l in open(path)]
        self.tf = [collections.Counter(tokens(d["title"] + " " + d["text"] + " " + " ".join(d.get("tags", []))))
                   for d in self.docs]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.len) / max(1, len(self.len))
        df = collections.Counter()
        for c in self.tf:
            df.update(c.keys())
        n = len(self.docs)
        self.idf = {w: math.log(1 + (n - v + 0.5) / (v + 0.5)) for w, v in df.items()}

    def score(self, q, i, k1=1.5, b=0.75):
        c, L = self.tf[i], self.len[i]
        return sum(self.idf.get(w, 0) * c[w] * (k1 + 1) / (c[w] + k1 * (1 - b + b * L / self.avg)) for w in q if w in c)

    def query(self, text, mode="fixed", k=5, caps=CAPS):
        q = tokens(text)
        allowed = CRAFT_KINDS[mode]
        scored = sorted(((self.score(q, i), i) for i, d in enumerate(self.docs) if d["kind"] in allowed),
                        key=lambda x: (-x[0], self.docs[x[1]]["id"]))
        out, per = [], collections.Counter()
        for s, i in scored:
            d = self.docs[i]
            if s <= 0 or per[d["source"]] >= caps.get(d["source"], 2):
                continue
            per[d["source"]] += 1
            out.append(dict(d, score=round(s, 2)))
            if len(out) >= k:
                break
        return out


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build()
    elif sys.argv[1] == "query":
        mode = sys.argv[sys.argv.index("--mode") + 1] if "--mode" in sys.argv else "fixed"
        k = int(sys.argv[sys.argv.index("-k") + 1]) if "-k" in sys.argv else 5
        for d in Index().query(sys.argv[2], mode, k):
            print(d["score"], d["id"], d["kind"], d["title"], "|", d["text"][:120])
