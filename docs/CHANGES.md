# Changes and attribution

Append new rows at the end. "Actual author" is the agent and model that made the
change, as that agent identifies itself.

| Date | Actual author | Files / scope | Reason and verification |
|---|---|---|---|
| 2026-10-06 | Claude / Opus 5.5 | `docs/PLAN.md`, `docs/01-phase-0-plan.md`, `docs/LICENSES.md`, `Dockerfile`, `cpp/` (env_check), `LICENSE` | Phase 0: test plan with fixed criteria, license review, CPU Docker image (ORT 1.30.0 SHA-256 pinned). `env_check` passed; see `results/phase-0-environment.md`. |
| 2026-10-06 | Claude / Opus 5.5 | `python/` (export, parity), `Dockerfile` (pytools), `assets.json`, `results/phase-1-*` | Phase 1: ONNX export of nano/tiny. Parity: tiny pass; nano fails the 1e-3 raw tolerance (1.18e-3), kept as a failure with investigation. |
| 2026-10-06 | Claude / Opus 5.5 | `cpp/src/detector.*`, `cpp/src/detect_frames.cpp`, `python/check_cpp_detector.py`, `python/draw_sample.py`, `scripts/phase2_detector_parity.sh`, `results/phase-2-*` | Phase 2: C++ detector. Matches Python reference on 20 frames for both models (counts equal, min IoU 0.99998, max score diff 4.8e-6). |
| 2026-10-06 | Claude / Opus 5.5 | `docs/walkthrough/phase-0..2.md` | Bilingual beginner walkthroughs requested by the owner. |
| 2026-10-06 | Claude / Opus 5.5 | `docs/PROJECT_RULES.md`, `AGENTS.md`, `CLAUDE.md`, `docs/CHANGES.md`, `docs/ISSUES.md`, `docs/SOL6_TASKS.md`, `docs/01-phase-0-plan.md` (amendment A1) | Handoff to an executor: shared rules, ledgers, Phase 3 taskbook. Amendment A1 pre-registers MOT20 tracker settings before any MOT20 run. |
