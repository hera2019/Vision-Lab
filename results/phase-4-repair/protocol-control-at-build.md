# Post-hoc nano quantization investigation

Author: Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-08.
Scope: R-A in [Opus's review](reviews/phase-4-6-opus.md). This protocol is
written before this investigation's inference/calibration. Original Phase 4
models, measurements, failed gates and calibration manifests remain unchanged.

## Diagnosis, not selection

Inspect frames 1 and 150 of each of the four MOT20 sequences. Compare FP32 and
original INT8 confidence distributions, detections after the original decoder/
NMS, and quantization ranges against the corresponding floating activations.
Also inspect frames 2 and `floor(sequence_length/2)` in each MOT17 sequence.
Save source hashes and summaries, not activation arrays. These are selected
examples, not an estimate of dataset-wide failure frequency. Adding graph
outputs may disable fusions; compare instrumented final outputs with ordinary
inference and record differences. Clipping alone does not prove causation.

## Fixed remedy candidates and selection

Use the unchanged prepared nano graph, original 112 MOT17 calibration frames,
Conv-only QDQ, signed INT8 activations/weights, per-channel weights, MinMax,
no reduced range, intermediate-output cap 128, and the existing pinned image.
Only the excluded Conv nodes differ:

1. `head-fp32`: exclude all `/head/` Conv nodes.
2. `neck-head-fp32`: exclude all Conv nodes outside `/backbone/backbone/`
   (keep the feature pyramid and prediction head floating).

Build both once; no threshold/range search. Run each on all seven MOT17
sequences, with original C++ tracker settings and four threads. Selection uses
only motmetrics MOT17 fidelity: choose the first candidate in the above order
whose overall MOTA and IDF1 losses are each no greater than 1.0 percentage
point relative to the stored FP32 nano baseline. This development rule is not
a new acceptance criterion. If neither qualifies, report unresolved and stop
before another MOT20 evaluation. Record the selected model hash and decision
before running MOT20. Do not use MOT20 diagnostic outcomes to change this list.

## One subsequent held-out evaluation

For a qualifying candidate only, run all 8,931 MOT20 frames once with unchanged
A1 settings. Score with the original motmetrics procedure. Benchmark selected
candidate and FP32 in paired order at 1/2/4 threads, matched CPU quotas, three
fresh repeats, original frames 51–150 after 50 warm-up frames. Retain raw CSVs,
hashes, model coverage, calibration provenance and selected-model declaration.
Assess the original usefulness rule (speed >=1.3x AND MOTA loss <=1.0 pp).
Failure stays failed; do not iterate after MOT20. Report a post-hoc variant,
not replacement of the original result or a newly blind research design.

## Boundary and outputs

No new dependencies, downloads, training, UI access or Docker setting changes.
Use unchanged `scripts/drun.sh`, writable `data/phase-4-repair` and `results`
only. Check disk before large runs. No commits, merge or push in this task.
New paired reports: `results/phase-4-nano-diagnosis.{md,json}` and
`results/phase-4-nano-repair.{md,json}`. Raw data: `results/phase-4-repair/`;
models/tracks: `data/phase-4-repair/`.

Method reference: [ONNX Runtime quantization debugging](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html#quantization-debugging).

## Conditional diagnostic control (declared before development scores)

The same preselected MOT17 diagnostic frames show a different mechanism from
integer saturation: the stem's step is 0.7163, its lower representable endpoint
is zero, and 100% of its observed negative floating activations round to zero.
Its actual round-then-clamp fraction is only 0.0000027%. This observation uses
MOT17, not MOT20, and motivates one conditional control if neither of the two
original candidates meets the development rule. The v1 protocol is archived in
`results/phase-4-repair/protocol-v1.md`.

`weight-control` keeps **all activations and biases FP32**, while reusing the
original model's exact per-channel INT8 weight initializers/scales/zero points
through weight-only DequantizeLinear nodes. No activation calibration is
changed or rerun. This is INT8 **weight storage with floating computation**,
not an accelerated INT8 convolution scheme. It tests whether retaining float
activations restores quality while keeping weight quantization fixed.

Only after the original MOT17 selection explicitly returns no candidate, build
this control once and evaluate all MOT17 frames. Apply the same fixed MOTA and
IDF1 loss rule. If it qualifies, declare its hash before the single full MOT20
evaluation and paired benchmarks described above; otherwise stop. No other
candidate or calibration/range search is included. Report original candidates
as failed, keep their scores/declaration, and describe the control accurately
even if it restores quality but fails the speed rule.

Commands with existing inputs/images: diagnostic via
`python -B /work/python/phase4_nano_repair.py diagnose` inside the wrapper;
`bash scripts/phase4_nano_repair.sh develop`; conditional `control` only if
selection is null; `evaluate` only for a qualifying declared model; final
`python -B /work/python/phase4_nano_repair.py report` inside the wrapper.
