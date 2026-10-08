#!/usr/bin/env bash
# Fixed post-hoc candidates. Explicit separate stages prevent held-out tuning.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mkdir -p data/phase-4-repair results/phase-4-repair
mode=${1:-develop}
py() {
  VL_RW='results data/phase-4-repair' scripts/drun.sh vision-lab:phase4-pytools -- \
    python -B /work/python/phase4_nano_repair.py "$1"
}
track() {
  local benchmark=$1 candidate=$2 sequence name target
  for sequence in data/"$benchmark"/train/*; do
    name=$(basename "$sequence")
    if [[ $benchmark == MOT17 && $name != *-FRCNN ]]; then continue; fi
    target="data/phase-4-repair/tracks/$benchmark/$candidate/$name.txt"
    [[ ! -e $target ]] || { echo "Refuse track overwrite: $target" >&2; exit 2; }
    VL_RW='results data/phase-4-repair' scripts/drun.sh vision-lab:phase4 --cpus=4 -- \
      /src/build/track_sequence --sequence "/work/$sequence" \
      --model "/work/data/phase-4-repair/$candidate.onnx" --threads 4 --out "/work/$target"
  done
}
case "$mode" in
  develop)
    py quantize
    track MOT17 head-fp32
    track MOT17 neck-head-fp32
    py score-mot17
    ;;
  evaluate)
    selection=results/phase-4-repair/selection.json
    candidate=$(jq -r '.selected // empty' "$selection")
    [[ -n $candidate ]] || { echo 'No qualifying MOT17 candidate; stop.' >&2; exit 2; }
    expected=$(jq -r '.selected_model_sha256' "$selection")
    actual=$(shasum -a 256 "data/phase-4-repair/$candidate.onnx")
    [[ ${actual%% *} == "$expected" ]] || { echo 'Selected model changed.' >&2; exit 2; }
    track MOT20 "$candidate"
    py score-mot20
    mkdir -p results/phase-4-repair/benchmark
    for threads in 1 2 4; do
      for repeat in 1 2 3; do
        for precision in fp32 "$candidate"; do
          model='/work/models/bytetrack_nano_mot17.onnx'
          if [[ $precision != fp32 ]]; then model="/work/data/phase-4-repair/$candidate.onnx"; fi
          stem="results/phase-4-repair/benchmark/$precision-t$threads-r$repeat"
          [[ ! -e $stem.csv ]] || { echo 'Refuse benchmark overwrite.' >&2; exit 2; }
          VL_RW=results scripts/drun.sh vision-lab:phase4 --cpus="$threads" -- \
            /src/build/benchmark_pipeline --sequence /work/data/MOT17/train/MOT17-02-FRCNN \
            --model "$model" --threads "$threads" --warmup 50 --frames 100 \
            --out "/work/$stem.csv" > "$stem.json" 2> "$stem.stderr.log"
          echo "$precision t$threads repeat$repeat complete"
        done
      done
    done
    ;;
  control)
    py weight-control
    track MOT17 weight-control
    py score-control
    ;;
  *) echo 'expected develop, control or evaluate' >&2; exit 2;;
esac
