# Third-party licenses

Checked 2026-10-06. Model weights and datasets are **not** redistributed in this
repository; scripts download them from the original sources.

| Component | Source | License | Notes |
|---|---|---|---|
| ByteTrack (code, tracker, light-model checkpoints) | [FoundationVision/ByteTrack](https://github.com/FoundationVision/ByteTrack) | MIT | Checkpoints trained on MOT17, CrowdHuman, Cityperson, ETHZ — see dataset terms below |
| YOLOX (detector architecture) | [Megvii-BaseDetection/YOLOX](https://github.com/Megvii-BaseDetection/YOLOX) | Apache-2.0 | |
| ONNX Runtime 1.30.0 | [microsoft/onnxruntime](https://github.com/microsoft/onnxruntime) | MIT | Prebuilt Linux tarballs, SHA-256 pinned in the Dockerfile |
| ml_dtypes 0.6.0 | [PyPI release files](https://pypi.org/project/ml-dtypes/0.6.0/#files) | Apache-2.0; bundled Eigen MPL-2.0 | Owner-approved, hash-pinned binary wheel in the separate Phase 4 Python image only |
| TrackEval | [JonathonLuiten/TrackEval](https://github.com/JonathonLuiten/TrackEval) | MIT | |
| OpenCV | Ubuntu 24.04 packages | Apache-2.0 | |
| Eigen | Ubuntu 24.04 packages | MPL-2.0 | |
| MOT17, MOT20 | [motchallenge.net](https://motchallenge.net/) | CC BY-NC-SA 3.0 | **Non-commercial research only.** Any frames, crops or GIFs from these sequences shown in this repository are shared under the same license, with attribution to the MOTChallenge authors. |

## Consequences

- `cpp/src/tracker/tracker.*` ports the ByteTrack Python tracker at commit
  `d1bf0191adff59bc8fcfeaa0b33d3d1642552a99`. `cpp/src/tracker/lapjv.*` is
  copied from that revision's `deploy/ncnn/cpp` linear assignment solver.
  The upstream MIT notice is preserved in `cpp/src/tracker/LICENSE.ByteTrack`.

- This repository's own code is released under its own license (see `LICENSE`).
- Results derived from MOT17 / MOT20 are for non-commercial research.
- The ByteTrack light checkpoints were trained on datasets with their own
  terms (CrowdHuman is non-commercial as well). Treat the weights as research-only.
