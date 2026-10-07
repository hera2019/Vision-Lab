# Container protections — inspected and probed

Date: 2026-10-06. Actual experiment runs use `scripts/drun.sh`.
Probe results: `container-safety.json`; initial probe failure is retained.

| Protection | Actual configuration and observation |
|---|---|
| Offline execution | `--network none`; no active non-loopback interface or IPv4 route; reserved external connection probe returns ENETUNREACH. |
| Non-root | Caller UID/GID, measured UID 502 / GID 20. |
| No added privilege | `--cap-drop ALL`, measured CapEff zero; `no-new-privileges`, measured NoNewPrivs 1. |
| Read-only filesystem | Root filesystem read-only; `/etc` write probe denied. |
| Project scope | `/work` project mount read-only; write probe denied. Only explicitly selected `results` and `data/phase-4` are writable in this run. No whole-home mount. |
| Temporary files | 1 GiB tmpfs; measured nosuid/nodev/noexec; direct script execution denied. An interpreter can still read code, so noexec is not a general ban on executing Python. |
| Resource bounds | Measured memory.max 6 GiB, pids.max 512. Benchmark CPU quotas 1/2/4 match ORT threads; inspected probe quota 4. Calibration is not a speed benchmark. |
| No Docker control | `/var/run/docker.sock` absent; no privileged container flag or host-network mode. |
| Cleanup | `--rm` removes each stopped container; intentionally written result/model files persist in the selected project output directories. |

Only the approved dependency image build needs network access. It installs
`ml_dtypes==0.6.0` with wheel hashes, `--no-deps` and `--only-binary` into a
separate local image. No host installation or dataset upload is involved.
The approved build succeeded and the quantization import passes.

The first probe wrongly required the interface-name list to contain only
`lo`; this VM kernel also creates down tunnel devices. Follow-up inspected
flags, route table and a real blocked connection. Runtime flags were not
weakened. The failed assertion and exact device list stay in
`container-safety-first-attempt.json`.

These protections restrict access; they are not a proof against every kernel
or Docker vulnerability. Readable project data and the explicit writable
output directories remain accessible to the container by design.
