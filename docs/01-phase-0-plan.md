# Phase 0 — Test Plan

Written 2026-10-06, **before any model weights or datasets were downloaded.**
Acceptance criteria and thresholds below are fixed now; if one changes later,
the change and its reason are recorded here, not silently edited.

## Questions

1. **Can it ship?** Does a C++ ONNX Runtime detector + ByteTrack pipeline run
   in real time inside a CPU-only Linux container with an edge-like thread budget?
2. **What does it cost?** Latency per stage, throughput, peak memory, model size;
   what INT8 quantization buys and what it costs in accuracy.
3. **How does it fail?** Occlusion, ID switches, small and distant objects,
   crowding — with frame references, not anecdotes.

## Components

| Role | Choice | Why |
|---|---|---|
| Detector | `bytetrack_nano_mot17` (primary), `bytetrack_tiny_mot17` (secondary) — YOLOX trained for pedestrians by the ByteTrack authors | Edge-sized (0.90 M / 5.03 M params, 3.99 / 24.45 GFLOPs), Apache-2.0 / MIT, published MOTA/IDF1 to reproduce |
| Tracker | ByteTrack, ported to C++ | MIT; reference Python implementation available for parity checks |
| Runtime | ONNX Runtime 1.30.0, CPU execution provider, C++ API | MIT; prebuilt for linux-aarch64 and linux-x64 |
| Image I/O | OpenCV (Ubuntu 24.04 packages) | Decoding, resize, drawing |
| Evaluation | TrackEval (MOTA, IDF1, HOTA) | MIT; the reference implementation used by MOTChallenge |
| Container | `ubuntu:24.04`, CPU only | Matches common edge Linux userlands |

## Data — and a contamination problem

The ByteTrack light models were trained on *MOT17 train + CrowdHuman +
Cityperson + ETHZ*, and their published scores (nano 69.0 MOTA / 66.3 IDF1,
tiny 77.1 / 71.5) are measured **on MOT17 train — data the model has seen.**
MOT17 test has no public ground truth.

So the data is split by purpose, and every result is labelled with it:

| Set | Seen in training? | Used for |
|---|---|---|
| MOT17 train (7 sequences, one image copy) | **Yes** | *Fidelity only*: does our C++ pipeline reproduce the published numbers? Never reported as accuracy. |
| MOT20 train (4 sequences, 8,931 frames, ground truth public) | No | *Accuracy*: held-out MOTA / IDF1 / HOTA. Very crowded scenes, so a harder, shifted domain — expected to score much lower. |

INT8 calibration frames come from MOT17 train only, never from MOT20.

## Hardware caveat

Docker on this Mac runs a Linux VM on Apple Silicon cores (arm64, 12 vCPU,
~8 GB). These are much faster than typical edge CPUs (e.g. Cortex-A76). Thread
budgets of **1, 2 and 4 threads** stand in for edge core counts, but absolute
FPS is **not** an edge-device number. Relative results (FP32 vs INT8, nano vs
tiny, stage breakdown) transfer better than absolute ones.

## Phases and acceptance criteria

| Phase | Check | Pass criterion |
|---|---|---|
| 0 | Container builds; C++ links ONNX Runtime and OpenCV | `env_check` reports ORT 1.30.0 with `CPUExecutionProvider`, OpenCV JPEG round-trip OK |
| 1 | PyTorch → ONNX export parity | On 20 fixed MOT17 frames, raw head outputs max abs diff ≤ 1e-3 |
| 2 | C++ detector vs Python ONNX reference | Same frames: same detection count after NMS; every box matched with IoU ≥ 0.99 and score diff ≤ 1e-3 |
| 3a | C++ ByteTrack vs official Python ByteTrack, same detections | MOTA and IDF1 within 0.1 on each MOT17 train sequence |
| 3b | End-to-end fidelity on MOT17 train | Within ±1.0 of published MOTA / IDF1 (nano 69.0 / 66.3, tiny 77.1 / 71.5). A larger gap is reported and investigated, not tuned away. |
| 4 | Speed and cost | 50 warm-up frames excluded; ≥ 3 repeats; report median and p95 per stage; peak RSS from `VmHWM` |
| 4 | INT8 (ORT static QDQ) | Reported regardless of outcome. Called *worth it* only if end-to-end speed-up ≥ 1.3× **and** MOT20 MOTA drop ≤ 1.0 point |
| 4 | Real time | "Ships" at a given thread budget if end-to-end ≥ 25 FPS at the model's native 608×1088 input. Lower input sizes reported separately, never substituted. |
| 5 | Failure cases | ≥ 3 categories, each with sequence + frame range + crop, from MOT20 (held-out) |
| 5 | Mean-shift baseline (bonus) | OpenCV mean-shift initialised from first-appearance ground truth boxes, scored with the same TrackEval settings |
| 6 | Reproduction | Fresh clone → documented commands reproduce headline numbers within run-to-run variance |

## Amendments

Additions only, each dated and made **before** the data it concerns was run.

### A1 · 2026-10-06 · Tracker settings and evaluators (before any tracking run)

- **MOT17 train (fidelity):** reproduce ByteTrack's own procedure exactly: tracker
  defaults `track_thresh 0.6, track_buffer 30, match_thresh 0.9, min_box_area 100`,
  boxes with w/h > 1.6 dropped, frame rate 30, plus the per-sequence overrides in
  `yolox/evaluators/mot_evaluator.py` (e.g. MOT17-05 `track_buffer 14`, MOT17-13
  `track_buffer 25`). Scored with ByteTrack's own motmetrics evaluation
  (`tools/track.py`), because that is how the published numbers were produced.
  TrackEval numbers are reported alongside, labelled as such.
- **MOT20 train (held-out):** the deployed configuration, unchanged: the MOT17
  defaults above, `fuse_score` on (MOT17 mode), **no** per-sequence overrides,
  input 608×1088. No MOT20-specific tuning, because tuning on held-out data would
  make it no longer held out. Reported with both TrackEval (HOTA, MOTA, IDF1) and motmetrics.
- **Detection thresholds** for all tracking runs: conf 0.01, NMS IoU 0.7 (as Phase 2).

## Not claimed

- No training or fine-tuning; weights are the authors' published checkpoints.
- No MOT17 test-server submission.
- MOT17 train scores are a pipeline check, not an accuracy result.
