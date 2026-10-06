#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/phase-3/demos
for name in MOT17-02-FRCNN MOT17-05-FRCNN MOT20-03; do
  if [[ $name == MOT17* ]]; then benchmark=MOT17; else benchmark=MOT20; fi
  VL_RW="results data/phase-3" scripts/drun.sh vision-lab:pytools -- \
    python /work/python/render_tracking_demo.py --sequence "/work/data/$benchmark/train/$name" \
    --tracks "/work/data/phase-3/tracks/end-to-end/nano/$name.txt" --model nano \
    --out "/work/data/phase-3/demos/$name-nano.mp4"
  VL_RW="results data/phase-3" scripts/drun.sh vision-lab:dev -- \
    /src/build/transcode_demo "/work/data/phase-3/demos/$name-nano.mp4" "/work/data/phase-3/demos/$name-nano.h264.mp4"
  VL_RW="results data/phase-3" scripts/drun.sh vision-lab:pytools -- \
    python /work/python/finalize_demo_encoding.py --video "/work/data/phase-3/demos/$name-nano.mp4"
done
