#!/usr/bin/env python3
"""Batch image generation on gravitex (gpt-image-2.6-sunburst).

usage: gen_image.py jobs.json [--workers 6] [--only id1,id2] [--force]

jobs.json: [{"id": ..., "out": "path/to.png", "prompt": "...",
             "inputs": ["optional/ref.png", ...], "size": "1536x1024"}]
With "inputs" the /v1/images/edits endpoint is used (reference-conditioned).
Every output gets a sidecar <out>.json holding the exact prompt + inputs used.
"""
import argparse, base64, json, os, sys, time, threading
from concurrent.futures import ThreadPoolExecutor
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, "tools", "config.json")))
URL = CFG["gravitex"]["url"].rstrip("/")
KEY = CFG["gravitex"]["key"]
MODEL = CFG["gravitex"]["image_model"]
LOG = os.path.join(ROOT, "ledger", "images.jsonl")
lock = threading.Lock()


def log(rec):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with lock, open(LOG, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def run(job, force=False):
    out = os.path.join(ROOT, job["out"])
    if os.path.exists(out) and not force:
        return job["id"], "skip"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    size = job.get("size", "1536x1024")
    inputs = job.get("inputs") or []
    err = None
    for attempt in range(4):
        t0 = time.time()
        try:
            if inputs:
                files = []
                for p in inputs:
                    ap = os.path.join(ROOT, p)
                    mime = "image/png" if ap.endswith(".png") else "image/jpeg"
                    files.append(("image[]", (os.path.basename(ap), open(ap, "rb"), mime)))
                r = requests.post(URL + "/v1/images/edits", headers={"Authorization": "Bearer " + KEY},
                                  data={"model": MODEL, "prompt": job["prompt"], "size": size, "n": "1"},
                                  files=files, timeout=600)
            else:
                r = requests.post(URL + "/v1/images/generations", headers={"Authorization": "Bearer " + KEY},
                                  json={"model": MODEL, "prompt": job["prompt"], "size": size, "n": 1}, timeout=600)
            if r.status_code != 200:
                err = f"{r.status_code} {r.text[:300]}"
                if r.status_code == 400 and "moderation" in r.text.lower():
                    break
                time.sleep(5 + 10 * attempt)
                continue
            d = r.json()
            item = d["data"][0]
            if item.get("b64_json"):
                raw = base64.b64decode(item["b64_json"])
            else:
                raw = requests.get(item["url"], timeout=300).content
            with open(out, "wb") as f:
                f.write(raw)
            meta = {"id": job["id"], "out": job["out"], "model": MODEL, "size": size, "prompt": job["prompt"],
                    "inputs": inputs, "usage": d.get("usage"), "seconds": round(time.time() - t0, 1),
                    "ts": time.strftime("%F %T")}
            json.dump(meta, open(out + ".json", "w"), ensure_ascii=False, indent=1)
            log(meta)
            return job["id"], "ok"
        except Exception as e:  # network hiccup: retry
            err = repr(e)[:300]
            time.sleep(5 + 10 * attempt)
    log({"id": job["id"], "out": job["out"], "error": err, "ts": time.strftime("%F %T")})
    return job["id"], "FAIL " + str(err)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--only", default="")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    jobs = json.load(open(a.jobs))
    if a.only:
        keep = set(a.only.split(","))
        jobs = [j for j in jobs if j["id"] in keep]
    with ThreadPoolExecutor(a.workers) as ex:
        for jid, st in ex.map(lambda j: run(j, a.force), jobs):
            print(time.strftime("%T"), jid, st, flush=True)


if __name__ == "__main__":
    main()
