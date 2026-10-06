#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/phase-3/determinism results/phase-3
for model in nano tiny; do
  for threads in 1 4; do
    VL_RW="results data/phase-3" scripts/drun.sh vision-lab:dev -- \
      /src/build/detect_sequence --model "/work/models/bytetrack_${model}_mot17.onnx" \
      --sequence /work/data/MOT17/train/MOT17-02-FRCNN --limit 50 --threads "$threads" \
      --out "/work/data/phase-3/determinism/$model-$threads.txt"
  done
done
VL_RW="results data/phase-3" scripts/drun.sh vision-lab:pytools -- \
  python /work/python/check_thread_determinism.py
