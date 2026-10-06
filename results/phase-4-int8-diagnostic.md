# Phase 4 INT8 failure diagnosis

Read-only diagnosis on MOT17-02 frames 1/51/150; no held-out input, modified model or alternative quality score.

The calibration helper uses the same official RGB normalization as the existing Python reference. Independent reconstruction of the C++ formula agrees within 1e-6 on all three fixed images. This is a limited input check, not a full new parity claim.

| Model | Graph/runtime | Frame | Raw max difference from original FP32 | Maximum confidence | Post-NMS boxes >=0.01 | Post-NMS boxes >=0.6 |
|---|---|---:|---:|---:|---:|---:|
| nano | fp32-original | 1 | 0 | 0.871982 | 184 | 10 |
| nano | fp32-original | 51 | 0 | 0.878948 | 141 | 10 |
| nano | fp32-original | 150 | 0 | 0.882313 | 200 | 14 |
| nano | fp32-preprocessed | 1 | 0 | 0.871982 | 184 | 10 |
| nano | fp32-preprocessed | 51 | 0 | 0.878948 | 141 | 10 |
| nano | fp32-preprocessed | 150 | 0 | 0.882313 | 200 | 14 |
| nano | int8-optimized | 1 | 8.69577 | 0.808968 | 510 | 16 |
| nano | int8-optimized | 51 | 8.94211 | 0.915634 | 463 | 27 |
| nano | int8-optimized | 150 | 10.1385 | 0.892895 | 504 | 26 |
| nano | int8-optimization-disabled | 1 | 9.67765 | 0.891454 | 450 | 18 |
| nano | int8-optimization-disabled | 51 | 9.32042 | 0.899861 | 487 | 15 |
| nano | int8-optimization-disabled | 150 | 9.58787 | 0.917965 | 493 | 31 |
| tiny | fp32-original | 1 | 0 | 0.909971 | 139 | 17 |
| tiny | fp32-original | 51 | 0 | 0.907041 | 118 | 16 |
| tiny | fp32-original | 150 | 0 | 0.90403 | 153 | 23 |
| tiny | fp32-preprocessed | 1 | 0 | 0.909971 | 139 | 17 |
| tiny | fp32-preprocessed | 51 | 0 | 0.907041 | 118 | 16 |
| tiny | fp32-preprocessed | 150 | 0 | 0.90403 | 153 | 23 |
| tiny | int8-optimized | 1 | 7.07117 | 0.915291 | 150 | 17 |
| tiny | int8-optimized | 51 | 9.14135 | 0.906786 | 124 | 16 |
| tiny | int8-optimized | 150 | 6.85385 | 0.915106 | 163 | 20 |
| tiny | int8-optimization-disabled | 1 | 7.1965 | 0.915584 | 157 | 16 |
| tiny | int8-optimization-disabled | 51 | 8.92324 | 0.906786 | 126 | 16 |
| tiny | int8-optimization-disabled | 150 | 7.08266 | 0.915106 | 165 | 20 |

Optimization-disabled INT8 is diagnostic only. It is not benchmarked or proposed as a replacement. No setting, model, threshold or calibration changes.

These observations distinguish input preparation, FP32 graph preprocessing and INT8/runtime behavior on a development slice. They do not isolate a specific operator or establish a general root cause. The complete MOT20 failure remains the acceptance result.
