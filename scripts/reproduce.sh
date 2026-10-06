#!/usr/bin/env bash
# smoke = bounded check; full = the original full experiment in a clean checkout.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mode=${1:-smoke}
[[ $mode == smoke || $mode == full ]] || { echo 'Usage: bash scripts/reproduce.sh [smoke|full]' >&2; exit 2; }
free_kib=$(df -Pk . | awk 'NR==2 {print $4}')
[[ $free_kib -ge 10485760 ]] || { echo 'Less than 10 GiB free; stopping.' >&2; exit 2; }
if [[ $mode == full ]]; then
  [[ ${VL_DISPOSABLE_CLONE:-0} == 1 ]] || { echo 'Full mode writes experiment outputs; set VL_DISPOSABLE_CLONE=1 only inside a disposable clone.' >&2; exit 2; }
  git diff --quiet && git diff --cached --quiet || { echo 'Full mode requires committed source.' >&2; exit 2; }
  [[ -z $(git ls-files --others --exclude-standard) ]] || { echo 'Full mode requires all source/docs committed.' >&2; exit 2; }
  [[ -z ${VL_ASSET_ROOT:-} ]] || { echo 'Shared snapshot assets support smoke only.' >&2; exit 2; }
  mkdir -p results/phase-6 data/phase-4
  git rev-parse HEAD > results/phase-6/source-commit.txt
  git remote get-url origin > results/phase-6/source-origin.txt
  git status --porcelain --untracked-files=no > results/phase-6/source-status-before.txt
  network=${VL_BUILD_NETWORK:-none}
  [[ $network == none || $network == default ]] || { echo 'VL_BUILD_NETWORK must be none or default.' >&2; exit 2; }
  docker build --network="$network" --target build -t vision-lab:dev .
  docker build --network="$network" --target pytools -t vision-lab:pytools .
  docker build --network=none -f Dockerfile.review-fixes -t vision-lab:review-fixes .
  docker build --network=none -f Dockerfile.phase4 -t vision-lab:phase4 .
  docker build --network="$network" -f Dockerfile.phase4-pytools -t vision-lab:phase4-pytools .
fi
mkdir -p results/phase-6 data/phase-6
asset_root=${VL_ASSET_ROOT:-$PWD}
: > results/phase-6/external-revisions.txt
for label in ByteTrack TrackEval; do
  revision=$(git -C "$asset_root/external/$label" rev-parse HEAD)
  [[ -z $(git -C "$asset_root/external/$label" status --porcelain --untracked-files=no) ]] || { echo "External source changed: $label" >&2; exit 2; }
  echo "$label $revision" >> results/phase-6/external-revisions.txt
done
extra=()
if [[ -n ${VL_ASSET_ROOT:-} ]]; then
  for pair in 'models:models' 'external:external' 'data/MOT17:data/MOT17' 'data/MOT20:data/MOT20' 'data/phase-3:data/phase-3'; do
    src=${pair%%:*}; dst=${pair#*:}
    [[ -d "$VL_ASSET_ROOT/$src" ]] || { echo "Missing shared asset directory: $src" >&2; exit 2; }
    extra+=(--mount "type=bind,src=$VL_ASSET_ROOT/$src,dst=/work/$dst,readonly")
  done
fi
runpy() {
  VL_RW="results data/phase-6" scripts/drun.sh vision-lab:phase4-pytools ${extra[@]+"${extra[@]}"} -- python "$@"
}
runpy /work/python/phase6_preflight.py "$mode"
if [[ $mode == full ]]; then
  scripts/drun.sh vision-lab:dev -- /src/build/env_check > results/phase-3/environment.txt
  docker image inspect vision-lab:dev vision-lab:pytools \
    --format '{{json .RepoTags}} {{.Id}} {{.Architecture}} {{.Os}}' > results/phase-3/image-versions.txt
  scripts/drun.sh vision-lab:pytools -- pip freeze --all > results/phase-3/python-environment.txt
  scripts/drun.sh vision-lab:phase4-pytools -- pip freeze --all > results/phase-6/python-environment.txt
  cp results/phase-3-tracking.json results/phase-6/reference-phase3.json
  cp results/phase-4-performance.json results/phase-6/reference-phase4.json
  cp results/phase-3/evaluation-final.json results/phase-6/reference-evaluation.json
  scripts/drun.sh vision-lab:phase4 -- /src/build/env_check > results/phase-4/environment.json
  scripts/drun.sh vision-lab:phase4 -- sh -c 'uname -a; getconf _NPROCESSORS_ONLN; cat /sys/fs/cgroup/memory.max' > results/phase-4/hardware.txt
  docker image inspect vision-lab:phase4 vision-lab:phase4-pytools vision-lab:pytools \
    --format '{{json .RepoTags}} {{.Id}} {{.Architecture}} {{.Os}}' > results/phase-4/all-image-versions.txt
  # Original executor-only metadata must not be presented as newly run checks.
  for file in implementation-checks.json container-safety.json; do
    if [[ -f results/phase-4/$file ]]; then
      mv "results/phase-4/$file" "results/phase-6/reference-$file"
    fi
  done
  VL_RW="results data/phase-4" scripts/drun.sh vision-lab:phase4-pytools --cpus=4 -- \
    python /work/python/check_container_safety.py
  # Original reference/cache/end-to-end/evaluation steps; no new settings.
  bash scripts/phase3_determinism.sh
  bash scripts/phase3_edge_cases.sh
  bash scripts/phase3_evaluate.sh self
  bash scripts/phase3_detect.sh 4
  bash scripts/phase3_track.sh
  bash scripts/phase3_end_to_end.sh 4
  VL_RW="results data/phase-3" scripts/drun.sh vision-lab:pytools -- \
    python /work/python/check_score_boundaries.py
  bash scripts/phase3_evaluate.sh final --fresh
  bash scripts/phase4_experiment.sh
  bash scripts/phase5_failures.sh
  runpy /work/python/phase6_smoke_report.py full
  exit
fi
base=${VL_REPRO_BASE:-vision-lab:phase4}
docker image inspect "$base" --format '{{.Id}} {{.Architecture}} {{.Os}}' > results/phase-6/toolchain-image.txt
docker build --network=none --build-arg "REPRO_BASE=$base" -f Dockerfile.reproduce \
  -t vision-lab:phase6-smoke . > results/phase-6/build.log 2>&1
docker image inspect vision-lab:phase6-smoke --format '{{.Id}} {{.Architecture}} {{.Os}}' > results/phase-6/built-image.txt
VL_RW="results data/phase-6" scripts/drun.sh vision-lab:phase6-smoke ${extra[@]+"${extra[@]}"} -- \
  /src/build/env_check > results/phase-6/environment.json
runpy /work/python/track_reference.py --sequence /work/data/phase-3/edge-cases \
  --cache /work/data/phase-3/edge-cases/dets.txt --out /work/data/phase-6/edge-python.txt
VL_RW="results data/phase-6" scripts/drun.sh vision-lab:phase6-smoke ${extra[@]+"${extra[@]}"} -- \
  /src/build/track_sequence --sequence /work/data/phase-3/edge-cases \
  --cache /work/data/phase-3/edge-cases/dets.txt --out /work/data/phase-6/edge-cpp.txt
for model in nano tiny; do
  VL_RW="results data/phase-6" scripts/drun.sh vision-lab:phase6-smoke --cpus=4 ${extra[@]+"${extra[@]}"} -- \
    /src/build/detect_sequence --sequence /work/data/MOT17/train/MOT17-02-FRCNN \
    --model "/work/models/bytetrack_${model}_mot17.onnx" --threads 4 --limit 50 \
    --out "/work/data/phase-6/$model-detections.txt"
  VL_RW="results data/phase-6" scripts/drun.sh vision-lab:phase6-smoke --cpus=4 ${extra[@]+"${extra[@]}"} -- \
    /src/build/track_sequence --sequence /work/data/MOT17/train/MOT17-02-FRCNN \
    --model "/work/models/bytetrack_${model}_mot17.onnx" --threads 4 --limit 50 \
    --out "/work/data/phase-6/$model-tracks.txt"
  for repeat in 1 2 3; do
    VL_RW="results data/phase-6" scripts/drun.sh vision-lab:phase6-smoke --cpus=4 ${extra[@]+"${extra[@]}"} -- \
      /src/build/benchmark_pipeline --sequence /work/data/MOT17/train/MOT17-02-FRCNN \
      --model "/work/models/bytetrack_${model}_mot17.onnx" --threads 4 --warmup 50 --frames 100 \
      --out "/work/results/phase-6/$model-r$repeat.csv" > "results/phase-6/$model-r$repeat.json"
    echo "$model four-thread smoke benchmark repeat $repeat complete"
  done
done
runpy /work/python/phase6_smoke_report.py smoke
