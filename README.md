# Vision Lab

A CPU-only object-detection and multi-object-tracking study using YOLOX nano/
tiny, C++ ONNX Runtime and ByteTrack. Python handles export, evaluation and
reporting. The supplied checkpoints detect **pedestrians only**; this is not
a vehicle tracker, person-recognition system or finished product.

## Current evidence

| Question | Measured answer |
|---|---|
| Does the C++ tracker reproduce the reference? | Phase 3 accepted: zero MOTA/IDF1 delta on 14 MOT17 model/sequence pairs; 22 end-to-end outputs equal cached C++ tracking. |
| How fast is it? | Four-thread FP32 nano 27.34 FPS, tiny 9.76 FPS on a fixed 608×1088-input benchmark in the M2 Max Docker Linux VM. This includes JPEG decoding through tracking/filtering, excludes drawing/writing and is not edge-board FPS. |
| Is this INT8 scheme worthwhile? | No. Nano loses 56.1002 pp MOT20 MOTA. Tiny speeds up, but loses 1.0635 pp, above the frozen 1.0 pp cap. Both fail. |
| How does it fail? | Documented pillar occlusion 75→107, visible-person correspondence switch 13→22, and small/truncated boundary-target misses. |
| Is fresh-clone reproduction accepted? | Pending full execution. Owner approved committing the complete Phase 3–6 source and evidence on 2026-10-07. Local source-snapshot smoke is a separate, narrower check. |

See [work plan](docs/PLAN.md), [fixed acceptance criteria](docs/01-phase-0-plan.md),
[Phase 3](results/phase-3-tracking.md), [Phase 4](results/phase-4-performance.md),
[Phase 5](results/phase-5-failures.md) and [reproduction record](results/phase-6-reproduction.md).
MOT17 training footage is used for fidelity/development only; MOT20 is held
out. No settings are tuned on MOT20. Negative results remain recorded.

## Requirements and inputs

- Docker Desktop/Engine with Linux CPU containers, Git and a POSIX shell.
  On this Mac the Docker CLI is in `$HOME/.docker/bin`; the scripts add it.
- At least 10 GiB free disk before large runs. The two original video archives
  total roughly 10 GiB; extracted data, models and images need additional space.
- ByteTrack and TrackEval under `external/`, at the revisions recorded in
  [assets.json](assets.json). Clone from the recorded upstream URLs and verify
  the exact revisions; external tracked files must be unchanged.
- Existing exported `models/bytetrack_{nano,tiny}_mot17.onnx` with the recorded
  SHA-256. Original weight URLs and hashes are also in assets.json. Export
  uses `python/export_onnx.py` inside the Python image; Phase 1 raw nano parity
  failure remains a separate historical result.
- MOT17's seven `*-FRCNN` training image copies under `data/MOT17/train/`,
  and all four MOT20 training sequences under `data/MOT20/train/`, with
  `seqinfo.ini`, `img1/` and `gt/gt.txt`. Sources/archive checksums are in
  assets.json. Inputs are not bundled with Git or automatically downloaded.

The preflight checks model hashes, external revisions/clean tracked files,
GT hashes, image counts and a representative image hash. It is not a complete
hash scan of all JPEGs. Use only the original licensed inputs.

## Quick check with installed assets and images

```sh
bash scripts/reproduce.sh smoke
```

This requires the existing `vision-lab:phase4` installed C++ toolchain and
`vision-lab:phase4-pytools` Python image. It rebuilds current C++ sources
offline, checks the environment and synthetic tracker behavior, reproduces
both models' first-50-frame detections/tracks byte for byte, and runs three
four-thread FP32 speed repeats. Results go only to `results/phase-6/`,
`results/phase-6-reproduction.*` and `data/phase-6/`. Repeating smoke replaces
those smoke records, not the earlier Phase 3–5 results. First 50 frames warm
up each benchmark; only the next 100 enter timings. FPS checks use the
original three-repeat min/max intervals without widening them after failure.
This command is a bounded check, not full reproduction or startup timing.

An isolated source snapshot may supply `VL_ASSET_ROOT=/absolute/path/to/the/
existing/project`. Smoke then mounts only models, external sources, MOT17,
MOT20 and frozen Phase 3 caches as read-only subdirectories. It never mounts
the whole home or Docker socket. The [snapshot helper](scripts/phase6_snapshot.sh)
captures source hashes and distinguishes the actual HEAD clone from this
working-source snapshot. It does not commit or overlay the clone.

## Full reproduction from committed source

Once this complete source revision is committed and independently cloned,
stage the recorded inputs inside the clone, then run:

```sh
VL_DISPOSABLE_CLONE=1 VL_BUILD_NETWORK=default bash scripts/reproduce.sh full
```

Full mode requires a clean Git checkout and an explicit disposable-clone
declaration at entry. `default` explicitly enables
network only for dependency image builds; every experiment container remains
offline and hardened. With all required build layers cached, use
`VL_BUILD_NETWORK=none`. Root image builds use the pinned Ubuntu digest and
SHA-checked ORT release. Python versions are fixed; Ubuntu apt packages and
Python transitive dependencies are not a complete lockfile, so a genuinely
fresh dependency build may drift and must be measured rather than assumed
equivalent. The separate INT8 dependency wheel is hash-pinned.

The command builds images, archives canonical reference reports under
`results/phase-6/`, then runs the original detection caches, Python/C++
tracking, full end-to-end evaluation, all paired FP32/INT8 benchmarks and
held-out INT8 quality, followed by failure crops. It writes new experiment
outputs inside that disposable clone. Full execution is substantially longer
than smoke and is currently **unexecuted**, not an accepted reproduction.
The earlier Phase 0–2 HEAD clone lacked this source; that failure stays in the
historical report. Clone the complete source commit for this command. No
workaround snapshot counts as passing that gate.

Full checks compare canonical evaluator scores and track hashes against the
archived reference, and every speed median against its original repeat
interval. A failed check remains failed. The historical Phase 3 human report
is retained as reference; a new Phase 3 canonical evaluation file is scored.
Reproduction does not resolve INT8 failures or guarantee continuous IDs.

## Container boundary

Every run uses [scripts/drun.sh](scripts/drun.sh): offline, ordinary UID,
all capabilities dropped, no privilege escalation, read-only project/root,
explicit writable outputs, 1 GiB temporary filesystem, 6 GiB memory and
512-process cap. Benchmarks additionally pair CPU quota with ORT threads.
The [safety report](results/phase-4/container-safety.md) distinguishes measured
protections from absolute guarantees. No GUI access is needed.

## Learning and licensing

[Bilingual walkthroughs](docs/walkthrough/) explain each phase for beginners.
[Changes](docs/CHANGES.md) name the actual contributors; [issues](docs/ISSUES.md)
retain failures. Commit/push requires the owner's explicit instruction.

Our code uses [LICENSE](LICENSE); third-party terms are in
[docs/LICENSES.md](docs/LICENSES.md). MOT17/MOT20 images, clips and crops retain
MOTChallenge attribution and CC BY-NC-SA 3.0 non-commercial research terms.
Models and datasets are not redistributed in this repository. Mean-shift is
a deferred optional bonus; GPU/NPU, training, multi-camera and appearance
re-identification are outside the current scope.
