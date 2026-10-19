#!/bin/bash
# Full system on the v1 libraries with the frozen code: the ablation baseline row.
W=/mnt/data/college/research/safemap_v2_heldout
while pgrep -f run_v2b.sh >/dev/null; do sleep 60; done
cd /mnt/data/college/research/SafeMAP || exit 1
set -a; . ./.env; set +a; unset SAFEMAP_MODEL SAFEMAP_BASE_URL
[ "$(git rev-parse HEAD)" = "$(python3 -c "import json;print(json.load(open('research/implementation_freeze_v2.json'))['git_commit'])")" ] || { echo "$(date -Is) ablation-full: HEAD differs from freeze"; exit 1; }
echo "$(date -Is) ablation-full: start"
until python3 -m safemap.cli final-eval --benchmarks external_corpus/conference_heldout/projects \
    --output $W/ablation-full --config research/resubmission_evaluation.yaml --mode safemap_guided; do
  echo "$(date -Is) ablation-full: failed (likely quota); retrying in 1 h"; sleep 3600; done
echo "$(date -Is) ablation-full: complete"
