#!/bin/bash
# Plain one-shot baseline on both held-out corpora; retries hourly after quota stops.
cd /mnt/data/college/research/SafeMAP
W=/mnt/data/college/research/safemap_v2_heldout
set -a; . ./.env; set +a
unset SAFEMAP_MODEL SAFEMAP_BASE_URL
for pair in "resubmission_heldout plain-orig" "resubmission_heldout_ext plain-ext"; do
  set -- $pair
  until python3 scripts/run_plain_llm_baseline.py external_corpus/$1 $W/$2 >> $W/$2.log 2>&1; do
    echo "$(date -Is) $2: failed, retrying in 1h" >> $W/run.log; sleep 3600
  done
  echo "$(date -Is) $2: complete" >> $W/run.log
done
