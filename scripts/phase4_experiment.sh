#!/usr/bin/env bash
# Requires the documented local images and licensed baseline models/datasets.
# No download/build/network access; sequential measurements preserve CPU budgets.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
bash scripts/phase4_quantize.sh
bash scripts/phase4_int8_threads.sh
bash scripts/phase4_benchmark.sh paired
bash scripts/phase4_accuracy.sh
scripts/drun.sh vision-lab:phase4-pytools -- python /work/python/report_phase4.py
