#!/usr/bin/env python3
"""Turn each scripted shot into the English fields of the client's H3 prompt template.
usage: make_tpl.py EP [EP ...] [--workers 8] [--force]   (adds shot["tpl"] in series/epNN.json)"""
import json, os, re, sys, time, threading
from concurrent.futures import ThreadPoolExecutor
import requests
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "tools", "config.json")))["gravitex"]
MODELS = ("claude-sonnet-5-5", "claude-opus-5-5", "gpt-6.2-sol")
SYS = """You convert one shot of a documentary-style sci-fi series into English fields for a video-generation prompt template. The clip is a single continuous shot (no cuts). Characters: Amu (male engineer, protagonist), Boye (old mentor), Xiaoman (young apprentice), Boss Jin (convoy boss), Governor Xing (female city governor), Researcher Zhou (female researcher), Luosi (small yellow tracked robot with a smiley screen face, never speaks), MOSS (AI terminal with a red lens, speaks from a loudspeaker).
You receive: shot type, duration in seconds, the English storyboard frame description, the Chinese description of camera/action/ambient sound, and the dialogue lines.
Return JSON only with these string fields:
- "summary": one sentence: what happens in this clip, where, and (if there is dialogue) which line it opens with and which line it ends on.
- "blocking": one sentence "Blocking lock: ..." fixing who/what is at frame left / centre / right / foreground / background, consistent with the storyboard frame.
- "camera": shot size + camera behaviour, e.g. "medium close-up, locked-off interview camera" or "wide shot, handheld follow with a faint shake" or "extreme close-up, slow push-in".
- "start", "middle", "end": the action at the beginning, middle and end of the clip, concrete and physical, one main action only, faithful to the Chinese description. Never describe anyone speaking words here.
- "mood": 2-3 adjectives.
- "blur": one phrase on depth of field / what is out of focus.
- "soundscape": the diegetic ambient sounds only (from the 环境声 part), comma separated. No music.
Rules: English only. Do not add subtitles, text, music, new characters or events. Do not include any dialogue text or quotation marks in any field except "summary" (where lines may be quoted in Chinese). Keep each field under 45 words."""
lock = threading.Lock()

def convert(shot):
    user = json.dumps({"type": shot["type"], "duration": shot["dur"], "frame": shot["frame"], "video_zh": shot["video"],
                       "dialogue": shot["dialogue"]}, ensure_ascii=False)
    for i, model in enumerate(MODELS * 2):
        try:
            r = requests.post(CFG["url"] + "/v1/chat/completions", headers={"Authorization": "Bearer " + CFG["key"]}, timeout=120,
                              json={"model": model, "max_tokens": 1200, "messages": [{"role": "system", "content": SYS}, {"role": "user", "content": user}]})
            txt = r.json()["choices"][0]["message"]["content"]
            d = json.loads(re.search(r"\{.*\}", txt, re.S).group(0))
            if all(isinstance(d.get(k), str) and d[k] for k in ("summary", "blocking", "camera", "start", "middle", "end", "mood", "blur", "soundscape")):
                return d
        except Exception:
            time.sleep(2 + 2 * i)
    return None

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 8
    if "--workers" in sys.argv: args.remove(str(workers))
    for ep in args:
        f = f"{ROOT}/series/ep{int(ep):02d}.json"
        d = json.load(open(f))
        todo = [s for s in d["shots"] if "--force" in sys.argv or "tpl" not in s]
        def one(s):
            t = convert(s)
            if t:
                with lock:
                    s["tpl"] = t
                    json.dump(d, open(f, "w"), ensure_ascii=False, indent=1)
            return s["id"], bool(t)
        with ThreadPoolExecutor(workers) as ex:
            bad = [sid for sid, ok in ex.map(one, todo) if not ok]
        print(f"ep{int(ep):02d}: {len(todo)-len(bad)} converted, failed: {bad}", flush=True)
if __name__ == "__main__":
    main()
