#!/usr/bin/env python3
"""Official MiniMax H3-Context-IR (hosted prompt compiler) client.

usage: ir.py compile <text_file> <duration> [image ...] [--out FILE]
Creates one task (POST /v2/h3_context_ir), polls GET /v2/query/video_generation/{id} and prints the
compiled prompt (content.prompt).  Every call is logged (no prompt text, no key) to ledger/ir.jsonl.
"""
import base64, json, os, sys, time
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg as _cfg

ROOT = _cfg.ROOT
LOG = os.path.join(ROOT, "ledger", "ir.jsonl")


def data_uri(path, max_side=1344):
    """JPEG data URI of an image (downscaled like the video pipeline)."""
    from PIL import Image
    import io
    im = Image.open(path)
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    im = im.convert("RGB")
    im.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=88)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def _task(d):
    return d.get("task") if isinstance(d.get("task"), dict) else d


def compile_prompt(text, duration, images=(), ratio="16:9", tag="", timeout=600):
    c = _cfg.load()
    base, key, model = c["minimax"]["base"], c["minimax"]["key"], c["minimax"]["model"]
    content = [{"type": "text", "text": text}]
    for p in images:
        content.append({"type": "image_url", "image_url": {"url": data_uri(p)}, "role": "reference_image"})
    body = {"model": model, "content": content, "duration": int(max(4, min(15, duration))), "ratio": ratio}
    hdr = {"Authorization": "Bearer " + key, "Content-Type": "application/json"}
    t0 = time.time()
    r = requests.post(base + "/v2/h3_context_ir", headers=hdr, data=json.dumps(body), timeout=120)
    d = r.json()
    tid = d.get("task_id") or (_task(d) or {}).get("task_id") or (d.get("data") or {}).get("task_id")
    rec = {"tag": tag, "ts": time.strftime("%F %T"), "images": len(images), "duration": body["duration"], "chars": len(text)}
    if not tid:
        rec.update(status="create_failed", http=r.status_code, base_resp=d.get("base_resp"))
        _log(rec)
        raise RuntimeError(f"IR create failed: http {r.status_code} {json.dumps(d.get('base_resp'), ensure_ascii=False)}")
    rec["task_id"] = tid
    wait = 2.0
    while time.time() - t0 < timeout:
        time.sleep(wait)
        wait = min(10.0, wait * 1.5)
        try:
            q = requests.get(base + "/v2/query/video_generation/" + tid, headers=hdr, timeout=60).json()
        except Exception:
            continue
        t = _task(q)
        st = str(t.get("status", "")).lower()
        if st in ("succeeded", "success", "completed", "finished"):
            prompt = ((t.get("content") or {}).get("prompt") or "").strip()
            rec.update(status="succeeded", seconds=round(time.time() - t0, 1), usage=t.get("usage"), out_chars=len(prompt))
            _log(rec)
            return prompt
        if st in ("failed", "fail", "cancelled", "canceled", "expired", "error"):
            rec.update(status="failed", seconds=round(time.time() - t0, 1), base_resp=q.get("base_resp"))
            _log(rec)
            raise RuntimeError("IR task failed: " + json.dumps(q.get("base_resp"), ensure_ascii=False))
    rec.update(status="timeout")
    _log(rec)
    raise RuntimeError("IR timeout")


def _log(rec):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    a = sys.argv[1:]
    out = None
    if "--out" in a:
        i = a.index("--out"); out = a[i + 1]; del a[i:i + 2]
    assert a and a[0] == "compile", __doc__
    text = open(a[1]).read()
    p = compile_prompt(text, int(a[2]), a[3:], tag=os.path.basename(a[1]))
    if out:
        open(out, "w").write(p + "\n")
    print(p)
