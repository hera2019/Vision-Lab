# Phase 2 — C++ detector parity

Date: 2026-10-06 · Result: **pass (nano and tiny)**

Criterion (fixed in [the test plan](../docs/01-phase-0-plan.md)): on the same
frames, the C++ detector and the Python reference produce the same number of
detections after NMS, and every box is matched with IoU ≥ 0.99 and score
difference ≤ 1e-3.

## Command

```bash
./scripts/phase2_detector_parity.sh
```

Data: [`phase-2-detector-parity.json`](phase-2-detector-parity.json), raw C++
outputs in [`phase-2/`](phase-2/).

## What is compared

| | Python reference | C++ ([`cpp/src/detector.cpp`](../cpp/src/detector.cpp)) |
|---|---|---|
| Preprocessing | ByteTrack's `preproc` (opencv-python 4.10, float64) | Re-implemented (OpenCV 4.6, float32) |
| Inference | ONNX Runtime 1.30.0 Python | ONNX Runtime 1.30.0 C++ API, 1 thread |
| Decoding | Same arithmetic as `YOLOXHead.decode_outputs` (torch) | Re-implemented |
| NMS | ByteTrack's `postprocess` → `torchvision.ops.batched_nms` | Re-implemented greedy NMS |
| Thresholds | conf 0.01, NMS IoU 0.7 (ByteTrack `tools/track.py` defaults) | same |

Frames: the same 20 MOT17 train frames as Phase 1 (seed 0).

## Result

| Model | Detections (Python / C++) | Frames with equal count | Worst matched IoU | Worst score diff | Pass |
|---|---|---|---|---|---|
| nano | 1516 / 1516 | 20 / 20 | 0.999981 | 4.8e-6 | yes |
| tiny | 1166 / 1166 | 20 / 20 | 0.999986 | 1.9e-6 | yes |

Visual check (nano, score > 0.6) on MOT17-04 frame 177:
[`phase-2/sample-nano.jpg`](phase-2/sample-nano.jpg). It shows 41 boxes against
37 ground-truth pedestrians that are more than 25% visible. This is a sanity
look, not a score, and it is a frame the model was trained on.

## Timing observed during this run (not a benchmark)

1 ONNX Runtime thread, median over frames 2–20, single pass:

| Model | Preprocess | Inference | Postprocess |
|---|---|---|---|
| nano | 1.6 ms | 77 ms | < 0.1 ms |
| tiny | 1.6 ms | 304 ms | 0.1 ms |

These are reported only so the order of magnitude is visible. Phase 4 measures
speed properly (warm-up, repeats, thread budgets, p50/p95, memory).

## What this does and does not show

- It shows the C++ preprocessing, decoding and NMS reproduce ByteTrack's Python
  path on these frames, despite different OpenCV versions and float precision.
- It does **not** show tracking works. That is Phase 3.
- 20 frames from one dataset is a narrow sample. Phase 3's end-to-end
  comparison over all MOT17 train frames is the wider check.
