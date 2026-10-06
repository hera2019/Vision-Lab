#!/usr/bin/env bash
# Sequential fresh processes; raw timing/metadata files retained per run.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="$HOME/.docker/bin:$PATH"
mode=${1:-fp32}
case "$mode" in
  fp32) precisions=(fp32);;
  paired) precisions=(fp32 int8);;
  *) echo "expected fp32 or paired" >&2; exit 2;;
esac
mkdir -p "results/phase-4/benchmark-$mode"
docker image inspect vision-lab:phase4 \
  --format '{{json .RepoTags}} {{.Id}} {{.Architecture}} {{.Os}}' \
  > "results/phase-4/benchmark-$mode/image-version.txt"
for model in nano tiny; do
  for threads in 1 2 4; do
    for repeat in 1 2 3; do
      for precision in "${precisions[@]}"; do
        path="/work/models/bytetrack_${model}_mot17.onnx"
        if [[ $precision == int8 ]]; then
          path="/work/data/phase-4/models/bytetrack_${model}_mot17.int8.onnx"
        fi
        stem="results/phase-4/benchmark-$mode/$model-$precision-t$threads-r$repeat"
        VL_RW="results" scripts/drun.sh vision-lab:phase4 --cpus="$threads" -- \
          /src/build/benchmark_pipeline --sequence /work/data/MOT17/train/MOT17-02-FRCNN \
          --model "$path" --threads "$threads" --warmup 50 --frames 100 \
          --out "/work/$stem.csv" > "$stem.json" 2> "$stem.stderr.log"
        echo "$model $precision threads=$threads repeat=$repeat completed"
      done
    done
  done
done
