# Post-hoc nano INT8 diagnosis

2026-10-07T16:10:04.205426+00:00

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

Clipping means the activation is outside the model's fixed INT8 representable range. FP32 clipping is counterfactual; prequant INT8 clipping is observed in the instrumented QDQ graph. Relative L1 error compares corresponding prequantization tensors after accumulated upstream quantization errors. Clipping/error alone does not establish a single causal operator.

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

All instrumented final outputs equal noninstrumented outputs with optimization disabled. Optimized/unoptimized differences and all tensor ranges are recorded in the [JSON](phase-4-nano-diagnosis.json). This instrumented graph can suppress deployment fusions; only ordinary optimized inference supplies the detection counts.
