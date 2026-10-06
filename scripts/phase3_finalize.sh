#!/usr/bin/env bash
# Final collection after all cache/reference/end-to-end steps complete.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
# Re-run C++ caches with the final corrected build; Python reference is unchanged.
./scripts/phase3_track.sh --cpp-only tiny
VL_RW="results data/phase-3" scripts/drun.sh vision-lab:pytools -- \
  python /work/python/check_score_boundaries.py
./scripts/phase3_evaluate.sh final
./scripts/phase3_report.sh
