#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/phase-5-meanshift results/phase-5-meanshift
image=vision-lab:phase4-pytools
run() {
  VL_RW='results data/phase-5-meanshift' scripts/drun.sh "$image" --cpus=1 -- \
    python -B /work/python/meanshift_baseline.py "$@"
}
run preflight
run verify-evaluator
for sequence in data/MOT20/train/MOT20-*; do
  run track --sequence "/work/$sequence"
done
for repeat in 1 2 3; do
  run benchmark --sequence /work/data/MOT17/train/MOT17-02-FRCNN --repeat "$repeat"
done
run evaluate
VL_RW=results scripts/drun.sh "$image" -- \
  python -B /work/python/report_meanshift.py
VL_RW=results scripts/drun.sh "$image" -- \
  python -B /work/python/verify_meanshift.py
