#!/usr/bin/env python3
"""Narration for the short film: TTS every `vo` line of series/ep13.json -> film/vo/<shot>.wav (gravitex gemini TTS, flaky channel -> long retries)."""
import json, requests, base64, os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
c = json.load(open(f"{ROOT}/tools/config.json"))["gravitex"]
vo = [(s["id"], s["vo"]) for s in json.load(open(f"{ROOT}/series/ep13.json"))["shots"] if s.get("vo")]
os.makedirs(f"{ROOT}/film/vo", exist_ok=True)
for rnd in range(40):
    todo = [(i, t) for i, t in vo if not os.path.exists(f"{ROOT}/film/vo/{i}.wav")]
    if not todo: break
    for sid, txt in todo:
        body = {"contents": [{"parts": [{"text": "用低沉、克制、平静的纪录片旁白语气，语速偏慢地读：" + txt}]}],
                "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Charon"}}}}}
        try:
            r = requests.post(c["url"] + "/v1beta/models/gemini-3.8-flash-tts:generateContent", headers={"Authorization": "Bearer " + c["key"]}, json=body, timeout=180)
            p = r.json()["candidates"][0]["content"]["parts"][0]["inlineData"]
            open(f"{ROOT}/film/vo/{sid}.wav", "wb").write(base64.b64decode(p["data"])); print(sid, "ok", flush=True)
        except Exception:
            time.sleep(3)
    time.sleep(20)
print("left:", [i for i, t in vo if not os.path.exists(f"{ROOT}/film/vo/{i}.wav")], flush=True)
