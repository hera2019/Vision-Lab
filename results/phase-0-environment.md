# Phase 0 — Environment

Date: 2026-10-06 · Result: **pass**

Criterion (from [the test plan](../docs/01-phase-0-plan.md)): `env_check` reports
ONNX Runtime 1.30.0 with `CPUExecutionProvider`, and an OpenCV JPEG round-trip succeeds.

## Command

```bash
docker build -t vision-lab:dev .
docker run --rm vision-lab:dev
```

## Observed

Machine-readable output: [`phase-0-env-check.json`](phase-0-env-check.json)

| Item | Value |
|---|---|
| Host | Apple Silicon Mac, 32 GB RAM, Docker Desktop 29.8.2 |
| Docker VM | linux/arm64, 12 vCPU, ~7.7 GiB memory |
| Base image | `ubuntu:24.04` pinned by digest (Ubuntu 24.04.5 LTS) |
| Compiler / build | g++ 13.3.0, CMake 3.28.3, Ninja |
| ONNX Runtime | 1.30.0 (linux-aarch64 prebuilt, SHA-256 verified) — providers: `CPUExecutionProvider` only |
| OpenCV | 4.6.0 (Ubuntu per-module packages) |
| Eigen | 3.4.0 |
| Image size | 1.41 GB |

## Notes

- Ubuntu's per-module OpenCV `-dev` packages do not ship `OpenCVConfig.cmake`;
  the first build failed at `find_package(OpenCV)`. Fixed by locating headers and
  libraries directly rather than installing the full `libopencv-dev`.
- apt package versions are not pinned; the versions above are what the pinned
  base image resolved on this date.
