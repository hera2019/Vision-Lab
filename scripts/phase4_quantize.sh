#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/phase-4/models results/phase-4
# This image must already have been built after owner download approval.
VL_RW="results data/phase-4" scripts/drun.sh vision-lab:phase4-pytools -- \
  python /work/python/quantize_phase4.py
