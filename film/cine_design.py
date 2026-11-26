#!/usr/bin/env python3
"""Cinematography pass for the short film: redesign every shot of series/ep13.json (story, dialogue, duration unchanged)
into a designed film shot -> series/ep14.json.  One LLM call per act so the shots of a scene are designed together.
usage: cine_design.py [--force]"""
import json, os, re, sys, time, requests
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GX = json.load(open(f"{ROOT}/tools/config.json"))["gravitex"]
MODELS = ("claude-opus-5-5", "claude-sonnet-5-5")

BIBLE = """You are the director of photography of a 12-minute science-fiction short film 《未熄》 (a fan side-story in the world of The Wandering Earth) aiming at festival / Academy level craft.
The previous version was shot as a loose mockumentary and looked like TV footage: no shot design. Redesign every shot as CINEMA. Story, dialogue, characters, props and duration of each shot are fixed; you design the IMAGE and the CAMERA.

VISUAL BIBLE
- Camera & texture: ARRI ALEXA 65 with anamorphic lenses, Kodak Vision3 500T film-out, fine heavy grain, pure deep blacks, natural skin. Final frame is cropped to 2.39:1, so compose in a wide horizontal band, faces never near the top or bottom edge.
- Light (Roger Deakins): colour comes from the light source. Motivated practicals only (tungsten work lamps, sodium tunnel lights, red MOSS lens glow, blue-white engine plasma, orange Jupiter light, small green/red node LEDs). Volumetric haze, steam and ice dust catch the beams. Use silhouettes and backlight boldly; let blacks fall.
- Scale (Denis Villeneuve / megastructure aesthetics): few colours, layered luminance, monumental scale. Whenever the engine, the shaft city, the ice plain or Jupiter is in frame, put tiny human figures or a tiny vehicle against the colossal form.
- Order vs. warmth (Kubrick): MOSS and the command hall are photographed in rigid one-point symmetry, wide lens, cold, locked-off or dead-straight slow push. Humans and the little robot are photographed warm, close, slightly asymmetric, with shallow focus and foreground objects.
- Palette by act: Prologue = near-black with one warm lamp. Act 1 (isolation) = cold cyan-grey concrete with small islands of warm tungsten. Act 2 (crushing) = Jupiter's orange-red floods everything, then total darkness, then tiny green/warm points returning. Act 3 (saturation) = blue-white ice and plasma against orange sky, sparks, breath vapour. Act 4 (ignition) = everything bleaches toward white. Coda = soft warm light, first calm.
- The interviews (2078) are the only documentary element, shot like a prestige feature documentary: 85mm, subject off-centre with deep negative space, one soft side key, background falling to darkness, an almost imperceptible slow push-in. Vary side and size between interviewees; keep each interviewee's own setup consistent.
- Three motifs must be designed to rhyme visually across the film: (1) a human hand and the robot's claw touching - always the same tight profile two-shot of hand and claw, backlit; (2) lights going out / coming back - always seen as small points in a large dark frame; (3) the paper receipt tape - always macro, shallow focus, warm backlight through the paper.

SHOT GRAMMAR (every shot gets exactly ONE motivated camera idea)
Choose from: slow dolly push-in (emotion tightening); slow pull-back reveal (isolation / scale); lateral tracking with foreground parallax (pipes, railings, people passing); low-angle Steadicam follow from behind or leading from the front; slow crane/jib rise or descent revealing scale; locked-off symmetric tableau; slow arc/orbit around a still subject; rack focus between two depth planes; tilt up from a detail to a face or to the sky; handheld close and breathing (only for panic, collapse, running - used sparingly so it means something); top-down overhead; macro on a slider.
- State lens (e.g. 27mm, 40mm, 65mm, 85mm, 100mm macro), camera height/angle, shot size, and the composition at the START and at the END of the move, so the move has a destination.
- Always give depth: something in the foreground (out of focus), the subject, and a readable background.
- Within a scene vary shot size with intent (wide -> medium -> close) and do not repeat the same move on consecutive shots. Cut on motion or on a look so adjacent shots join.
- Action must be simple enough to read in the shot's duration: one main action per shot, clearly staged, described as a beginning, a middle and an end.
- Dialogue shots: frame so the speaker's mouth is visible and the camera move is gentle; the listener may be a soft foreground shoulder.
- Nothing may be added to the story: no new characters, no new events, no on-screen text. Keep the robot, logos and props as given.

OUTPUT
Return ONLY a JSON array, one object per input shot, same order, each with:
{"id": "sNN",
 "design": "一句中文：景别/焦段/机位/运镜/光线的设计意图",
 "frame": "English. The OPENING FRAME of the shot as a still: shot size, lens, camera height and angle, composition (what is foreground / subject / background and where in frame), who and what is visible with their look and pose, light sources and colour, atmosphere. 60-110 words. No style buzzwords, no camera brand names, no text in image.",
 "tpl": {
   "summary": "English, one sentence: what happens in this shot (and who speaks, if anyone).",
   "blocking": "English: 'Blocking lock: ...' positions of subjects in frame and what must stay consistent.",
   "camera": "English: shot size, lens, angle and the ONE camera move with its speed and its start and end framing.",
   "start": "English: what we see and what happens in the first third.",
   "middle": "English: the middle third.",
   "end": "English: the last third and the final composition the camera lands on.",
   "mood": "English, 3-5 words.",
   "blur": "English: focus design - what is sharp, depth of field, any rack focus; the main subject is always crisp.",
   "soundscape": "English: location sound only (no music)."}}"""


def call(payload):
    for i, model in enumerate(MODELS * 3):
        try:
            r = requests.post(GX["url"] + "/v1/chat/completions", headers={"Authorization": "Bearer " + GX["key"]}, timeout=900,
                              json={"model": model, "max_tokens": 32000, "messages": [{"role": "system", "content": BIBLE},
                                    {"role": "user", "content": payload}]})
            txt = r.json()["choices"][0]["message"]["content"]
            return json.loads(re.search(r"\[.*\]", txt, re.S).group(0))
        except Exception as e:
            print("retry", model, str(e)[:120], flush=True); time.sleep(5 + 5 * i)
    return None


def main():
    src = json.load(open(f"{ROOT}/series/ep13.json"))
    outf = f"{ROOT}/series/ep14.json"
    out = json.load(open(outf)) if os.path.exists(outf) and "--force" not in sys.argv else json.loads(json.dumps(src))
    out["episode"] = 14; out["title"] = "未熄（电影版）"
    refs = json.load(open(f"{ROOT}/refs/refs.json"))
    acts = []
    for s in src["shots"]:
        if not acts or acts[-1][0] != s["act"]: acts.append((s["act"], []))
        acts[-1][1].append(s)
    # split long acts in two so each call stays focused
    chunks = []
    for name, shots in acts:
        if len(shots) > 14:
            h = len(shots) // 2; chunks += [(name + " (first half)", shots[:h]), (name + " (second half)", shots[h:])]
        else: chunks.append((name, shots))
    done = {s["id"] for s in out["shots"] if s.get("_cine")}

    def one(chunk):
        name, shots = chunk
        if all(s["id"] in done for s in shots): return name, "cached"
        items = [{"id": s["id"], "duration_s": s["dur"], "kind": s["type"], "what_happens_zh": s["video"], "dialogue": s.get("dialogue") or [],
                  "old_frame": s["frame"], "available_refs": {r: refs[r]["en"][:160] for r in s["refs"] if r in refs}} for s in shots]
        res = call(f"Act: {name}\nThe whole film in order, for context: " + " | ".join(f"{s['id']}:{s['video'][:28]}" for s in src["shots"]) +
                   "\n\nDesign these shots:\n" + json.dumps(items, ensure_ascii=False, indent=1))
        if not res or [r["id"] for r in res] != [s["id"] for s in shots]: return name, "FAIL"
        by = {s["id"]: s for s in out["shots"]}
        for r in res:
            t = by[r["id"]]; t["frame"] = r["frame"]; t["tpl"] = r["tpl"]; t["design"] = r["design"]; t["_cine"] = True
        return name, "ok"

    with ThreadPoolExecutor(4) as ex:
        for r in ex.map(one, chunks):
            print(*r, flush=True)
            json.dump(out, open(outf, "w"), ensure_ascii=False, indent=1)
    json.dump(out, open(outf, "w"), ensure_ascii=False, indent=1)
    print("designed", sum(1 for s in out["shots"] if s.get("_cine")), "/", len(out["shots"]))


if __name__ == "__main__":
    main()
