# Issues

Record each issue before changing code: observation, reproduction, proposed
minimal fix, status. Append; do not delete resolved entries.

## I-1 · Phase 1 raw-output tolerance is badly specified (open, accepted as-is)

- **Observed:** nano PyTorch vs ONNX Runtime max abs diff 1.18e-3 > 1e-3 on raw outputs.
- **Cause:** the criterion spans all 13,566 anchors; the worst diff is on a background anchor (score 7.8e-10). Diff is identical at every ORT optimisation level. On anchors with score > 0.1 the diff is ≤ 2.4e-5.
- **Decision:** keep "fail" on record; no re-scoring. Later criteria are stated on post-NMS detections. See `results/phase-1-export-parity.md`.

## I-2 · ByteTrack's official C++ tracker port differs from its Python tracker (known before Phase 3)

- **Observed (code reading, ByteTrack commit `d1bf019`):** `yolox/tracker/byte_tracker.py` applies `matching.fuse_score` (IoU similarity multiplied by detection score) in the first and the unconfirmed association when not MOT20. `deploy/ncnn/cpp/src/BYTETracker.cpp` has no equivalent.
- **Consequence:** a port copied from `deploy/ncnn/cpp` will not reproduce the Python results. Phase 3 must follow the Python tracker; any deviation is recorded here.

## I-3 · TrackEval master is incompatible with NumPy ≥ 1.24 (known before Phase 3)

- **Observed (code reading, TrackEval commit `12c8791`):** uses removed aliases `np.float`, `np.int` (e.g. `trackeval/datasets/mot_challenge_2d_box.py` lines 228, 359, 413, 420). The pytools image has NumPy 2.1.3.
- **Proposed minimal fix:** in our own runner, before importing TrackEval, set `np.float = float`, `np.int = int`, `np.bool = bool` if missing. Do not edit `external/TrackEval`. Verify by evaluating the ground truth against itself (expect MOTA = IDF1 = 100).
