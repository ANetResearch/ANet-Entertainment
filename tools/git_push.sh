#!/bin/bash
# commit + push part of repo/.  usage: GH_TOKEN=... git_push.sh "<message>" <path> [<path> ...]
cd "$(dirname "$0")/../repo" || exit 1
msg="$1"; shift
git add -- "$@" || exit 1
git diff --cached --quiet && { echo "nothing to commit for: $*"; exit 0; }
git commit -q -m "$msg" -m "Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>" || exit 1
AUTH=$(printf 'x-access-token:%s' "$GH_TOKEN" | base64 -w0)
for i in 1 2 3; do
  git -c http.extraheader="Authorization: Basic $AUTH" -c http.postBuffer=524288000 push -q origin main && { echo "pushed: $msg"; exit 0; }
  echo "push retry $i"; sleep 10
done
exit 1
