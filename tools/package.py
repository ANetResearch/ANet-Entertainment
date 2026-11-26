#!/usr/bin/env python3
"""Build the web package: per-episode rough cut (shots in script order) + storyboard sheet + index.html.
usage: package.py [EP ...]   -> dist/anet-weixi-zhi-wang/   (episodes with no clips are listed as pending)"""
import html, json, os, subprocess, sys, glob
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FF = os.path.join(ROOT, "tools", "ffmpeg")
DIST = os.path.join(ROOT, "dist", "anet-weixi-zhi-wang")
NAMES = {"amu": "阿牧", "boye": "波爷", "xiaoman": "小满", "jin": "金老板", "xing": "邢总督", "zhou": "周研究员", "moss": "MOSS"}

def pick(name, sid):
    """best available take: QC-clean first, then a, b, others."""
    qc_f = f"{ROOT}/episodes/{name}/qc.json"
    qc = json.load(open(qc_f)) if os.path.exists(qc_f) else {}
    takes = sorted(glob.glob(f"{ROOT}/episodes/{name}/video/{sid}_*.mp4"))
    def score(p):
        k = os.path.basename(p)[:-4]
        flags = [f for f in qc.get(k, {}).get("flags", []) if f != "music?"]
        return (len(flags), "music?" in qc.get(k, {}).get("flags", []), k)
    return min(takes, key=score) if takes else None

def build_episode(ep):
    name = f"ep{ep:02d}"
    d = json.load(open(f"{ROOT}/series/{name}.json"))
    os.makedirs(f"{DIST}/{name}", exist_ok=True)
    clips = [(s, pick(name, s["id"])) for s in d["shots"]]
    have = [(s, c) for s, c in clips if c]
    info = {"ep": ep, "name": name, "title": d["title"], "concept": d["concept"], "logline": d["logline"],
            "shots": len(clips), "done": len(have), "video": None, "sheet": None, "script": d}
    if have:
        lst = f"{DIST}/{name}/concat.txt"
        open(lst, "w").write("".join(f"file '{c}'\n" for _, c in have))
        out = f"{DIST}/{name}/{name}-roughcut.mp4"
        subprocess.run([FF, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-vf", "scale=854:-2,fps=24",
                        "-c:v", "libx264", "-crf", "29", "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "64k",
                        "-ar", "44100", "-movflags", "+faststart", out], check=True)
        os.remove(lst)
        info["video"] = f"{name}/{name}-roughcut.mp4"
        info["takes"] = {s["id"]: os.path.basename(c) for s, c in have}
    frames = [f"{ROOT}/episodes/{name}/storyboard/{s['id']}.png" for s in d["shots"]]
    frames = [f for f in frames if os.path.exists(f)]
    if frames:
        cols, w = 6, 320; h = 180
        sheet = Image.new("RGB", (cols * w, ((len(frames) + cols - 1) // cols) * h), (12, 12, 16))
        for n, f in enumerate(frames):
            im = Image.open(f).convert("RGB").resize((w - 4, h - 4)); sheet.paste(im, ((n % cols) * w + 2, (n // cols) * h + 2))
        sheet.save(f"{DIST}/{name}/{name}-storyboard.jpg", quality=82)
        info["sheet"] = f"{name}/{name}-storyboard.jpg"
    json.dump(d, open(f"{DIST}/{name}/{name}-script.json", "w"), ensure_ascii=False, indent=1)
    return info

def page(infos):
    e = html.escape
    cards = []
    for i in infos:
        rows = []
        for s in i["script"]["shots"]:
            dl = "<br>".join(f"<b>{e(NAMES.get(x['who'], x['who']))}</b>：{e(x['line'])}" for x in s["dialogue"])
            rows.append(f"<tr><td>{s['id']}</td><td>{s['dur']}s</td><td>{dl}</td><td class=vo>{e(s.get('vo',''))}</td></tr>")
        vid = (f"<video controls preload=none poster='{i['sheet'] or ''}' src='{i['video']}'></video>" if i["video"]
               else "<p class=pending>视频生成中</p>")
        state = "完整" if i["done"] == i["shots"] else f"{i['done']}/{i['shots']} 镜头"
        cards.append(f"""<section id="{i['name']}"><p class=kicker>第 {i['ep']:02d} 集 · {state}</p><h2>{e(i['title'])}</h2>
<p class=concept>{e(i['concept'])}</p><p class=desc>{e(i['logline'])}</p>{vid}
<p class=links>{f"<a href='{i['video']}' download>下载粗剪 MP4</a>" if i['video'] else ''}
{f"<a href='{i['sheet']}'>分镜总览图</a>" if i['sheet'] else ''}<a href="{i['name']}/{i['name']}-script.json">分镜脚本 JSON</a></p>
<details><summary>对白与旁白稿（供配字幕）</summary><table><tr><th>镜头</th><th>时长</th><th>现场对白</th><th>旁白建议</th></tr>{''.join(rows)}</table></details></section>""")
    nav = " ".join(f"<a href='#{i['name']}'>{i['ep']:02d} {e(i['title'])}</a>" for i in infos)
    return f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow"><title>未熄之网 · ANET 纪录片体科普短剧</title><style>
:root{{--red:#E60000;--ink:#030213;--paper:#F5F5F6;--muted:#717182;--line:#DCDCE0;--card:#FFFFFF}}
@media (prefers-color-scheme: dark){{:root{{--ink:#F5F5F6;--paper:#0B0B10;--muted:#9A9AA8;--line:#2A2A33;--card:#13131A}}}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--paper);color:var(--ink);font:15px/1.6 Roboto,"Noto Sans SC","PingFang SC","Microsoft YaHei",-apple-system,"Segoe UI",sans-serif}}
main{{max-width:960px;margin:0 auto;padding:56px 16px 72px}}
.kicker{{font-size:12px;letter-spacing:.18em;color:var(--red);font-weight:700}}
h1{{font-size:30px;line-height:1.3;margin:8px 0 10px}} h2{{font-size:22px;margin:4px 0}}
.lead,.desc{{color:var(--muted)}} .concept{{font-weight:700;margin-top:4px}}
nav{{margin-top:24px;display:flex;flex-wrap:wrap;gap:8px}} nav a{{font-size:13px;padding:4px 10px;border:1px solid var(--line);color:var(--ink);text-decoration:none}}
section{{margin-top:44px;padding-top:20px;border-top:2px solid var(--ink)}}
video{{display:block;width:100%;aspect-ratio:16/9;background:#000;margin-top:14px}}
.pending{{margin-top:14px;padding:28px;border:1px dashed var(--line);color:var(--muted);text-align:center}}
.links{{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}} .links a{{font-size:13px;font-weight:700;padding:6px 12px;border:1px solid var(--line);color:var(--ink);text-decoration:none}}
.links a:first-child{{background:var(--red);border-color:var(--red);color:#fff}}
details{{margin-top:12px}} summary{{cursor:pointer;color:var(--muted);font-size:13px}}
.tw{{overflow-x:auto}} table{{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}} td,th{{text-align:left;vertical-align:top;padding:6px 8px;border-bottom:1px solid var(--line)}}
.vo{{color:var(--muted)}} footer{{margin-top:40px;color:var(--muted);font-size:13px}}
</style></head><body><main>
<p class=kicker>ANET · 纪录片体科普短剧</p><h1>流浪地球番外 · 未熄之网</h1>
<p class=lead>12 集粗剪样片。每集按分镜顺序拼接 AI 生成的镜头，保留现场对白与环境声，未加字幕、旁白和配乐。视频由 AutoDL 上的 MiniMax H3 生成，分镜图与参考图由 gpt-image 生成。</p>
<nav>{nav}</nav>{''.join(cards)}
<footer>设定集：<a href="bible.md">bible.md</a> · 参考图：<a href="refs-characters.jpg">人物</a> / <a href="refs-locations.jpg">场景与道具</a></footer></main></body></html>"""

def main():
    os.makedirs(DIST, exist_ok=True)
    only = [int(a) for a in sys.argv[1:]]
    cache = f"{DIST}/.infos.json"
    infos = {int(k): v for k, v in (json.load(open(cache)).items() if os.path.exists(cache) else [])}
    for ep in range(1, 13):
        if not only or ep in only or ep not in infos:
            infos[ep] = build_episode(ep); print(f"ep{ep:02d}", infos[ep]["done"], "/", infos[ep]["shots"], flush=True)
    json.dump(infos, open(cache, "w"), ensure_ascii=False)
    open(f"{DIST}/index.html", "w").write(page([infos[k] for k in sorted(infos)]))
    import shutil
    shutil.copy(f"{ROOT}/series/bible.md", f"{DIST}/bible.md")
    for a, b in (("tests/refs_sheet_chars.jpg", "refs-characters.jpg"), ("tests/refs_sheet_locs.jpg", "refs-locations.jpg")):
        if os.path.exists(f"{ROOT}/{a}"): shutil.copy(f"{ROOT}/{a}", f"{DIST}/{b}")
if __name__ == "__main__":
    main()
