#!/usr/bin/env bash
# Track caches with both implementations; each sequence runs in a fresh process.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/phase-3
models=(nano tiny)
if [[ -n ${2:-} ]]; then
  case $2 in nano|tiny) models=("$2");; *) echo "unknown model: $2" >&2; exit 2;; esac
fi
for model in "${models[@]}"; do
  for sequence in data/MOT17/train/*-FRCNN data/MOT20/train/MOT20-*; do
    name=$(basename "$sequence")
    if [[ ${1:-} == --wait ]]; then
      frames=$(awk -F= '$1 == "seqLength" {gsub(/\r/, "", $2); print $2}' "$sequence/seqinfo.ini")
      timing="data/phase-3/dets/$model/$name.txt.timing.csv"
      while [[ ! -f $timing ]] || [[ $(wc -l < "$timing") -lt $((frames+1)) ]]; do
        sleep 5
      done
    fi
    cache="/work/data/phase-3/dets/$model/$name.txt"
    if [[ ${1:-} != --cpp-only ]]; then
      VL_RW="results data/phase-3" scripts/drun.sh vision-lab:pytools -- \
        python /work/python/track_reference.py --sequence "/work/$sequence" \
        --cache "$cache" --out "/work/data/phase-3/tracks/python/$model/$name.txt"
    fi
    VL_RW="results data/phase-3" scripts/drun.sh vision-lab:dev -- \
      /src/build/track_sequence --sequence "/work/$sequence" --cache "$cache" \
      --out "/work/data/phase-3/tracks/cpp/$model/$name.txt"
  done
done
