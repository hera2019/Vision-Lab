#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/phase-4/tracks
for model in nano tiny; do
  mkdir -p "data/phase-4/tracks/$model"
  for sequence in data/MOT20/train/MOT20-*; do
    name=$(basename "$sequence")
    VL_RW="results data/phase-4" scripts/drun.sh vision-lab:phase4 --cpus=4 -- \
      /src/build/track_sequence --sequence "/work/$sequence" \
      --model "/work/data/phase-4/models/bytetrack_${model}_mot17.int8.onnx" \
      --threads 4 --out "/work/data/phase-4/tracks/$model/$name.txt"
  done
done
VL_RW="results data/phase-4" scripts/drun.sh vision-lab:phase4-pytools -- \
  python /work/python/evaluate_phase4.py
