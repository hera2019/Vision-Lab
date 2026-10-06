# Phase 4 — controlled speed and memory

Date: 2026-10-06. Author: Codex / GPT-6 (exact runtime model ID not exposed).

Status: **phase-4-measurements-complete**. All predeclared measurements finished; failed gates remain failed. Independent review is pending.

**Conclusion: Neither INT8 model meets the fixed usefulness gate at any tested budget. nano MOTA loss 56.1002 pp; tiny MOTA loss 1.0635 pp. The FP32 baseline is retained.**

Existing baseline tracker/settings; native 608×1088 detector input. One fresh process at a time, OpenCV one thread, ORT/container CPU budgets 1/2/4. Each setting has three repeats; frames 1–50 warm up and only 51–150 are measured. FPS includes JPEG read/decode, detector and track update/box filtering, excluding output serialization and video drawing. Each median FPS is the median of three repeat throughputs, not reciprocal median latency.

| Model | Precision | Threads / CPU quota | Median repeat FPS | End-to-end p50 ms | End-to-end p95 ms | Peak RSS MiB (max repeat) | Model MiB | >=25 FPS |
|---|---|---:|---:|---:|---:|---:|---:|---|
| nano | fp32 | 1 | 11.61 | 85.17 | 89.16 | 153.2 | 3.48 | False |
| nano | fp32 | 2 | 19.09 | 52.42 | 54.49 | 153.7 | 3.48 | False |
| nano | fp32 | 4 | 27.34 | 35.97 | 38.69 | 153.9 | 3.48 | True |
| nano | int8 | 1 | 15.28 | 65.01 | 68.82 | 197.8 | 1.33 | False |
| nano | int8 | 2 | 20.56 | 46.71 | 50.28 | 200.8 | 1.33 | False |
| nano | int8 | 4 | 25.46 | 38.57 | 44.55 | 201.4 | 1.33 | True |
| tiny | fp32 | 1 | 3.18 | 312.34 | 354.11 | 203.9 | 19.23 | False |
| tiny | fp32 | 2 | 5.66 | 172.53 | 210.16 | 205.1 | 19.23 | False |
| tiny | fp32 | 4 | 9.76 | 98.64 | 126.12 | 205.7 | 19.23 | False |
| tiny | int8 | 1 | 7.81 | 123.64 | 144.34 | 220.7 | 5.18 | False |
| tiny | int8 | 2 | 13.00 | 76.38 | 93.64 | 222.5 | 5.18 | False |
| tiny | int8 | 4 | 18.25 | 53.97 | 58.00 | 221.4 | 5.18 | False |

## Mean stage latency — milliseconds

| Model | Precision | Threads | Decode | Preprocess | Inference | Postprocess | Tracking/filtering | End-to-end |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| nano | fp32 | 1 | 5.20 | 2.70 | 77.90 | 0.14 | 0.06 | 86.00 |
| nano | fp32 | 2 | 5.42 | 2.70 | 44.42 | 0.15 | 0.06 | 52.74 |
| nano | fp32 | 4 | 5.27 | 2.75 | 28.56 | 0.15 | 0.05 | 36.79 |
| nano | int8 | 1 | 5.19 | 2.68 | 57.02 | 0.45 | 0.31 | 65.65 |
| nano | int8 | 2 | 5.34 | 2.68 | 39.68 | 0.45 | 0.31 | 48.46 |
| nano | int8 | 4 | 5.50 | 2.77 | 30.73 | 0.46 | 0.31 | 39.78 |
| tiny | fp32 | 1 | 5.92 | 2.78 | 309.93 | 0.15 | 0.06 | 318.85 |
| tiny | fp32 | 2 | 5.93 | 2.77 | 168.96 | 0.10 | 0.06 | 177.84 |
| tiny | fp32 | 4 | 5.41 | 2.76 | 93.74 | 0.10 | 0.06 | 102.07 |
| tiny | int8 | 1 | 5.68 | 2.80 | 119.06 | 0.12 | 0.09 | 127.75 |
| tiny | int8 | 2 | 6.34 | 2.68 | 70.27 | 0.12 | 0.08 | 79.50 |
| tiny | int8 | 4 | 5.35 | 2.76 | 46.37 | 0.12 | 0.08 | 54.68 |

## Held-out MOT20 — unchanged procedures and A1 settings

Four complete sequences, 8,931 frames per model. Calibration uses MOT17 only. FP32 baseline hashes checked against the accepted Phase 3 result. Every number keeps its evaluator label; no MOT20 tuning or post-result recalibration.

| Evaluator | Model | Sequence | FP32 MOTA | INT8 MOTA | ΔMOTA pp | FP32 IDF1 | INT8 IDF1 | ΔIDF1 pp |
|---|---|---|---:|---:|---:|---:|---:|---:|
| motmetrics | nano | MOT20-01 | 59.1444 | 0.2114 | -58.9331 | 57.2644 | 0.6104 | -56.6539 |
| motmetrics | nano | MOT20-02 | 57.1105 | 0.1028 | -57.0078 | 48.2232 | 0.4994 | -47.7238 |
| motmetrics | nano | MOT20-03 | 63.9598 | -0.2021 | -64.1619 | 65.5991 | 3.5926 | -62.0066 |
| motmetrics | nano | MOT20-05 | 51.8111 | -0.0726 | -51.8837 | 44.9316 | 0.3530 | -44.5785 |
| motmetrics | nano | OVERALL | 56.0207 | -0.0795 | -56.1002 | 51.3699 | 1.3235 | -50.0464 |
| TrackEval | nano | MOT20-01 | 64.2124 | 0.2315 | -63.9809 | 59.1179 | 0.6006 | -58.5173 |
| TrackEval | nano | MOT20-02 | 61.7176 | 0.1351 | -61.5825 | 49.5971 | 0.4983 | -49.0988 |
| TrackEval | nano | MOT20-03 | 67.7276 | 0.0175 | -67.7101 | 67.0016 | 3.6033 | -63.3983 |
| TrackEval | nano | MOT20-05 | 59.9611 | 0.0210 | -59.9401 | 47.0982 | 0.3525 | -46.7458 |
| TrackEval | nano | OVERALL | 62.4221 | 0.0393 | -62.3828 | 53.3148 | 1.3243 | -51.9905 |
| motmetrics | tiny | MOT20-01 | 63.4927 | 61.7816 | -1.7111 | 59.8191 | 62.2319 | +2.4129 |
| motmetrics | tiny | MOT20-02 | 64.4318 | 63.5619 | -0.8698 | 55.7506 | 55.3893 | -0.3613 |
| motmetrics | tiny | MOT20-03 | 66.9599 | 66.6430 | -0.3169 | 72.3134 | 72.5872 | +0.2739 |
| motmetrics | tiny | MOT20-05 | 57.3416 | 55.8893 | -1.4523 | 54.0741 | 51.1783 | -2.8959 |
| motmetrics | tiny | OVERALL | 61.0752 | 60.0117 | -1.0635 | 59.4906 | 57.9299 | -1.5608 |
| TrackEval | tiny | MOT20-01 | 70.4831 | 68.9431 | -1.5400 | 62.3031 | 64.8607 | +2.5576 |
| TrackEval | tiny | MOT20-02 | 69.5241 | 68.6582 | -0.8660 | 57.3878 | 56.9960 | -0.3919 |
| TrackEval | tiny | MOT20-03 | 71.2260 | 70.6154 | -0.6105 | 74.0083 | 74.1847 | +0.1764 |
| TrackEval | tiny | MOT20-05 | 66.0873 | 64.5571 | -1.5301 | 56.8331 | 53.8044 | -3.0287 |
| TrackEval | tiny | OVERALL | 68.0535 | 66.8680 | -1.1855 | 61.8822 | 60.2407 | -1.6414 |

TrackEval HOTA and identity switches, motmetrics identity switches/FP/FN, coverage and track hashes are retained in the JSON.

## Fixed INT8 usefulness gate

Worth it requires paired end-to-end speed-up ≥1.3× AND overall motmetrics MOT20 MOTA loss ≤1.0 pp. Quality is measured at four threads; the separate 50-frame 1/4-thread consistency check is limited evidence for transfer to other budgets.

| Model | Threads | End-to-end speed-up | MOT20 MOTA loss pp | Speed pass | Accuracy pass | Worth it |
|---|---:|---:|---:|---|---|---|
| nano | 1 | 1.316× | 56.1002 | True | False | False |
| nano | 2 | 1.077× | 56.1002 | False | False | False |
| nano | 4 | 0.931× | 56.1002 | False | False | False |
| tiny | 1 | 2.461× | 1.0635 | True | False | False |
| tiny | 2 | 2.297× | 1.0635 | True | False | False |
| tiny | 4 | 1.871× | 1.0635 | True | False | False |

## Quantization, safety and retained failures

The owner approved ml_dtypes 0.6.0; its hash-checked binary wheel was installed into a separate image with no other package upgrades. Static QDQ uses Conv-only S8S8, per-channel weights and MinMax over the same 112 MOT17 images. Native-shaped outputs are finite and original FP32 model hashes remain unchanged. Model/node counts, hashes, calibration sample counts and dependency versions are in the JSON.

An initial calibration failed: ORT 1.30 cleared each capped intermediate batch without computing/merging its ranges. Raising the storage cap from 1 to 128 retains all 112 fixed observations; reader count is asserted. No input, quantization scheme, score threshold or memory limit changed. Initial log/JSON remain. The initial safety probe also failed an overly narrow interface-name assumption; down kernel tunnel devices were inspected, and actual routing/connectivity checks confirm isolation. Runtime protections were unchanged.

Runtime protections are documented in `phase-4/container-safety.md` / `.json`: offline, non-root, zero capabilities, no privilege escalation, read-only root/project except selected outputs, 1 GiB nosuid/nodev/noexec tmpfs, 6 GiB RAM, 512-process cap, no Docker socket. Only approved image builds use network.

The read-only [INT8 diagnostic](phase-4-int8-diagnostic.md) uses MOT17-02 frames 1/51/150. Official preprocessing matches the reconstructed C++ formula within 4.77e-7; preprocessed FP32 and original FP32 raw outputs are identical on all three frames for both models. Nano INT8 produces far more post-NMS boxes, including when runtime optimization is disabled. This localizes the observed issue to the INT8 path on this slice, without identifying a specific operator or establishing its general root cause. No model/settings changes or replacement quality score were made.

## Limits and remaining work

These are Mac M2 Max cores in Docker’s Linux VM, not measurements on an edge board. Peak memory is process VmHWM, including initialization and warm-up; it is not host/VM total RAM. CPU quota is verified from cgroup cpu.max and does not pin physical cores. Repeated images benefit from filesystem cache. Individual repeat FPS, raw frame timings, per-stage mean/p50/p95, model/image hashes and all failed real-time settings remain in the JSON.

Original FP32-only runs/report are retained as `phase-4-performance-fp32.*`. Paired runs are used for speed ratios to reduce ordering bias. This phase does not repair the owner-reported identity failures. Failure-category documentation and fresh-clone reproduction remain later work. Package inventory checks confirm that only ml_dtypes 0.6.0 was added; original packages retain their versions. Model ledger hashes/sizes and Python/shell syntax checks pass. The single-command wrapper is syntax-checked; its individual stages were run in this workspace, not in a fresh clone.

Reproduce using the existing baseline models/data, pinned external evaluators and local base images:

```sh
docker build --network=none -f Dockerfile.phase4 -t vision-lab:phase4 .
docker build -f Dockerfile.phase4-pytools -t vision-lab:phase4-pytools .
bash scripts/phase4_experiment.sh
```
