#!/usr/bin/env python3
"""Print the AutoDL status of open sp01 tasks (no secrets printed). usage: task_status.py [KEY ...]"""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfg as _cfg, requests
ROOT = _cfg.ROOT; AD = _cfg.load()["autodl"]
keys = sys.argv[1:] or [os.path.basename(f)[:-5] for f in sorted(glob.glob(f"{ROOT}/episodes/sp01/tasks/*.json"))]
for k in keys:
    st = json.load(open(f"{ROOT}/episodes/sp01/tasks/{k}.json"))
    if st.get("status") == "SUCCESS":
        print(k, "SUCCESS", st.get("cost")); continue
    d = requests.get(f"{AD['base']}/result/{st['task_id']}", headers={"Authorization": AD["token"]}, timeout=60).json().get("data") or {}
    print(k, d.get("status"), "dur", d.get("duration"), "created", d.get("created_at"), "started", d.get("started_at"), "cost", d.get("cost"))
