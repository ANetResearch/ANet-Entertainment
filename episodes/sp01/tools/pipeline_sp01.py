#!/usr/bin/env python3
"""Pipeline of the side story sp01 《第一页》 (adapted from tools/pipeline.py of the series).

  pipeline_sp01.py frames [--workers N] [--only s01,s02] [--force]     storyboard frames (gravitex gpt-image)
  pipeline_sp01.py ir     [--workers N] [--only ...] [--force]          compile each shot's prompt with the
                                                                         official MiniMax H3-Context-IR, then post-edit
  pipeline_sp01.py videos [--takes a,b] [--workers N] [--only ...] [--dry]   clips via AutoDL minimax_h3_adl_int8
  pipeline_sp01.py status                                               spend so far

Differences from the series pipeline:
- episode id is the string "sp01" (series/sp01.json, episodes/sp01/); refs = refs/refs.json + refs/sp01/refs.json;
- each shot has an "era" with its own documentary look (home video 2048, institute archive 2050s, broadcast
  archive 2058, raw verite 2075, clean interview 2078), used in frame and video prompts;
- the input images of a shot (storyboard frame + seeded random refs, 2..5 in total) are drawn once per shot, so
  every take of a shot shares the image set and the IR-compiled prompt; takes differ by seed;
- the prompt is the IR-compiled six-section document (episodes/sp01/ir/<shot>.txt) after post-editing (exact
  dialogue, no music, no subtitles, era look); without it, the series template (build_prompt) is used.
"""
import argparse, base64, hashlib, json, os, random, re, sys, threading, time
from concurrent.futures import ThreadPoolExecutor
import requests
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg as _cfg

ROOT = _cfg.ROOT
CFG = _cfg.load()
AD = CFG["autodl"]
REFS = json.load(open(os.path.join(ROOT, "refs", "refs.json")))
REFS.update(json.load(open(os.path.join(ROOT, "refs", "sp01", "refs.json"))))
NAME = "sp01"
SCRIPT = os.path.join(ROOT, "series", NAME + ".json")
OUT = os.path.join(ROOT, "episodes", NAME)
LEDGER = os.path.join(ROOT, "ledger", "videos.jsonl")
lock = threading.Lock()

# ------------------------------------------------------------------ looks per era (cinematic research: IR rules
# "look combinations" of body / stock / lens / filter, documentary defaults, one main camera move per shot)
FRAME_ERA = {
    "home48": ("This must look like a frame grab from a degraded consumer family video recorded in 2048 on a cheap "
               "handheld camera: soft breathing focus, auto-exposure blooming in the sunlight, warm faded colour with a "
               "beige cast, low-light noise in the shadows, mild compression blocking, slight motion blur, intimate "
               "off-centre framing; a quiet domestic documentary feel with soft diffused daylight and no harsh shadows."),
    "lab50s": ("This must look like a frame from observational documentary footage in a research institute's own 2050s "
               "film archive, shot on Super 16 colour negative: lively visible grain, slightly soft resolution, cold "
               "fluorescent tube light mixed with one warm desk lamp, deep shadows, muted desaturated palette, "
               "imperfect handheld framing."),
    "arch58": ("This must look like a frame from archival 2058 broadcast news footage shot on a shoulder-mounted ENG "
               "camera and recorded on tape: interlaced softness, faint scan lines, chroma smear on reds, clipped hot "
               "whites, crushed murky shadows, compression noise, urgent imperfect framing."),
    "v75": ("This must look like a frame from raw verite documentary footage shot handheld in 2075 on a high-ISO "
            "full-frame documentary camera in available light only (emergency red light, cold monitor glow, "
            "flashlight): visible sensor noise, deep solid blacks, volumetric haze and silhouettes, true-to-life skin "
            "tones, imperfect framing."),
    "int78": ("This must look like a frame from a clean oral-history documentary interview recorded in 2078 on a Sony "
              "FX6 with a 50mm lens at f/2.8: one soft key light from the left with gentle falloff, true-to-life skin "
              "texture, shallow depth of field, neutral colour; plain talking-head framing, subject slightly off "
              "centre looking past the lens at the interviewer."),
}
FRAME_RULES = (" NOT a movie still, NOT concept art, NOT CGI, no glossy render look, no teal-and-orange grading, no lens "
               "flares beyond what the light really does; show ONLY the people and objects described above, never add "
               "an extra person, presenter or foreground figure that is not described. Keep every person, place, prop "
               "and logo consistent with the supplied reference images (identity, age and costume as described), but "
               "render them in this documentary look. 16:9 frame. No captions, no subtitles, no watermark, no timestamp "
               "overlay, no legible text or numbers anywhere.")
VIDEO_ERA = {
    "home48": ("degraded consumer home video recorded in 2048 on a cheap handheld family camera: soft breathing autofocus, "
               "auto-exposure blooming in the sunlight, warm faded colour with a beige cast, mild compression blocking "
               "and low-light noise, slight motion blur, intimate unsteady framing, soft diffused daylight with no harsh "
               "shadows"),
    "lab50s": ("observational documentary footage from a research institute's own 2050s film archive, shot on Super 16 "
               "colour negative: lively visible grain, slightly soft resolution, cold fluorescent light mixed with one "
               "warm desk lamp, muted desaturated palette, deep shadows, imperfect handheld framing"),
    "arch58": ("archival 2058 broadcast news footage from a shoulder-mounted ENG camera recorded on tape: interlaced "
               "softness, faint scan lines, chroma smear on reds, clipped hot whites, crushed murky shadows, compression "
               "noise, urgent imperfect framing"),
    "v75": ("raw verite documentary footage shot handheld in 2075 on a high-ISO full-frame documentary camera in available "
            "light only: visible sensor noise, deep solid blacks, volumetric haze and silhouettes, true-to-life skin "
            "tones, focus occasionally hunting"),
    "int78": ("a clean oral-history documentary interview recorded in 2078 on a Sony FX6 with a 50mm lens at f/2.8: one "
              "soft key light from the left with gentle falloff, true-to-life skin texture, shallow depth of field, "
              "neutral colour, calm and restrained"),
}
ERA_ZH = {
    "home48": ("2048 年的家庭录像：廉价手持家用摄像机拍摄，自动对焦来回呼吸，阳光过曝溢出，暖色褪色、偏米色，暗部有噪点和轻微压缩块，"
               "轻微运动模糊，构图随意不稳；是枝裕和式的家庭日常纪实质感，低饱和、柔和漫射光、没有硬阴影。这是记忆，可以偏柔、偏模糊。"),
    "lab50s": ("2050 年代研究院自己的影像档案：Super 16 彩色负片质感，颗粒明显、分辨率略软，冷白荧光灯混一盏暖台灯，低饱和，深阴影，"
               "构图不完美的手持观察式纪录片镜头。"),
    "arch58": ("2058 年的新闻资料影像：肩扛 ENG 广播级摄像机录在磁带上，隔行扫描的柔软感、淡淡的扫描线、红色拖影、高光溢出、暗部发闷、"
               "压缩噪点，构图仓促。这是旧素材，可以明显退化、偏模糊。"),
    "v75": ("2075 年现场纪实：高感光全画幅纪录片摄影机手持拍摄，只有现场光（警报红光、监视器冷光、手电光），明显噪点、深黑、体积雾和剪影，"
            "真实肤色，焦点偶尔寻找；关键的人脸和物件要清楚。"),
    "int78": ("2078 年口述史纪录片采访：Sony FX6 纪录片摄影机，50mm 镜头，f/2.8，S-Cinetone 色彩，左侧单一柔光，浅景深，真实肤色，"
              "中性色调，干净克制。"),
}
TYPE_ZH = {"interview": "纪录片采访镜头", "verite": "纪录片现场纪实镜头", "archival": "纪录片中引用的旧资料影像",
           "establishing": "纪录片空镜", "macro": "纪录片细节特写镜头"}
TYPE_EN = {
    "interview": "documentary talking-head interview, tripod camera, subject looks past the lens at the interviewer",
    "verite": "fly-on-the-wall documentary camera, shoulder-mounted handheld with small reframings, operator reacting late",
    "archival": "archival footage quoted inside a documentary",
    "establishing": "documentary establishing shot on a long zoom lens, atmospheric haze",
    "macro": "documentary insert close-up grabbed handheld, focus breathing",
}
SPEAKER = {
    "nian_child": "Little Nian (a six-year-old girl's high, soft, clear voice)",
    "nian": "Nian (a woman in her mid-thirties, low, calm, restrained voice)",
    "song": "Song (a man in his early thirties, warm and gentle voice with a smile in it)",
    "song58": "Song (a man in his early forties, warm, steady, slightly hoarse voice)",
    "song_radio": "Song (a man in his forties, voice distorted through a diving-helmet radio, breathing hard)",
    "boye58": "Boye at forty-four (male voice, brisk, slightly gruff and stubborn)",
    "boye": "Boye (old male voice, slow and slightly hoarse)",
    "chair": "The committee chairman (a man in his fifties, measured official voice)",
    "moss": "MOSS (calm, polite, emotionless synthetic male voice coming from a loudspeaker)",
}
SPEAKER_ZH = {
    "nian_child": "小念念（6 岁小女孩的声音，稚嫩清亮）", "nian": "宋念（三十多岁女性的声音，低沉、平静、克制）",
    "song": "宋工（三十出头男性的声音，温和、带笑意）", "song58": "宋工（四十出头男性的声音，温和坚定，略沙哑）",
    "song_radio": "宋工（四十多岁男性的声音，从潜水头盔对讲机里传出，失真、喘着气）",
    "boye58": "四十四岁的波爷（男声，干脆、略带倔强）", "boye": "波爷（六十多岁老人的声音，缓慢、沙哑）",
    "chair": "评审会主席（五十多岁男性官员的声音，平稳、官方）", "moss": "MOSS（平静、礼貌、没有情绪的合成男声，从扬声器传出）",
}
SAY = {"550W": "五五零W"}       # pronunciation in prompts; the script keeps the written form


def spoken(line):
    for a, b in SAY.items():
        line = line.replace(a, b)
    return line


def load_ep():
    return json.load(open(SCRIPT))


# ---------------------------------------------------------------- frames
def cmd_frames(a):
    ep = load_ep()
    jobs = []
    for s in ep["shots"]:
        ids = [r for r in s["refs"] if r in REFS][:4]
        legend = "; ".join(f"reference image {i+1} = {REFS[r]['en_name']}: {REFS[r]['zh']}" for i, r in enumerate(ids))
        prompt = s["frame"].strip() + (f" ({legend})" if legend else "") + " " + FRAME_ERA[s["era"]] + FRAME_RULES
        jobs.append({"id": s["id"], "out": f"episodes/{NAME}/storyboard/{s['id']}.png", "prompt": prompt,
                     "inputs": [REFS[r]["file"] for r in ids]})
    os.makedirs(OUT, exist_ok=True)
    jf = os.path.join(OUT, "storyboard_jobs.json")
    json.dump(jobs, open(jf, "w"), ensure_ascii=False, indent=1)
    cmd = [sys.executable, os.path.join(ROOT, "tools", "gen_image.py"), jf, "--workers", str(a.workers)]
    if a.only:
        cmd += ["--only", a.only]
    if a.force:
        cmd += ["--force"]
    os.execv(sys.executable, cmd)


# ---------------------------------------------------------------- inputs
def data_uri(rel):
    """Downscaled JPEG data URI (cached) for a project-relative image path."""
    src = os.path.join(ROOT, rel)
    key = hashlib.md5((rel + str(os.path.getmtime(src))).encode()).hexdigest()
    cache = os.path.join(ROOT, ".cache", key + ".jpg")
    if not os.path.exists(cache):
        os.makedirs(os.path.dirname(cache), exist_ok=True)
        im = Image.open(src)
        if im.mode in ("RGBA", "LA", "P"):
            im = im.convert("RGBA")
            bg = Image.new("RGB", im.size, (255, 255, 255))
            bg.paste(im, mask=im.split()[-1])
            im = bg
        im = im.convert("RGB")
        im.thumbnail((1344, 1344))
        im.save(cache, quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(open(cache, "rb").read()).decode()


def pick_refs(shot):
    """storyboard + seeded random subset of the shot's refs, total number of images random in 2..5 (once per shot)."""
    rng = random.Random(f"{NAME}/{shot['id']}/a")
    cands = [r for r in shot["refs"] if r in REFS]
    total = rng.randint(2, 5)
    k = max(1, min(total - 1, len(cands)))
    return sorted(rng.sample(cands, k), key=cands.index)


def take_seed(shot, take):
    return random.Random(f"{NAME}/{shot['id']}/{take}/seed").randint(1, 2**31 - 1)


def images_of(shot):
    return [f"episodes/{NAME}/storyboard/{shot['id']}.png"] + [REFS[r]["file"] for r in pick_refs(shot)]


# ---------------------------------------------------------------- template prompt (fallback, series format)
def build_prompt(shot, chosen):
    tp = shot["tpl"]
    dur = int(shot["dur"])
    subj = [f"<Subject 1> is the storyboard keyframe of this shot from <Picture 1>, serving as composition, lighting and "
            f"blocking reference. {shot['frame'].strip()} {tp['blocking'].strip()}"]
    ret = ["<Subject 1> (appears in the whole clip): fully_preserved — composition, environment, lighting and layout retained as the opening frame."]
    for i, r in enumerate(chosen):
        ref = REFS[r]
        n = i + 2
        subj.append(f"<Subject {n}> is {ref['en_name']} from <Picture {n}>, serving as {ref['role']}. {ref['en']}")
        how = {"character": "face, outfit, hairstyle and accessories retained; only pose and expression change.",
               "location": "environment, lighting and layout retained as the location.",
               "prop": "shape and surface details retained as the prop.",
               "logo": "shape and colours retained exactly as an in-world mark."}[ref["kind"]]
        ret.append(f"<Subject {n}> (appears in this shot): fully_preserved — {how}")
    said = [f"{SPEAKER.get(d['who'], 'An extra (ordinary voice)')} says, <d>[Chinese] {spoken(d['line'])}</d>;"
            for d in shot.get("dialogue") or []]
    shot_txt = (f"[Shot 1] At 0.0s, {tp['camera'].strip()}; pacing: natural speed, a single continuous take with no cut. "
                f"{tp['blocking'].strip()} Start: {tp['start'].strip()} Middle: {tp['middle'].strip()} End: {tp['end'].strip()} "
                f"Mood: {tp['mood'].strip()}. Blur: {tp['blur'].strip()} ")
    if said:
        last = spoken(shot["dialogue"][-1]["line"])
        shot_txt += " ".join(said) + (f" Final line of this shot: end on “{last[-8:]}”, complete the whole sentence, no cut-off; "
                                       f"after the last line nobody speaks. Hold the last frame.")
    else:
        shot_txt += ("No character speaks any line in this shot; if people are present their murmur is indistinct, unintelligible "
                     "Mandarin Chinese walla only, never any other language. Hold the last frame.")
    return "\n".join([
        "subject_definitions:", *subj, "",
        "summary:", tp["summary"].strip().replace("550W", "五五零W"), "",
        "retention_analysis:", *ret, "",
        "detailed_description:",
        f"16:9 horizontal, single clip {dur}.0s, 24fps, {VIDEO_ERA[shot['era']]}; {TYPE_EN[shot['type']]}; real documentary "
        "footage, not a movie, not CGI, unposed and unstaged; no hard subtitles, no burned-in captions, no overlay "
        "logo/watermark/platform bugs, no on-screen text.",
        shot_txt, "",
        "overall_soundscape:", tp["soundscape"].strip().rstrip(".") + "; raw production location sound only, dry and "
        "unscored: no background music, no score, no melody. Any background voices are indistinct Mandarin Chinese.", "",
        "non_diegetic_music:", "N/A (none: this is an unscored documentary location recording)"])


# ---------------------------------------------------------------- IR
def ir_brief(shot, chosen):
    """Chinese brief sent to the official H3-Context-IR, with a legend of the pictures actually sent."""
    legend = ["图1是本镜头的分镜关键帧，决定构图、光线、景别和人物站位。"]
    for i, r in enumerate(chosen):
        legend.append(f"图{i+2}是参考图：{REFS[r]['zh']}。")
    lines = []
    for d in shot.get("dialogue") or []:
        lines.append(f"{SPEAKER_ZH.get(d['who'], '群众角色')}说：“{spoken(d['line'])}”")
    tp = shot["tpl"]
    txt = [f"{TYPE_ZH[shot['type']]}，{shot['dur']} 秒，16:9 横屏，单镜头一镜到底，中间不切换。",
           "画面风格：" + ERA_ZH[shot["era"]],
           "".join(legend),
           f"景别与运镜（本镜头只做这一个主要运镜）：{tp['camera']}。",
           "内容：" + shot["video"],
           ("台词（必须一字不差，普通话）：" + "；".join(lines) + "。台词说完之后没有人再说话。") if lines else
           "这个镜头没有任何台词；如有人声，只是听不清的普通话背景人声。",
           "声音：只有现场同期声（环境声和人物说话声）。严禁任何背景音乐、配乐、旋律、鼓点和旁白。",
           "画面中没有字幕、没有任何文字、数字和水印。"]
    return "\n".join(txt)


SECTIONS = ("subject_definitions", "summary", "retention_analysis", "detailed_description", "overall_soundscape",
            "non_diegetic_music")
MUSIC_RX = re.compile(r"\b(music|musical|melod\w*|score|soundtrack|singing|piano|violin|cello|synthesizers?|synth pad|orchestra\w*|"
                      r"percussion|drums?|drumbeat)\b", re.I)          # note: "Song" is a character name


def split_sections(doc):
    out, cur = {}, None
    for line in doc.splitlines():
        m = re.match(r"^\s*(%s)\s*:\s*(.*)$" % "|".join(SECTIONS), line)
        if m:
            cur = m.group(1)
            out[cur] = [m.group(2)] if m.group(2).strip() else []
        elif cur:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def finalize_ir(raw, shot, n_images):
    """Post-edit an IR document: exact dialogue, no music, no subtitles, era look. Returns (doc, notes) or (None, why)."""
    sec = split_sections(raw)
    if any(k not in sec for k in SECTIONS):
        return None, "missing sections: " + ",".join(k for k in SECTIONS if k not in sec)
    notes = []
    pics = [int(x) for x in re.findall(r"<Picture (\d+)>", raw)]
    if pics and max(pics) > n_images:
        return None, f"picture {max(pics)} > {n_images} images"
    # dialogue: same number of lines, exact text, in order
    want = [spoken(d["line"]) for d in shot.get("dialogue") or []]
    got = re.findall(r"<d>\[Chinese\]\s*(.*?)</d>", sec["detailed_description"], re.S)
    def nz(x):
        return re.sub(r"[^一-鿿A-Za-z0-9]", "", x)
    if len(got) == len(want):
        it = iter(want)
        dd = re.sub(r"<d>\[Chinese\]\s*(.*?)</d>", lambda m: f"<d>[Chinese] {next(it)}</d>", sec["detailed_description"], flags=re.S)
        if got != want:
            notes.append("dialogue text restored")
    elif nz("".join(got)) == nz("".join(want)):
        dd = sec["detailed_description"]          # the IR split a line at a natural pause; the words are exact
        notes.append(f"line split into {len(got)} parts by the IR (words exact)")
    else:
        return None, f"dialogue count {len(got)} != {len(want)} and text differs: {got}"
    # drop any sentence that mentions music positively
    def scrub(text):
        keep = []
        for sent in re.split(r"(?<=[.!?])\s+", text):
            if MUSIC_RX.search(sent) and not re.search(r"\b(no|without|never|none|free of|devoid|absent|absence|excluding|zero)\b", sent, re.I):
                if "<d>" in sent or "[Shot" in sent:
                    notes.append("music word kept in a structural sentence: " + sent[:90])
                else:
                    notes.append("dropped: " + sent[:90])
                    continue
            keep.append(sent)
        return " ".join(keep)
    dd = "\n\n".join(scrub(p) for p in dd.split("\n\n"))
    look = (f"Documentary look of this era: {VIDEO_ERA[shot['era']]}; {TYPE_EN[shot['type']]}. Real documentary footage, "
            "unposed and unstaged, not a movie, not CGI. No hard subtitles, no burned-in captions, no on-screen text, no "
            "watermark, no logo overlay.")
    paras = dd.split("\n\n")
    paras.insert(1 if len(paras) > 1 else 0, look)
    dd = "\n\n".join(paras)
    if not want:
        dd += ("\n\nNo character speaks any line in this shot; any human voices are indistinct, unintelligible Mandarin "
               "Chinese walla only.")
    snd = scrub(sec["overall_soundscape"]).rstrip(". ") + (". Raw production location sound only, dry and unscored: no "
                                                            "background music, no score, no melody of any kind.")
    doc = "\n".join(["subject_definitions:", sec["subject_definitions"], "",
                     "summary:", sec["summary"], "",
                     "retention_analysis:", sec["retention_analysis"], "",
                     "detailed_description:", dd, "",
                     "overall_soundscape:", snd, "",
                     "non_diegetic_music:", "N/A"])
    return doc, notes


def cmd_ir(a):
    import ir as IR
    ep = load_ep()
    only = set(a.only.split(",")) if a.only else None
    d = os.path.join(OUT, "ir")
    os.makedirs(d, exist_ok=True)

    def one(s):
        raw_f, fin_f = f"{d}/{s['id']}.raw.txt", f"{d}/{s['id']}.txt"
        chosen = pick_refs(s)
        imgs = images_of(s)
        if not os.path.exists(os.path.join(ROOT, imgs[0])):
            return s["id"], "NO_FRAME"
        brief = ir_brief(s, chosen)
        if a.force or not os.path.exists(raw_f):
            open(f"{d}/{s['id']}.brief.txt", "w").write(brief + "\n")
            try:
                raw = IR.compile_prompt(brief, s["dur"], [os.path.join(ROOT, p) for p in imgs], tag=f"{NAME}/{s['id']}")
            except Exception as e:
                return s["id"], f"IR_FAIL {e}"
            open(raw_f, "w").write(raw + "\n")
        doc, notes = finalize_ir(open(raw_f).read(), s, len(imgs))
        if doc is None:
            return s["id"], f"POSTEDIT_REJECT {notes} (template prompt will be used)"
        open(fin_f, "w").write(doc + "\n")
        json.dump({"images": imgs, "ref_ids": chosen, "notes": notes}, open(f"{d}/{s['id']}.json", "w"), ensure_ascii=False, indent=1)
        return s["id"], f"ok {len(doc)} chars {notes[:3]}"

    work = [s for s in ep["shots"] if not only or s["id"] in only]
    with ThreadPoolExecutor(a.workers) as ex:
        for sid, st in ex.map(one, work):
            print(time.strftime("%T"), sid, st, flush=True)


def prompt_for(shot, take=""):
    """Production prompt: the director harness (tools/director.py, DeepSeek) output; the template for takes named 't*'
    (A/B reference). The MiniMax-IR documents in ir/ are kept as A/B reference only (takes a/b of the first batch)."""
    if take.startswith("t"):
        return build_prompt(shot, pick_refs(shot)), "template"
    if take.startswith("n"):                  # A/B: director in enrich-only mode (no style preset)
        f = os.path.join(OUT, "director_enrich", shot["id"] + ".txt")
        if os.path.exists(f):
            return open(f).read().strip(), "director_enrich"
    rec = os.path.join(OUT, "director", shot["id"] + ".record.json")
    f = os.path.join(OUT, "director", shot["id"] + ".txt")
    if os.path.exists(f):
        src = json.load(open(rec)).get("source", "director") if os.path.exists(rec) else "director"
        return open(f).read().strip(), src
    return build_prompt(shot, pick_refs(shot)), "template"


# ---------------------------------------------------------------- videos
def ledger_add(rec):
    with lock, open(LEDGER, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def spent():
    """Money already charged + worst-case cost of still-open tasks."""
    done, open_tasks = 0.0, {}
    if os.path.exists(LEDGER):
        for line in open(LEDGER):
            r = json.loads(line)
            if r.get("event") == "submit":
                open_tasks[r["task_id"]] = r["seconds"] * AD["price_per_sec"]
            else:
                open_tasks.pop(r.get("task_id"), None)
                done += float(r.get("cost") or 0)
    return done, sum(open_tasks.values())


def api(method, url, **kw):
    err = None
    for attempt in range(6):
        try:
            r = requests.request(method, url, headers={"Authorization": AD["token"], "Content-Type": "application/json"},
                                 timeout=180, **kw)
            return r.json()
        except Exception as e:
            err = e
            time.sleep(5 + 5 * attempt)
    raise RuntimeError(f"api failed: {type(err).__name__}")


def run_take(shot, take, dry=False):
    tag = f"{NAME}/{shot['id']}_{take}"
    mp4 = os.path.join(OUT, "video", f"{shot['id']}_{take}.mp4")
    state_f = os.path.join(OUT, "tasks", f"{shot['id']}_{take}.json")
    if os.path.exists(mp4):
        return tag, "skip"
    images = images_of(shot)
    if not os.path.exists(os.path.join(ROOT, images[0])):
        return tag, "NO_FRAME"
    os.makedirs(os.path.dirname(mp4), exist_ok=True)
    os.makedirs(os.path.dirname(state_f), exist_ok=True)
    state = json.load(open(state_f)) if os.path.exists(state_f) else {}
    if os.environ.get("NO_SUBMIT") and (not state.get("task_id") or state.get("status") == "FAILED"):
        return tag, "NOT_SUBMITTED"
    if not state.get("task_id") or state.get("status") == "FAILED":
        seed = take_seed(shot, take) + state.get("retries", 0) + (1 if state.get("status") == "FAILED" else 0)
        prompt, src = prompt_for(shot, take)
        dur = int(shot["dur"])
        if dry:
            return tag, f"DRY {dur}s imgs={len(images)} src={src} seed={seed}\n{prompt}\n"
        hold = "hold-" + tag
        with lock:
            done, pending = spent()
            if done + pending + dur * AD["price_per_sec"] > AD["budget_cny"]:
                return tag, f"BUDGET_STOP spent={done:.2f} pending={pending:.2f}"
            with open(LEDGER, "a") as f:
                f.write(json.dumps({"event": "submit", "task_id": hold, "shot": tag, "seconds": dur,
                                    "ts": time.strftime("%F %T")}, ensure_ascii=False) + "\n")
        body = {"prompt": prompt, "duration": dur, "resolution": "768p横", "seed": seed}
        for i, p in enumerate(images):
            body[f"ref_image_{i}"] = data_uri(p)
        try:
            d = api("POST", f"{AD['base']}/{AD['workflow']}", data=json.dumps(body))
        except Exception as e:
            d = {"code": "Exception", "msg": str(e)[:200]}
        ok = d.get("code") == "Success"
        with lock, open(LEDGER, "a") as f:
            f.write(json.dumps({"task_id": hold, "shot": tag, "cost": 0, "status": "HOLD_RELEASED"}) + "\n")
            if ok:
                tid = d["data"]["task_id"]
                f.write(json.dumps({"event": "submit", "task_id": tid, "shot": tag, "seconds": dur,
                                    "ts": time.strftime("%F %T")}, ensure_ascii=False) + "\n")
        if not ok:
            return tag, f"SUBMIT_FAIL {json.dumps(d, ensure_ascii=False)[:300]}"
        state = {"task_id": tid, "shot": tag, "take": take, "duration": dur, "seed": seed, "images": images,
                 "ref_ids": pick_refs(shot), "prompt_source": src, "prompt": prompt, "status": "QUEUED",
                 "submitted": time.strftime("%F %T"),
                 "retries": state.get("retries", 0) + (1 if state.get("status") == "FAILED" else 0)}
        json.dump(state, open(state_f, "w"), ensure_ascii=False, indent=1)
    tid = state["task_id"]
    t0 = time.time()
    while True:
        time.sleep(15)
        try:
            d = api("GET", f"{AD['base']}/result/{tid}")
        except Exception:
            continue
        data = d.get("data") or {}
        st = str(data.get("status", "")).upper()
        if st in ("SUCCESS", "COMPLETED"):
            url = next((r["url"] for r in data.get("results", []) if r.get("type") == "video"), None)
            if not url:
                url = next((r.get("url") for r in data.get("results", []) if str(r.get("url", "")).endswith(".mp4")), None)
            raw = requests.get(url, timeout=600).content
            with open(mp4 + ".part", "wb") as f:
                f.write(raw)
            os.replace(mp4 + ".part", mp4)
            state.update(status="SUCCESS", cost=data.get("cost"), gen_seconds=data.get("duration"),
                         finished=data.get("finished_at"), video=os.path.relpath(mp4, ROOT), result_meta={
                             k: v for k, v in data.items() if k not in ("results",)})
            json.dump(state, open(state_f, "w"), ensure_ascii=False, indent=1)
            ledger_add({"task_id": tid, "shot": tag, "seconds": state["duration"], "cost": data.get("cost"),
                        "status": "SUCCESS", "ts": time.strftime("%F %T")})
            return tag, f"ok cost={data.get('cost')} gen={data.get('duration')}s"
        if st in ("FAILED", "FAIL", "ERROR", "CANCELLED"):
            state.update(status="FAILED", error=json.dumps(d, ensure_ascii=False)[:600], cost=data.get("cost"))
            json.dump(state, open(state_f, "w"), ensure_ascii=False, indent=1)
            ledger_add({"task_id": tid, "shot": tag, "seconds": state["duration"], "cost": data.get("cost") or 0,
                        "status": "FAILED", "ts": time.strftime("%F %T")})
            return tag, f"FAILED {d.get('msg')} {json.dumps(data, ensure_ascii=False)[:200]}"
        if time.time() - t0 > 3 * 3600:
            return tag, "TIMEOUT (still open, rerun to resume polling)"


def cmd_videos(a):
    ep = load_ep()
    only = a.only.split(",") if a.only else None
    shots = {s["id"]: s for s in ep["shots"]}
    order = only or [s["id"] for s in ep["shots"]]
    work = [(shots[i], t) for t in a.takes.split(",") for i in order]
    with ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(run_take, s, t, a.dry) for s, t in work]
        for f in futs:
            tag, st = f.result()
            print(time.strftime("%T"), tag, st, flush=True)
    done, pending = spent()
    print(f"spent CNY {done:.2f}, pending CNY {pending:.2f}, budget CNY {AD['budget_cny']}", flush=True)


def cmd_status(a):
    done, pending = spent()
    print(f"spent CNY {done:.2f}, pending (worst case) CNY {pending:.2f}, budget CNY {AD['budget_cny']}, "
          f"assumed price {AD['price_per_sec']}/s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("frames"); p.add_argument("--workers", type=int, default=8)
    p.add_argument("--only", default=""); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_frames)
    p = sub.add_parser("ir"); p.add_argument("--workers", type=int, default=4)
    p.add_argument("--only", default=""); p.add_argument("--force", action="store_true"); p.set_defaults(fn=cmd_ir)
    p = sub.add_parser("videos"); p.add_argument("--takes", default="a")
    p.add_argument("--workers", type=int, default=8); p.add_argument("--only", default="")
    p.add_argument("--dry", action="store_true"); p.set_defaults(fn=cmd_videos)
    p = sub.add_parser("status"); p.set_defaults(fn=cmd_status)
    a = ap.parse_args()
    a.fn(a)
