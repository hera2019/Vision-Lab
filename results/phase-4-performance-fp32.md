# Phase 4 — controlled speed and memory

Date: 2026-10-06. Author: Codex / GPT-6 (exact runtime model ID not exposed).

Status: **fp32-benchmark-complete-int8-awaiting-dependency-approval**. This is a partial Phase 4 result, not phase completion.

Existing baseline tracker/settings; native 608×1088 detector input. One fresh process at a time, OpenCV one thread, ORT/container CPU budgets 1/2/4. Each setting has three repeats; frames 1–50 warm up and only 51–150 are measured. FPS includes JPEG read/decode, detector and track update/box filtering, excluding output serialization and video drawing. Each median FPS is the median of three repeat throughputs, not reciprocal median latency.

| Model | Precision | Threads / CPU quota | Median repeat FPS | End-to-end p50 ms | End-to-end p95 ms | Peak RSS MiB (max repeat) | Model MiB | >=25 FPS |
|---|---|---:|---:|---:|---:|---:|---:|---|
| nano | fp32 | 1 | 11.43 | 86.33 | 90.51 | 153.3 | 3.48 | False |
| nano | fp32 | 2 | 18.47 | 53.81 | 55.36 | 153.7 | 3.48 | False |
| nano | fp32 | 4 | 26.34 | 35.98 | 39.03 | 153.8 | 3.48 | True |
| tiny | fp32 | 1 | 3.14 | 316.40 | 336.53 | 203.9 | 19.23 | False |
| tiny | fp32 | 2 | 5.81 | 170.65 | 178.37 | 205.0 | 19.23 | False |
| tiny | fp32 | 4 | 10.11 | 97.78 | 105.89 | 205.6 | 19.23 | False |

## Mean stage latency — milliseconds

| Model | Precision | Threads | Decode | Preprocess | Inference | Postprocess | Tracking/filtering | End-to-end |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| nano | fp32 | 1 | 5.90 | 2.70 | 78.83 | 0.15 | 0.06 | 87.64 |
| nano | fp32 | 2 | 6.14 | 2.75 | 45.19 | 0.15 | 0.06 | 54.30 |
| nano | fp32 | 4 | 5.37 | 2.76 | 29.17 | 0.15 | 0.06 | 37.52 |
| tiny | fp32 | 1 | 5.35 | 2.70 | 310.57 | 0.10 | 0.06 | 318.80 |
| tiny | fp32 | 2 | 5.32 | 2.72 | 163.84 | 0.10 | 0.06 | 172.05 |
| tiny | fp32 | 4 | 5.62 | 2.73 | 92.33 | 0.11 | 0.06 | 100.86 |

## Limits and remaining work

These are Mac M2 Max cores in Docker’s Linux VM, not measurements on an edge board. Peak memory is process VmHWM, including initialization and warm-up; it is not host/VM total RAM. CPU quota is verified from cgroup cpu.max and does not pin physical cores. Repeated images benefit from filesystem cache. Individual repeat FPS, raw frame timings, per-stage mean/p50/p95, model/image hashes and all failed real-time settings remain in the JSON.

The existing ORT quantization import fails because ml_dtypes is missing. A pinned, hash-checked, container-only dependency proposal is documented in `phase-4-dependency.md`; download/install has not been authorized or executed. No INT8 model, speed-up, accuracy delta or “worth it” conclusion is claimed. Further INT8 work requires that dependency, then paired benchmarks and unchanged held-out MOT20 evaluation.

Reproduce the completed FP32 measurements using the existing local image/toolchain:

```sh
docker build --network=none -f Dockerfile.phase4 -t vision-lab:phase4 .
bash scripts/phase4_benchmark.sh fp32
scripts/drun.sh vision-lab:pytools -- python /work/python/report_phase4.py
```
