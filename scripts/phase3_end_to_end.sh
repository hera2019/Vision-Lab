#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
threads=${1:-1}
mkdir -p data/phase-3
for model in nano tiny; do
  for sequence in data/MOT17/train/*-FRCNN data/MOT20/train/MOT20-*; do
    name=$(basename "$sequence")
    VL_RW="results data/phase-3" scripts/drun.sh vision-lab:dev -- \
      /src/build/track_sequence --model "/work/models/bytetrack_${model}_mot17.onnx" \
      --sequence "/work/$sequence" --threads "$threads" \
      --out "/work/data/phase-3/tracks/end-to-end/$model/$name.txt"
  done
done
