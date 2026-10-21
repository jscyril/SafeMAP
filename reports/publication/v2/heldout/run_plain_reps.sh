#!/bin/bash
# Repeats 2 and 3 of the plain one-shot baseline (amendment 2).
cd /mnt/data/college/research/SafeMAP
W=/mnt/data/college/research/safemap_v2_heldout
set -a; . ./.env; set +a
unset SAFEMAP_MODEL SAFEMAP_BASE_URL
for i in 2 3; do
  for pair in "resubmission_heldout orig" "resubmission_heldout_ext ext"; do
    set -- $pair
    out=plain-rep$i-$2
    until python3 scripts/run_plain_llm_baseline.py external_corpus/$1 $W/$out >> $W/$out.log 2>&1; do
      echo "$(date -Is) $out: failed, retrying in 1h" >> $W/run.log; sleep 3600
    done
    echo "$(date -Is) $out: complete" >> $W/run.log
  done
done
