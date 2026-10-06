#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/phase-4/determinism
for model in nano tiny; do
  for threads in 1 4; do
    VL_RW="results data/phase-4" scripts/drun.sh vision-lab:phase4 --cpus="$threads" -- \
      /src/build/detect_sequence --sequence /work/data/MOT17/train/MOT17-02-FRCNN \
      --model "/work/data/phase-4/models/bytetrack_${model}_mot17.int8.onnx" \
      --threads "$threads" --limit 50 --out "/work/data/phase-4/determinism/$model-t$threads.txt"
  done
done
scripts/drun.sh vision-lab:phase4-pytools -- python /work/python/check_int8_threads.py
