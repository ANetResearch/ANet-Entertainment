#!/bin/bash
# Full production driver.  usage: run_all.sh frames | videos <takes> [workers]
cd "$(dirname "$0")/.." || exit 1
PY=.venv/bin/python
case "$1" in
 frames)
  for ep in 1 2 3 4 5 6 7 8 9 10 11 12; do
    $PY tools/pipeline.py frames $ep --workers 16
    touch episodes/$(printf 'ep%02d' $ep)/.frames_done
  done ;;
 videos)
  for ep in ${EPS:-1 2 3 4 5 6 7 8 9 10 11 12}; do
    d=episodes/$(printf 'ep%02d' $ep)
    until [ -f $d/.frames_done ]; do $PY -c "import time; time.sleep(20)"; done
    $PY tools/pipeline.py videos $ep --takes "$2" --workers "${3:-20}"
  done ;;
esac
