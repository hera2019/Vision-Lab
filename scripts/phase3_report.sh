#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
scripts/drun.sh vision-lab:pytools -- python /work/python/report_phase3.py
