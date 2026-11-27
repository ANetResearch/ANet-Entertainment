#!/usr/bin/env python3
"""A/B a second AutoDL workflow against existing takes with byte-identical inputs (prompt, seed, duration, resolution, images).
usage: ab_workflow.py WORKFLOW EP SHOT[,SHOT...] [take]   -> compare/<WORKFLOW>/<EP>_<SHOT>.mp4 + .json"""
import hashlib, json, os, sys, time, requests
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as P
wf, ep, shots = sys.argv[1], sys.argv[2], sys.argv[3].split(",")
take = sys.argv[4] if len(sys.argv) > 4 else "a"
out = f"{P.ROOT}/compare/{wf.replace('minimax_h3_', '')}"
os.makedirs(out, exist_ok=True)


def one(sid):
    src = json.load(open(f"{P.ROOT}/episodes/{ep}/tasks/{sid}_{take}.json"))
    sf, mp4 = f"{out}/{ep}_{sid}.json", f"{out}/{ep}_{sid}.mp4"
    st = json.load(open(sf)) if os.path.exists(sf) else {}
    if os.path.exists(mp4): return sid, "have"
    body = {"prompt": src["prompt"], "duration": src["duration"], "resolution": "768p横", "seed": src["seed"]}
    for i, p in enumerate(src["images"]): body[f"ref_image_{i}"] = P.data_uri(p)
    sha = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    if not st.get("task_id"):
        d = P.api("POST", f"{P.AD['base']}/{wf}", data=json.dumps(body))
        if d.get("code") != "Success": return sid, "SUBMIT_FAIL " + json.dumps(d, ensure_ascii=False)[:300]
        st = {"workflow": wf, "task_id": d["data"]["task_id"], "baseline_workflow": "minimax_h3_adl_int8", "baseline_task_id": src["task_id"],
              "baseline_video": src["video"], "shot": f"{ep}/{sid}_{take}", "duration": src["duration"], "seed": src["seed"],
              "resolution": "768p横", "images": src["images"], "prompt": src["prompt"], "request_sha256": sha, "submitted": time.strftime("%F %T")}
        json.dump(st, open(sf, "w"), ensure_ascii=False, indent=1)
        P.ledger_add({"event": "submit", "task_id": st["task_id"], "shot": f"ab/{wf}/{ep}/{sid}", "seconds": src["duration"], "ts": time.strftime("%F %T")})
    t0 = time.time()
    while time.time() - t0 < 3600:
        time.sleep(12)
        data = P.api("GET", f"{P.AD['base']}/result/{st['task_id']}").get("data") or {}
        s = str(data.get("status", "")).upper()
        if s in ("SUCCESS", "COMPLETED"):
            url = next(r["url"] for r in data["results"] if r.get("type") == "video")
            open(mp4, "wb").write(requests.get(url, timeout=600).content)
            st.update(status="SUCCESS", cost=data.get("cost"), gen_seconds=data.get("duration"), finished=data.get("finished_at"))
            json.dump(st, open(sf, "w"), ensure_ascii=False, indent=1)
            P.ledger_add({"task_id": st["task_id"], "shot": f"ab/{wf}/{ep}/{sid}", "seconds": src["duration"], "cost": data.get("cost"), "status": "SUCCESS", "ts": time.strftime("%F %T")})
            return sid, f"ok cost={data.get('cost')} gen={data.get('duration')}s"
        if s in ("FAILED", "FAIL", "ERROR", "CANCELLED"):
            tid = st.pop("task_id"); st.update(status="FAILED", error=json.dumps(data, ensure_ascii=False)[:500])
            json.dump(st, open(sf, "w"), ensure_ascii=False, indent=1)
            P.ledger_add({"task_id": tid, "shot": f"ab/{wf}/{ep}/{sid}", "seconds": src["duration"], "cost": data.get("cost") or 0, "status": "FAILED"})
            return sid, "FAILED " + json.dumps(data, ensure_ascii=False)[:300]
    return sid, "TIMEOUT"


with ThreadPoolExecutor(6) as ex:
    for r in ex.map(one, shots): print(time.strftime("%T"), *r, flush=True)
