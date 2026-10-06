#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/continuity-pilot
VL_RW="results data/continuity-pilot" scripts/drun.sh vision-lab:pytools -- \
  python /work/python/continuity_pilot.py
