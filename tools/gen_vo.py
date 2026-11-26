#!/usr/bin/env python3
"""Narration for the short film via AutoDL indextts2: every `vo` line of series/<EP>.json -> film/vo/<shot>.wav
Voice is cloned from film/vo/_voice_ref.wav.  usage: gen_vo.py [EP=ep13] [--force]"""
import json, requests, base64, os, sys, time
from concurrent.futures import ThreadPoolExecutor
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AD = json.load(open(f"{ROOT}/tools/config.json"))["autodl"]
H = {"Authorization": AD["token"], "Content-Type": "application/json"}
BASE = AD["base"]
EP = next((a for a in sys.argv[1:] if a.startswith("ep")), "ep13")
REF = "data:audio/wav;base64," + base64.b64encode(open(f"{ROOT}/film/vo/_voice_ref.wav", "rb").read()).decode()


def tts(text, out):
    body = {"prompt_text": text, "prompt_simple": REF, "emo_control_method": "使用情感向量控制", "emo_calm": 0.7, "emo_melancholic": 0.35,
            "emo_sad": 0, "emo_happy": 0, "emo_angry": 0, "emo_afraid": 0, "emo_disgusted": 0, "emo_surprised": 0, "emo_random": False}
    r = requests.post(f"{BASE}/indextts2-v1", headers=H, data=json.dumps(body), timeout=120).json()
    if r.get("code") != "Success": return "submit: " + json.dumps(r, ensure_ascii=False)[:300]
    tid = r["data"]["task_id"]
    for _ in range(120):
        time.sleep(5)
        d = requests.get(f"{BASE}/result/{tid}", headers=H, timeout=60).json().get("data", {})
        st = str(d.get("status", "")).upper()
        if st in ("SUCCESS", "COMPLETED"):
            open(out, "wb").write(requests.get(d["results"][0]["url"], timeout=300).content)
            with open(f"{ROOT}/ledger/tts.jsonl", "a") as f: f.write(json.dumps({"out": out, "task": tid, "cost": d.get("cost")}, ensure_ascii=False) + "\n")
            return f"ok cost={d.get('cost')}"
        if st == "FAILED": return "failed: " + json.dumps(d, ensure_ascii=False)[:300]
    return "timeout"


def main():
    vo = [(s["id"], s["vo"]) for s in json.load(open(f"{ROOT}/series/{EP}.json"))["shots"] if s.get("vo")]
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    todo = [(i, t) for i, t in vo if (not only or i in only) and ("--force" in sys.argv or not os.path.exists(f"{ROOT}/film/vo/{EP}_{i}.wav"))]
    with ThreadPoolExecutor(6) as ex:
        for (i, t), r in zip(todo, ex.map(lambda a: tts(a[1], f"{ROOT}/film/vo/{EP}_{a[0]}.wav"), todo)):
            print(i, r, flush=True)


if __name__ == "__main__":
    main()
