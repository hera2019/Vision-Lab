#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p results/phase-5 data/phase-5/crops
VL_RW="results data/phase-5" scripts/drun.sh vision-lab:phase4-pytools --cpus=4 -- \
  python /work/python/phase5_failures.py
