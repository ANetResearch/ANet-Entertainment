#!/bin/bash
# after take b + QC: re-export, push alt takes, cut 12 episodes, publish a release
cd "$(dirname "$0")/.." || exit 1
W=/tmp/claude-1001/-data-projs-anet-movie/6792670a-3d23-42c2-ab65-b5bf83ed5e53/tasks/br39e9zqi.output
until grep -q "budget" "$W" 2>/dev/null; do .venv/bin/python -c "import time; time.sleep(60)"; done
for e in 01 02 03 04 05 06 07 08 09 10 11 12; do
  .venv/bin/python tools/export_repo.py $((10#$e)) | tail -1
  tools/git_push.sh "Episode $e: second takes, re-picked clips, audio QC" episodes/ep$e
  CRF=20 PRESET=veryfast .venv/bin/python tools/edit_film.py $((10#$e)) release/ep$e.mp4 --end release/end.png
done
echo ALLDONE
