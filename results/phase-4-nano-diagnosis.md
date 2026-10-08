# Post-hoc nano INT8 diagnosis

2026-10-07T16:17:07.589861+00:00

Original model unchanged. Selected frames; counts are not dataset-wide estimates.

| Frame | FP32 boxes >=0.6 | Original INT8 boxes >=0.6 |
|---|---:|---:|
| data/MOT17/train/MOT17-02-FRCNN/img1/000002.jpg | 10 | 31 |
| data/MOT17/train/MOT17-02-FRCNN/img1/000300.jpg | 15 | 60 |
| data/MOT17/train/MOT17-04-FRCNN/img1/000002.jpg | 44 | 6 |
| data/MOT17/train/MOT17-04-FRCNN/img1/000525.jpg | 40 | 3 |
| data/MOT17/train/MOT17-05-FRCNN/img1/000002.jpg | 2 | 1 |
| data/MOT17/train/MOT17-05-FRCNN/img1/000418.jpg | 4 | 0 |
| data/MOT17/train/MOT17-09-FRCNN/img1/000002.jpg | 5 | 1 |
| data/MOT17/train/MOT17-09-FRCNN/img1/000262.jpg | 9 | 0 |
| data/MOT17/train/MOT17-10-FRCNN/img1/000002.jpg | 15 | 14 |
| data/MOT17/train/MOT17-10-FRCNN/img1/000327.jpg | 15 | 8 |
| data/MOT17/train/MOT17-11-FRCNN/img1/000002.jpg | 9 | 0 |
| data/MOT17/train/MOT17-11-FRCNN/img1/000450.jpg | 9 | 0 |
| data/MOT17/train/MOT17-13-FRCNN/img1/000002.jpg | 14 | 12 |
| data/MOT17/train/MOT17-13-FRCNN/img1/000375.jpg | 12 | 9 |
| data/MOT20/train/MOT20-01/img1/000001.jpg | 23 | 1 |
| data/MOT20/train/MOT20-01/img1/000150.jpg | 25 | 3 |
| data/MOT20/train/MOT20-02/img1/000001.jpg | 30 | 2 |
| data/MOT20/train/MOT20-02/img1/000150.jpg | 33 | 6 |
| data/MOT20/train/MOT20-03/img1/000001.jpg | 72 | 16 |
| data/MOT20/train/MOT20-03/img1/000150.jpg | 77 | 9 |
| data/MOT20/train/MOT20-05/img1/000001.jpg | 123 | 3 |
| data/MOT20/train/MOT20-05/img1/000150.jpg | 131 | 8 |

## Quantization diagnostics

Outside-range counts describe values beyond the model's fixed INT8 representable window. They are not clamp counts: rounding near an endpoint can land on it without integer overflow. Actual saturation counts apply round-to-nearest then test integer bounds, and are recorded separately. FP32 values are counterfactual; INT8 prequant values are observed in the instrumented QDQ graph. Relative L1 error compares corresponding prequantization tensors after accumulated upstream quantization errors. Clipping/error alone does not establish a single causal operator.

### MOT17: ten largest head relative errors

| Tensor | FP32 outside | INT8 prequant outside | Relative L1 |
|---|---:|---:|---:|
| `/head/reg_convs.0/reg_convs.0.1/pconv/conv/Conv_output_0` | 0.0000% | 0.0000% | 1.3638 |
| `/head/cls_convs.0/cls_convs.0.1/pconv/conv/Conv_output_0` | 0.0000% | 0.0000% | 1.3569 |
| `/head/cls_preds.0/Conv_output_0` | 0.0000% | 0.0062% | 1.3051 |
| `/head/cls_convs.0/cls_convs.0.1/pconv/act/Mul_output_0` | 0.0000% | 0.0000% | 1.2706 |
| `/head/cls_convs.1/cls_convs.1.0/pconv/act/Mul_output_0` | 0.0000% | 0.0000% | 1.2022 |
| `/head/stems.1/act/Mul_output_0` | 0.0000% | 0.0000% | 1.1765 |
| `/head/cls_convs.1/cls_convs.1.0/pconv/conv/Conv_output_0` | 0.0000% | 0.0000% | 1.1756 |
| `/head/cls_convs.0/cls_convs.0.0/pconv/act/Mul_output_0` | 0.0000% | 0.0000% | 1.1749 |
| `/head/reg_convs.0/reg_convs.0.1/pconv/act/Mul_output_0` | 0.0000% | 0.0000% | 1.1505 |
| `/head/reg_convs.0/reg_convs.0.0/pconv/act/Mul_output_0` | 42.1996% | 25.8277% | 1.1327 |

Ten largest observed prequant integer-clamp fractions:

| Tensor | FP32 clamps | INT8 prequant clamps |
|---|---:|---:|
| `/backbone/backbone/dark2/dark2.1/conv2/conv/Conv_output_0` | 0.0000% | 0.1289% |
| `/backbone/backbone/dark4/dark4.1/m/m.1/Add_output_0` | 0.0000% | 0.0389% |
| `/head/reg_preds.0/Conv_output_0` | 0.0000% | 0.0126% |
| `/head/cls_preds.2/Conv_output_0` | 0.0111% | 0.0111% |
| `/backbone/backbone/dark3/dark3.0/dconv/conv/Conv_output_0` | 0.0000% | 0.0089% |
| `/head/cls_preds.0/Conv_output_0` | 0.0000% | 0.0055% |
| `/backbone/backbone/dark3/dark3.0/dconv/act/Mul_output_0` | 0.0000% | 0.0048% |
| `/head/obj_preds.0/Conv_output_0` | 0.0000% | 0.0041% |
| `/backbone/backbone/dark2/dark2.1/m/m.0/conv1/conv/Conv_output_0` | 0.0000% | 0.0017% |
| `/backbone/backbone/dark3/dark3.1/conv2/conv/Conv_output_0` | 0.0000% | 0.0012% |
### MOT20: ten largest head relative errors

| Tensor | FP32 outside | INT8 prequant outside | Relative L1 |
|---|---:|---:|---:|
| `/head/cls_preds.0/Conv_output_0` | 0.0000% | 0.0145% | 1.9006 |
| `/head/cls_convs.0/cls_convs.0.1/pconv/conv/Conv_output_0` | 0.0000% | 0.0000% | 1.5629 |
| `/head/reg_convs.0/reg_convs.0.1/pconv/conv/Conv_output_0` | 0.0001% | 0.0000% | 1.4147 |
| `/head/cls_preds.2/Conv_output_0` | 0.0000% | 0.0000% | 1.3757 |
| `/head/cls_convs.0/cls_convs.0.1/pconv/act/Mul_output_0` | 0.0000% | 0.0000% | 1.3506 |
| `/head/reg_convs.0/reg_convs.0.1/pconv/act/Mul_output_0` | 0.0000% | 0.0000% | 1.2790 |
| `/head/cls_convs.0/cls_convs.0.0/pconv/act/Mul_output_0` | 0.0000% | 0.0000% | 1.2745 |
| `/head/stems.1/act/Mul_output_0` | 0.0000% | 0.0000% | 1.1893 |
| `/head/cls_convs.1/cls_convs.1.0/pconv/act/Mul_output_0` | 0.0000% | 0.0000% | 1.1637 |
| `/head/reg_convs.0/reg_convs.0.0/pconv/act/Mul_output_0` | 42.0411% | 25.6544% | 1.1556 |

Ten largest observed prequant integer-clamp fractions:

| Tensor | FP32 clamps | INT8 prequant clamps |
|---|---:|---:|
| `/backbone/backbone/dark2/dark2.1/conv2/conv/Conv_output_0` | 0.0000% | 0.0834% |
| `/backbone/backbone/dark4/dark4.1/m/m.1/Add_output_0` | 0.0001% | 0.0451% |
| `/head/cls_preds.0/Conv_output_0` | 0.0000% | 0.0133% |
| `/backbone/backbone/dark3/dark3.0/dconv/conv/Conv_output_0` | 0.0000% | 0.0057% |
| `/head/reg_preds.0/Conv_output_0` | 0.0000% | 0.0048% |
| `/head/obj_preds.1/Conv_output_0` | 0.0000% | 0.0048% |
| `/backbone/backbone/dark3/dark3.0/dconv/act/Mul_output_0` | 0.0000% | 0.0040% |
| `/backbone/backbone/dark2/dark2.1/m/m.0/conv2/pconv/conv/Conv_output_0` | 0.0000% | 0.0030% |
| `/backbone/backbone/dark2/dark2.1/m/m.0/conv1/conv/Conv_output_0` | 0.0001% | 0.0027% |
| `/head/obj_preds.0/Conv_output_0` | 0.0024% | 0.0012% |

All instrumented final outputs equal noninstrumented outputs with optimization disabled. Optimized/unoptimized differences and all tensor ranges are recorded in the [JSON](phase-4-nano-diagnosis.json). This instrumented graph can suppress deployment fusions; only ordinary optimized inference supplies the detection counts.
