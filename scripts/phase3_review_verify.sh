#!/usr/bin/env bash
# Re-run only tracker caches after F2 readability changes; preserve baseline files.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ${1:-} == --inside ]]; then
  for model in nano tiny; do
    mkdir -p "data/phase-3/review-fixes/$model"
    for sequence in data/MOT17/train/*-FRCNN data/MOT20/train/MOT20-*; do
      name=$(basename "$sequence")
      output="/work/data/phase-3/review-fixes/$model/$name.txt"
      /src/build/track_sequence --sequence "/work/$sequence" \
        --cache "/work/data/phase-3/dets/$model/$name.txt" --out "$output"
      cmp "$output" "/work/data/phase-3/tracks/cpp/$model/$name.txt"
    done
  done
  /src/build/track_sequence --sequence /work/data/phase-3/edge-cases \
    --cache /work/data/phase-3/edge-cases/dets.txt \
    --out /work/data/phase-3/review-fixes/edge-cases.txt
  cmp data/phase-3/review-fixes/edge-cases.txt data/phase-3/edge-cases/cpp.txt
else
  export PATH="$HOME/.docker/bin:$PATH"
  mkdir -p data/phase-3/review-fixes
  VL_RW="results data/phase-3/review-fixes" scripts/drun.sh vision-lab:review-fixes -- \
    bash /work/scripts/phase3_review_verify.sh --inside
  docker image inspect vision-lab:dev vision-lab:review-fixes \
    --format '{{json .RepoTags}} {{.Id}} {{.Architecture}} {{.Os}}' \
    > results/phase-3/review-fixes-image-versions.txt
  scripts/drun.sh vision-lab:pytools -- python /work/python/report_review_fixes.py
fi
