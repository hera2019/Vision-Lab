# Vision Lab — Work Plan

Status: **Phase 4–5 evidence complete; Phase 6 entry point and local isolated validation complete, fresh-clone/full acceptance pending; independent review pending** · Started 2026-10-06 · Target 2026-10-13

Detailed test plan and acceptance criteria: [01-phase-0-plan.md](01-phase-0-plan.md).
Detector: ByteTrack's YOLOX nano/tiny checkpoints (decided 2026-10-06).

Review: [Opus verdict](reviews/phase-3.md); [follow-up verification](../results/phase-3-review-fixes.md).
The reviewer has not re-reviewed the follow-up changes. The separately
[predeclared continuity pilot](CONTINUITY_PILOT.md) and its
[results](../results/continuity-pilot.md) use exposed MOT17 development footage
and synthetic examples, not new held-out accuracy evidence. The accepted
baseline settings, outputs and demos stay unchanged. Owner-reported failures:
[pillar](../results/phase-3-occlusion-case-75-107.md),
[moving street](../results/phase-3-mobile-case-3-4-18.md).

Phase 4: [executor execution protocol](PHASE4_EXECUTION.md),
[complete measurements](../results/phase-4-performance.md),
[initial FP32 results](../results/phase-4-performance-fp32.md), and
[approved dependency installation](../results/phase-4-dependency.md). All 18 initial
FP32 runs completed with fixed warm-up/repeats/quotas. The owner authorized the
missing dependency on 2026-10-06; both INT8 models are generated using the same
112 MOT17 calibration frames. Paired speed tests and full MOT20 accuracy are
complete: 36 paired repeats and all 8,931 held-out MOT20 frames per model.
At four threads, nano FP32/INT8 measures 27.34/25.46 FPS and tiny 9.76/18.25 FPS.
Nano INT8 loses 56.1002 pp MOTA; tiny loses 1.0635 pp, above the fixed 1.0 pp cap.
Neither INT8 model is accepted at any tested budget; baseline unchanged.
[Read-only development diagnostics](../results/phase-4-int8-diagnostic.md) confirm
matching input preprocessing and identical original/preprocessed FP32 outputs
on three frames; the specific INT8 failure cause remains unisolated.
Final speed ratios use the paired matrix.

Phase 5: [executor protocol](PHASE5_EXECUTION.md),
[three-category failure report](../results/phase-5-failures.md), and
[beginner walkthrough](walkthrough/phase-5.md). Owner-reported MOT20-03
occlusion (75→107), MOT20-01 identity correspondence switch (13→22), and
small/truncated target detection misses each include frame intervals, crops,
per-frame GT/detection/track evidence and provenance. CLEAR audit counts match
upstream on the three scanned sequences. These are illustrative examples,
not frequency estimates or tuned improvements. Mandatory Phase 5 evidence is
complete; independent review pending. Mean-shift remains an optional deferred
bonus. Phase 6 fresh-clone reproduction is the next mandatory stage.

Phase 6: [README](../README.md), [execution protocol](PHASE6_EXECUTION.md),
[reproduction record](../results/phase-6-reproduction.md), and
[walkthrough](walkthrough/phase-6.md). One-command smoke/full profiles added;
full execution remains untested. The isolated source snapshot reproduces
both FP32 models' first-50-frame detections/tracks byte for byte and passes
Python/C++ synthetic behavior. Nano four-thread FPS 27.215 is inside the
original repeat interval; tiny 10.131 is outside, despite being faster, and
that strict check failure stays. Standalone root C++ dependency build succeeds
after the authorized download and produces identical 50-frame outputs.
Initial offline-build and mount failures remain recorded. Actual clean HEAD
clone is `6f0e68f` and lacks current Phase 3–6 source. Complete-source commit,
fresh clone and full numerical/environment validation are still required;
no commit/push performed. Fresh Python dependency installation has not been
tested. Local snapshots are not counted as fresh-clone acceptance.

## Goal

A one-week, reproducible study of **object detection + multi-object tracking on
CPU-only edge-class compute**, answering the same three questions as
[AI-Lab](https://github.com/hera2019/AI-Lab):

> Can this pipeline ship? What does it cost? How does it fail?

It provides evidence for: deep-learning vision, C++ inference (ONNX Runtime),
Linux, and Docker.

## Scope

- **Detection:** YOLOX nano (primary) and tiny, using the ByteTrack authors' pedestrian checkpoints.
- **Tracking:** ByteTrack-style association.
- **Inference:** model exported to ONNX and run from **C++ via ONNX Runtime**.
  Python is used only for export, evaluation and reporting.
- **Runtime:** everything runs inside a **Linux Docker container, CPU only**
  (Docker on macOS runs a Linux VM, so this stands in for an edge device).
- **Data:** public videos / MOT benchmark sequences with licenses recorded.

## Measurements

| Category | Metrics |
|---|---|
| Speed | FPS, per-frame latency (mean / p50 / p95), split into pre-process / inference / post-process / tracking |
| Cost | Peak RSS memory, model file size, CPU thread count used |
| Precision trade-off | FP32 vs INT8 (ONNX Runtime quantization): speed, size, and detection/tracking accuracy delta |
| Tracking quality | MOTA, IDF1 (HOTA if cheap), ID switches |
| Failure cases | Occlusion, ID switches, small objects — kept with frame references |

**Bonus:** a classical mean-shift tracker baseline, compared against
detection + tracking on the same sequences.

## Phases

| Phase | Work | Acceptance |
|---|---|---|
| 0 | Test plan; choose model, tracker, data; record licenses; Docker base image | Written plan with acceptance criteria before any model download |
| 1 | Export detector to ONNX; Python reference inference | ONNX output matches the source model within a stated tolerance |
| 2 | C++ ONNX Runtime detector inside Docker | C++ detections match the Python reference on fixed frames |
| 3 | Add tracker in C++; write MOT-format results | Tracking output scores with a standard evaluator (e.g. TrackEval) |
| 4 | Benchmark: FPS / latency / memory, FP32 vs INT8 | Results in `.md` + `.json`, re-runnable with one command |
| 5 | Failure-case analysis; mean-shift baseline (bonus) | Failure cases documented, negative results kept |
| 6 | README, license notes, one-command reproduction | Fresh clone → `docker build` + one run command reproduces the headline numbers |

## Method (inherited from AI-Lab)

1. Test plan first, with acceptance criteria.
2. Every result is reported twice: human-readable `.md` and machine-readable `.json`.
3. "It runs" is kept separate from "it passes".
4. Negative and unresolved results are kept.
5. Pinned versions, checksums, fixed seeds; model weights and datasets live outside the repository.

## Licensing notes (to verify in Phase 0)

- MOT17 / MOT20: non-commercial research use only.
- Ultralytics YOLO models: AGPL-3.0. YOLOX and RT-DETR (official repo): Apache-2.0.
- ByteTrack: MIT. ONNX Runtime: MIT.

## Out of scope

GPU / NPU acceleration, training or fine-tuning, multi-camera tracking.
