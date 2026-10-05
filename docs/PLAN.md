# Vision Lab — Work Plan

Status: **Phase 0 done, Phase 1 next** · Started 2026-10-06 · Target 2026-10-13

Detailed test plan and acceptance criteria: [01-phase-0-plan.md](01-phase-0-plan.md).
Detector: ByteTrack's YOLOX nano/tiny checkpoints (decided 2026-10-06).

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
