#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/phase-3 results/phase-3
VL_RW="results data/phase-3" scripts/drun.sh vision-lab:pytools -- \
  python /work/python/tracker_edge_cases.py --action prepare
VL_RW="results data/phase-3" scripts/drun.sh vision-lab:pytools -- \
  python /work/python/track_reference.py --sequence /work/data/phase-3/edge-cases \
  --cache /work/data/phase-3/edge-cases/dets.txt --out /work/data/phase-3/edge-cases/python.txt
VL_RW="results data/phase-3" scripts/drun.sh vision-lab:dev -- \
  /src/build/track_sequence --sequence /work/data/phase-3/edge-cases \
  --cache /work/data/phase-3/edge-cases/dets.txt --out /work/data/phase-3/edge-cases/cpp.txt
VL_RW="results data/phase-3" scripts/drun.sh vision-lab:pytools -- \
  python /work/python/tracker_edge_cases.py --action check
