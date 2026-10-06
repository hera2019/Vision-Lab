# Phase 4 execution protocol

Author: Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-06.
Owner authorized further work after accepted Phase 3 and its review fixes.
This executor-authored protocol implements the already frozen Phase 0 criteria;
it is not an Opus-authored taskbook or an independent review approval.
Written before Phase 4 quantization/benchmark outcomes.

## Protected baseline and environment

Keep Phase 0–2 source/results, accepted Phase 3 outputs and tracker settings
unchanged. Use the readability-cleaned, byte-verified baseline tracker, not
the continuity prototype. Only additive C++ target/build integration.
All runs through `scripts/drun.sh`, CPU only, no network, non-root, existing
6 GiB limit. Build from the existing local toolchain image; no downloads.
Record image IDs, model/data hashes, versions and Linux VM hardware. Mac
absolute FPS is not an edge-device measurement.

## Quantization fixed before calibration

Use existing ONNX Runtime 1.30 static QDQ quantization, signed INT8 weights
and activations (S8S8), per-channel weights, MinMax calibration, no reduced
range. Preprocess with ORT symbolic/ONNX shape inference and graph optimization
before quantization; preserve original FP32 files. No alternative quantization
scheme search after seeing held-out results. Report any unsupported operation
or failure rather than changing thresholds or excluding difficult layers.

Calibration: 16 evenly spaced image indices per MOT17 FRCNN sequence, selected
with NumPy linspace from frame 1 through its last frame; 112 total. Save names
and SHA-256 before use. Use the existing official YOLOX preprocessing at
608×1088 and no GT labels. Never use MOT20 for calibration or settings.
Restrict quantization to Conv operators; the remaining float operations and
float input/output are explicit mixed-precision portions. Record INT8 node
and initializer counts, file size and original/derived model hashes.

References: [ORT quantization](https://onnxruntime.ai/docs/performance/model-optimizations/quantization.html).

## Controlled benchmarks

- Models: nano/tiny × original FP32/derived static INT8.
- Budgets: ORT 1/2/4 intra-op threads, inter-op 1; container `--cpus=N` matches
  that budget. OpenCV one thread. Same native 608×1088 input and thresholds.
- One run at a time; no accuracy inference or calibration concurrently.
- Each fresh process handles MOT17-02 frames 1–150: first 50 are warm-up,
  subsequent 100 are measured. Three repeats per setting. Alternate FP32/INT8
  within each model/thread/repeat to reduce ordering bias; do not cherry-pick.
- Time image decoding, preprocess, inference, postprocess, tracker update
  plus output-box filtering, and full per-frame loop. No video rendering or
  disk result serialization inside the measured loop. FPS is in-process
  image-to-track throughput, including JPEG read/decode and filtering.
- Store raw per-frame timings. Report mean/p50/p95 per stage and end-to-end,
  each repeat's FPS and aggregate median repeat FPS. Peak process RSS is
  `/proc/self/status` VmHWM, including startup/warm-up; not host/VM memory.
- A given setting meets the frozen real-time gate only at >=25 FPS; preserve
  every failed setting. `--cpus` is a quota, not physical-core pinning.

## Held-out INT8 comparison

If both derived models load and produce finite native-shaped outputs, run
unchanged C++ detector+tracker on all four complete MOT20 sequences at 4 ORT
threads. Keep A1 configuration and emit tracks under `data/phase-4/`.
Report both motmetrics and TrackEval with their existing respective procedures;
compare each only to the same evaluator's stored FP32 baseline. No modified
tracker variant, MOT20 tuning, or recalibration after scoring.

Compute the predefined “worth it” gate per model and thread budget:
median-repeat end-to-end INT8/FP32 speed-up >=1.3 and overall MOT20 MOTA drop
<=1.0 percentage point (motmetrics, matching the fixed ByteTrack procedure).
Report TrackEval deltas alongside; do not substitute them into this gate.
INT8 outcomes are reported regardless of success. No claim about detection AP:
tracking metrics, counts and downstream effects are measured here.

## Deliverables and checks

`results/phase-4-performance.md` / `.json`, raw benchmark/evaluation/calibration
records, rerunnable scripts, assets provenance, change/issue ledger updates,
and bilingual `docs/walkthrough/phase-4.md`. Preserve incomplete/failed runs.
Check benchmark frame/repeat counts and warm-up exclusion, VmHWM presence,
CPU quotas, finite outputs, all accuracy sequence frame counts and hashes.
No commits, push, new assets, global Docker setting changes, Phase 0–2 edits
or baseline replacement. Stop if disk falls below 10 GiB or a new download
would be required.

## Execution notes (additive, no metric/settings changes)

- Owner approved only the missing ml_dtypes dependency download on 2026-10-06;
  use the separately pinned/hash-checked image proposal. Runtime remains offline.
- ORT 1.30's intermediate cap clears observations without merging their
  calibration ranges. Initial cap 1 failed; cap 128 holds all 112 fixed frames,
  and reader sample count is asserted. This changes storage, not the dataset,
  MinMax method, quantization scheme, or 6 GiB memory limit.
- Before held-out accuracy, check the existing fixed MOT17-02 first-50-frame
  detection slice at 1/4 threads for both INT8 models. Byte identity is evidence
  of consistency on that slice, not full held-out accuracy at every budget.
- Initial FP32-only measurements/report stay under their original raw directory
  and `phase-4-performance-fp32.*`; use the complete alternating paired matrix
  for final speed ratios. Independent review of Phase 4 remains pending.
