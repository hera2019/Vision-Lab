# Execution guide and audit history

Reader summary: [README](../README.md). This guide retains the earlier detailed
execution/history notes. As of 2026-10-08, [Opus's ruling](reviews/phase-4-6-opus.md)
supersedes the older headline interpretation: quality reproduces exactly;
speed differs by -2.73% to +5.76% across both full reruns. Strict historical
interval failures remain recorded; this spread is not a new acceptance rule.
R3 has a reviewer ruling; a future prospective timing protocol remains unwritten.
The separate [post-hoc nano investigation](PHASE4_REPAIR.md) does not replace
the original INT8 artifacts or results.

That investigation is now [complete](../results/phase-4-nano-repair.md): a
weight-only floating control restores quality within 0.705 pp on one full
MOT20 run, but fails the 1.3x speed rule at every budget. It is separate from
the earlier complete-clone reproductions below and has not undergone a new
clean-clone experiment or final Opus review.

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
| Is fresh-clone reproduction accepted? | Full clean-clone experiment complete at `dcdb81e`: FP32/INT8 scores and track hashes reproduce exactly. Strict speed check fails in 8/12 configurations, all above the old interval. Overall acceptance remains FAIL. |

See [work plan](PLAN.md), [fixed acceptance criteria](01-phase-0-plan.md),
[Phase 3](../results/phase-3-tracking.md), [Phase 4](../results/phase-4-performance.md),
[Phase 5](../results/phase-5-failures.md), [full reproduction](../results/phase-6-full-reproduction.md)
and [historical snapshot check](../results/phase-6-reproduction.md).
MOT17 training footage is used for fidelity/development only; MOT20 is held
out. No settings are tuned on MOT20. Negative results remain recorded.

## Requirements and inputs

- Docker Desktop/Engine with Linux CPU containers, Git and a POSIX shell.
  On this Mac the Docker CLI is in `$HOME/.docker/bin`; the scripts add it.
- At least 10 GiB free disk before large runs. The two original video archives
  total roughly 10 GiB; extracted data, models and images need additional space.
- ByteTrack and TrackEval under `external/`, at the revisions recorded in
  [assets.json](../assets.json). Clone from the recorded upstream URLs and verify
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
the whole home or Docker socket. The [snapshot helper](../scripts/phase6_snapshot.sh)
captures source hashes and distinguishes the actual HEAD clone from this
working-source snapshot. It does not commit or overlay the clone.

## Full reproduction from committed source

Clone the complete source revision independently, stage the recorded inputs
inside the clone, then run:

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
than smoke. Full execution completed from clean source commit `dcdb81e` on
2026-10-07: all canonical evaluator scores and track hashes reproduce exactly,
including the INT8 failures. Only 4/12 speed medians are inside the original
repeat intervals; the other eight are faster but above their upper bounds.
The driver therefore exits 1 at its final numerical gate after completing all
stages, and overall acceptance remains FAIL. Raw rerun evidence is archived
under `results/phase-6/full/`; original Phase 3–5 records remain unchanged.
The earlier Phase 0–2 HEAD clone lacked this source; that failure stays in the
historical report. Clone the complete source commit for this command. No
workaround snapshot counts as passing that gate.

Full checks compare canonical evaluator scores and track hashes against the
archived reference, and every speed median against its original repeat
interval. A failed check remains failed. The historical Phase 3 human report
is retained as reference; a new Phase 3 canonical evaluation file is scored.
Reproduction does not resolve INT8 failures or guarantee continuous IDs.
Cold dependency installation remains unverified. The later independent review
of existing implementation/evidence is described below.

Reporting follow-up: the [bounded audit](../results/phase-6-audit.md) verifies
existing raw evidence; [reporting fixes](../results/phase-6-reporting-fixes.md)
make the full command generate current paired reports automatically, with
run/source identity and explicit incomplete status if a build fails. Previous
reports are kept under `results/phase-6/previous-full-report/`. Source context
requires a clean standalone checkout matching its tracked upstream revision;
this is not independent reviewer approval. Thirteen reporting contracts pass.
The changed entry point has now undergone a complete clean-clone experiment at
`e3c4a83`: [full reporting verification](../results/phase-6-reporting-full-verification.md)
confirms automatic current reports, fresh evaluation and exact quality/hash
reproduction. Speed consistency passes 5/12 and fails 7/12 (two below and five
above the old intervals); overall acceptance remains FAIL. Historical results
and fixed speed intervals stay unchanged. The
[independent review](reviews/phase-4-6.md), explicitly owner-authorized on
2026-10-08, passes implementation/evidence within the single-run reporting
scope. R1/R2/R4 are resolved; no new actionable defect was established. R3
timing-method review remains open and experimental acceptance stays FAIL.
The reviewer independently checked existing arithmetic and hashes without new
inference, rescoring, visual inspection or a full experiment. This is a Codex
agent verdict, not an Opus verdict or evidence of device/product readiness.

## Container boundary

Every run uses [scripts/drun.sh](../scripts/drun.sh): offline, ordinary UID,
all capabilities dropped, no privilege escalation, read-only project/root,
explicit writable outputs, 1 GiB temporary filesystem, 6 GiB memory and
512-process cap. Benchmarks additionally pair CPU quota with ORT threads.
The [safety report](../results/phase-4/container-safety.md) distinguishes measured
protections from absolute guarantees. No GUI access is needed.

## Learning and licensing

[Bilingual walkthroughs](walkthrough/) explain each phase for beginners.
[Changes](CHANGES.md) name the actual contributors; [issues](ISSUES.md)
retain failures. Commit/push requires the owner's explicit instruction.

Our code uses [LICENSE](../LICENSE); third-party terms are in
[docs/LICENSES.md](LICENSES.md). MOT17/MOT20 images, clips and crops retain
MOTChallenge attribution and CC BY-NC-SA 3.0 non-commercial research terms.
Models and datasets are not redistributed in this repository. Mean-shift is
a deferred optional bonus; GPU/NPU, training, multi-camera and appearance
re-identification are outside the current scope.
