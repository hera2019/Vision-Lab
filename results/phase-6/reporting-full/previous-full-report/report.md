# Phase 6 — full clean-clone reproduction

**Experiment complete. Fresh-clone acceptance: FAIL.**

Author: Codex / GPT-6 (exact runtime model ID not exposed). Date: 2026-10-07.

Tested source commit: `dcdb81e03533045764468305b8a3b07306f4ab98`. Clone context: True. Fresh evaluator procedure: True. Ground-truth self-test: True.

All FP32 canonical evaluator scores and track hashes equal the frozen reference: True. INT8 scores and track hashes equal the frozen reference: True.

The full driver rebuilt the documented images, regenerated all detection caches, Python/C++ tracking and end-to-end outputs, recomputed reference metrics, recalibrated both fixed INT8 models, ran all 36 paired benchmarks and held-out INT8 evaluations, and regenerated the three failure-case crops. Runs use the original hardened container boundary. All failed criteria remain failed.

| Model | Precision | Threads / CPU quota | Original FPS interval | New median FPS | Within interval |
|---|---|---:|---|---:|---|
| nano | fp32 | 1 | 11.594–11.679 | 11.647 | True |
| nano | fp32 | 2 | 18.638–19.171 | 19.304 | False |
| nano | fp32 | 4 | 26.425–27.816 | 28.134 | False |
| nano | int8 | 1 | 15.070–15.349 | 15.170 | True |
| nano | int8 | 2 | 19.905–21.505 | 21.186 | True |
| nano | int8 | 4 | 24.045–25.992 | 26.029 | False |
| tiny | fp32 | 1 | 3.042–3.196 | 3.189 | True |
| tiny | fp32 | 2 | 5.400–5.829 | 5.983 | False |
| tiny | fp32 | 4 | 9.740–9.896 | 10.298 | False |
| tiny | int8 | 1 | 7.653–8.027 | 8.169 | False |
| tiny | int8 | 2 | 11.658–13.197 | 13.342 | False |
| tiny | int8 | 4 | 18.094–18.517 | 18.952 | False |

Speed acceptance retains the predeclared original three-repeat min/max interval. A faster result outside the interval also fails; the interval is not widened after measurement. Quality equality and valid Git-clone provenance do not override failed speed checks.

Original Phase 3–5 evidence in the main checkout is unchanged. Full-run outputs live in the disposable clone; canonical reference JSON files were archived before overwrite. The historical snapshot smoke report remains separate.

Limitations: Cached Docker build layers are allowed; a cold dependency install is not established. Mac Docker Linux VM speed; no edge hardware or real-camera acceptance. Independent review remains pending; original INT8 failures remain failed.

See the paired JSON for clone tree/commit evidence, per-setting checks and hashes; raw logs and metadata are under `results/phase-6/`.

Archived rerun evidence is under `phase-6/full/`: fresh Phase 3 evaluations,
paired Phase 4 timing/metadata and quality reports, Phase 5 case report, input
preflight, package inventory and Git provenance. All eight source evidence
hashes were checked against these copied files (`phase-6/full/archive-check.json`).
The paired JSON maps original clone paths to the archive paths. Driver exit
code 1 comes from the final failed speed gate after all stages completed,
not a mid-experiment crash. All eight failed medians are above the original
upper bounds. The first Bash compatibility failure is retained separately.
