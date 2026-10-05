# Phase 1 — ONNX export parity

Date: 2026-10-06 · Result: **tiny pass · nano FAIL (criterion as written)**, explained below

Criterion (fixed in [the test plan](../docs/01-phase-0-plan.md) before any download):
on 20 fixed MOT17 frames, raw head outputs of PyTorch and ONNX Runtime differ by
**at most 1e-3** (max absolute difference).

## Commands

```bash
docker build --target pytools -t vision-lab:pytools .
docker run --rm -v "$PWD:/work" -w /work/python vision-lab:pytools python export_onnx.py nano
docker run --rm -v "$PWD:/work" -w /work/python vision-lab:pytools python export_onnx.py tiny
docker run --rm -v "$PWD:/work" -w /work/python vision-lab:pytools python check_export_parity.py
docker run --rm -v "$PWD:/work" -w /work/python vision-lab:pytools python investigate_parity.py
```

Data: [`phase-1-export-parity.json`](phase-1-export-parity.json),
[`phase-1-parity-investigation.json`](phase-1-parity-investigation.json).
Frames: 20 sampled with seed 0 from the FRCNN copy of MOT17 train (listed in the JSON).

## Export

| Model | ONNX size | Input | Output | Opset |
|---|---|---|---|---|
| `bytetrack_nano_mot17` | 3.65 MB | 1×3×608×1088 | 1×13566×6 | 13 |
| `bytetrack_tiny_mot17` | 20.2 MB | 1×3×608×1088 | 1×13566×6 | 13 |

The output is raw (undecoded): 4 box-regression values, objectness, class score
per anchor. Decoding, NMS and tracking happen downstream.

## Result

| Model | Max abs diff, all anchors | Criterion | Max abs diff, anchors with score > 0.1 | Decoded box diff (score > 0.1) | Candidate count (score > 0.1) identical |
|---|---|---|---|---|---|
| nano | **1.18e-3** | ≤ 1e-3 → **fail** | 2.4e-5 | ≤ 0.0014 px | 20 / 20 frames |
| tiny | 1.58e-4 | ≤ 1e-3 → pass | 1.1e-5 | ≤ 0.0017 px | 20 / 20 frames |

The nano failure is kept as a failure. The threshold is not moved after the fact.

## What the failure is

- **Where:** the worst difference is on a box-regression value of a stride-8 anchor
  whose detection score is **7.8e-10**: pure background, ~8 orders of magnitude
  below any threshold the tracker uses.
- **Not caused by ONNX Runtime graph optimizations:** the diff is bit-identical
  with `ORT_DISABLE_ALL`, `ORT_ENABLE_BASIC` and `ORT_ENABLE_ALL`.
- **Hypothesis (not tested):** float32 accumulation-order differences between
  PyTorch's and ONNX Runtime's convolution kernels. Nano uses depthwise
  convolutions; tiny does not, and tiny's diff is ~7× smaller.
- **Effect on anything downstream:** none observed. On every anchor that could
  become a detection (score > 0.1), outputs agree to 2.4e-5, decoded boxes agree
  to under 0.002 pixels, and candidate counts are identical on all 20 frames.

## What this does and does not show

- The criterion was badly specified. An absolute tolerance over **all** 13,566
  anchors is dominated by background anchors whose values never reach the output.
  Raw values there go up to ~28, so 1e-3 absolute is ~4e-5 relative: float32 noise.
- That is a reason to write better criteria for **later** phases, not to re-score
  this one. Phase 2's criterion is already stated on post-NMS detections (the
  level that reaches the tracker), and stays as written.
- This shows the exported graph computes the same function. It does **not**
  show the C++ preprocessing, decoding or NMS are right. That is Phase 2.

## Decision

Proceed to Phase 2 with both models. nano stays the primary model. Its Phase 1
status remains "fail on raw-output tolerance, no observed effect on detections".
