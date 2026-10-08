# Post-hoc nano remedy and diagnostic control

2026-10-07T16:37:37.149329+00:00

Author: Codex / GPT-6 (exact runtime model ID not exposed). [Protocol](../docs/PHASE4_REPAIR.md). Original static INT8 failure and accepted FP32 baseline remain unchanged.

## MOT17 development: fixed candidates

| Candidate | MOTA | IDF1 | MOTA loss pp | IDF1 loss pp |
|---|---:|---:|---:|---:|
| head-fp32 | 10.6681 | 15.5008 | 58.5643 | 51.3406 |
| neck-head-fp32 | 37.3153 | 41.4902 | 31.9171 | 25.3513 |
| weight-control | 69.1755 | 66.4100 | 0.0570 | 0.4315 |

Each candidate processes all 5,316 MOT17 frames with the original C++ tracker. These are fidelity/development scores, not held-out accuracy. The first two candidates keep 77/47 convolutions activation-quantized. After both fail the development rule, the conditional control preserves exact original INT8 weight arrays/scales, with every activation and bias floating. **Weight-control uses FP32 convolution computation; it is not INT8 acceleration.** Pre-held-out selection: **weight-control**. The declaration and model hash are saved before any new MOT20 evaluation.

## Single MOT20 evaluation

All 8,931 frames evaluated once. Original FP32 MOTA 56.0207; original INT8 MOTA -0.0795. Selected variant MOTA **55.3158**, IDF1 **51.8449** (motmetrics).

| Threads / CPU quota | Paired FP32 FPS | Variant FPS | Speed ratio | MOTA loss pp | Original usefulness rule |
|---|---:|---:|---:|---:|---|
| 1 | 11.547 | 11.896 | 1.030x | 0.7049 | FAIL |
| 2 | 19.193 | 19.096 | 0.995x | 0.7049 | FAIL |
| 4 | 28.308 | 27.430 | 0.969x | 0.7049 | FAIL |

Three fresh paired repeats per budget; original 50-frame warm-up/100-frame measured slice. Raw timing, p50/p95 and memory metadata are retained. Drawing/writing excluded. No selection or recalibration on MOT20, and no further candidate after this evaluation.

## Interpretation and limits

The [diagnosis](phase-4-nano-diagnosis.md) observes low high-confidence detection counts on MOT20. MOT17 already shows a stem step of 0.7163 and all observed negative floating activations rounding to zero; the corresponding integer saturation rate is negligible. Large downstream head errors coexist with this loss of resolution. This is evidence of destructive numerical resolution loss, not evidence that MOT20 alone exceeded calibration ranges. The control retains weight quantization but removes activation quantization and restores FP32 biases across the whole network; original bias dequantization differs from FP32 by up to 0.013972. The two changes are not separately isolated, so restored quality supports the activation/bias path over weight quantization, not an exclusive causal attribution to activation quantization. It does not isolate one causal convolution or prove that negative rounding alone explains every error. Post-hoc measurements are clearly separated from the original predeclared experiment. No baseline replacement, fresh-clone acceptance of these uncommitted additions, cold-install or edge-device claim.

First candidate-build attempt failed because ORT tried to create an inferred helper beside a read-only input. The failure log is retained; the remedy uses a byte-identical input copy in the new writable directory. Outside-window diagnostic v1 is archived; v2 distinguishes rounding from true clamp saturation. Neither correction changes the original artifacts or container protections.
The original development driver also exits 127 after saving both scores/null selection because the executor edited the still-running shell file; its full log is retained. Subsequent stages use the completed saved driver.
