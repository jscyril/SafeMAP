#!/bin/bash
# Extension libraries (amendment 1), then two repeats of the LLM stage on all ten.
cd /mnt/data/college/research/SafeMAP || exit 1
set -a; . ./.env; set +a
unset SAFEMAP_MODEL SAFEMAP_BASE_URL
export SAFEMAP_C2RUST_DOCKER_IMAGE=safemap-c2rust:0.22.1-llvm14
W=/mnt/data/college/research/safemap_v2_heldout
ORIG=external_corpus/resubmission_heldout
EXT=external_corpus/resubmission_heldout_ext
step() { # work-root stage corpus
  local root=$W/$1
  if [ -f "$root/$2/stage_manifest.json" ]; then echo "$(date -Is) $1/$2: already complete"; return 0; fi
  resume=""; [ -d "$root/$2" ] && resume="--resume"
  echo "$(date -Is) $1/$2: start $resume"
  python3 scripts/run_conference_heldout.py --work-root $root --config research/resubmission_evaluation.yaml \
    --freeze-record research/implementation_freeze_v2.json --corpus "$3" run --stage "$2" $resume \
    || { echo "$(date -Is) $1/$2: FAILED"; exit 1; }
  echo "$(date -Is) $1/$2: complete"
}
step ext v2-non-llm $EXT
step ext v2-llm $EXT
for rep in rep2 rep3; do
  step $rep-orig v2-llm $ORIG
  step $rep-ext v2-llm $EXT
done
echo "$(date -Is) ALL DONE"
