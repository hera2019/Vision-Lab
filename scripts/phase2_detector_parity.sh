#!/usr/bin/env bash
# Phase 2: C++ detector vs Python reference. Run from the repository root.
set -euo pipefail

docker build -q --target build -t vision-lab:dev . >/dev/null
docker build -q --target pytools -t vision-lab:pytools . >/dev/null

mkdir -p results/phase-2
PY=(scripts/drun.sh vision-lab:pytools -w /work/python -- python)
CPP=(scripts/drun.sh vision-lab:dev -- /src/build/detect_frames)

"${PY[@]}" check_cpp_detector.py frames
for v in nano tiny; do
  "${CPP[@]}" --model "/work/models/bytetrack_${v}_mot17.onnx" \
    --frames /work/results/phase-2/frames.txt --out "/work/results/phase-2/cpp-${v}.json"
done
"${PY[@]}" check_cpp_detector.py compare
"${PY[@]}" draw_sample.py ../results/phase-2/cpp-nano.json 1 ../results/phase-2/sample-nano.jpg
