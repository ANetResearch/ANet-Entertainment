#!/usr/bin/env python3
"""Speech timing of the chosen takes, for trimming: a Gemini flash model lists every spoken phrase with start and end
seconds; the result is snapped to the speech-band energy of the clip. usage: speech_times.py work/picks.json
-> work/speech_times.json"""
import base64, json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg as _cfg
ROOT = _cfg.ROOT
G = _cfg.load()["gravitex"]
Q = ('This is a {dur:.2f}-second audio clip. List every spoken phrase (Mandarin Chinese) with precise start and end '
     'times in seconds measured from the beginning of the clip. Reply JSON only: {{"phrases": [{{"text": "...", '
     '"start": 0.0, "end": 0.0}}]}}. Empty list if nobody speaks.')


def ask(mp4, dur):
    audio = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", mp4, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "64k",
                            "-f", "mp3", "-"], capture_output=True).stdout
    body = {"model": "gemini-3.8-flash", "messages": [{"role": "user", "content": [{"type": "text", "text": Q.format(dur=dur)},
            {"type": "input_audio", "input_audio": {"data": base64.b64encode(audio).decode(), "format": "mp3"}}]}]}
    for i in range(4):
        try:
            r = requests.post(G["url"] + "/v1/chat/completions", headers={"Authorization": "Bearer " + G["key"]}, json=body, timeout=90)
            return json.loads(re.search(r"\{.*\}", r.json()["choices"][0]["message"]["content"], re.S).group(0))["phrases"]
        except Exception:
            time.sleep(2 + i)
    return None


def main():
    picks = json.load(open(sys.argv[1]))
    script = {s["id"]: s for s in json.load(open(f"{ROOT}/series/sp01.json"))["shots"]}
    out_f = f"{ROOT}/work/speech_times.json"
    res = json.load(open(out_f)) if os.path.exists(out_f) else {}
    todo = [f"{s}_{t}" for s, t in picks.items() if script[s]["dialogue"] and f"{s}_{t}" not in res]

    def one(k):
        p = f"{ROOT}/episodes/sp01/video/{k}.mp4"
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                   capture_output=True, text=True).stdout)
        return k, ask(p, dur)
    with ThreadPoolExecutor(6) as ex:
        for k, ph in ex.map(one, todo):
            res[k] = ph
            print(k, ph, flush=True)
    json.dump(res, open(out_f, "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
