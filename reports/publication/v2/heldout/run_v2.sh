#!/bin/bash
# Runs the frozen v2 evaluation: held-out stages, then ablations on the v1 corpus.
cd /mnt/data/college/research/SafeMAP || exit 1
set -a; . ./.env; set +a
unset SAFEMAP_MODEL SAFEMAP_BASE_URL
export SAFEMAP_C2RUST_DOCKER_IMAGE=safemap-c2rust:0.22.1-llvm14
W=/mnt/data/college/research/safemap_v2_heldout
R="python3 scripts/run_conference_heldout.py --work-root $W --config research/resubmission_evaluation.yaml --freeze-record research/implementation_freeze_v2.json"
step() { # stage corpus
  if [ -f "$W/$1/stage_manifest.json" ]; then echo "$(date -Is) $1: already complete"; return 0; fi
  resume=""; [ -d "$W/$1" ] && resume="--resume"
  echo "$(date -Is) $1: start $resume"
  $R --corpus "$2" run --stage "$1" $resume || { echo "$(date -Is) $1: FAILED"; exit 1; }
  echo "$(date -Is) $1: complete"
}
step v2-non-llm external_corpus/resubmission_heldout
step v2-llm external_corpus/resubmission_heldout
step v2-ablation external_corpus/conference_heldout
echo "$(date -Is) ALL DONE"
