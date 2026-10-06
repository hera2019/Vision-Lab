#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/phase-3 results/phase-3
VL_RW="results data/phase-3" scripts/drun.sh vision-lab:pytools -- \
  python /work/python/evaluate_tracking.py --stage "${1:-final}" "${@:2}"
