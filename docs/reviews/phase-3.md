# Review — Phase 3 (tracking)

Reviewer: Claude / Opus 5.5 · 2026-10-06 · Executor: Codex / GPT-6 (owner's "Sol 6.1")

**Verdict: accepted.** Both fixed criteria pass and the key claims reproduce
independently. Three follow-ups below are non-blocking.

## Independent checks (not using the executor's comparison or scoring code)

| Claim | Reviewer check | Result |
|---|---|---|
| Python reference is the unmodified upstream tracker | Read `python/track_reference.py`, `python/phase3_common.py` | Imports `yolox.tracker.byte_tracker.BYTETracker`; per-sequence overrides match `mot_evaluator.py`; MOT20 uses A1 defaults; empty frames skip `update()`; box filter matches |
| 3a: C++ = Python tracker | Own parser over all 22 output pairs (2,064,047 rows) | Frame, ID and all box coordinates identical in every row. 3 rows differ in score by 0.01 (see F3) |
| 3b: within ±1.0 of published | Own motmetrics script, ByteTrack's procedure | nano 69.2325 MOTA / 66.8414 IDF1; tiny 77.1347 / 71.5651, identical to the report, for both Python and C++ tracks |
| End-to-end = cache-then-track | `cmp` on all 22 files | 0 differ |
| Phase 0–2 code and results untouched | `git diff` on detector sources, earlier results, test plan | No changes |
| Hardened runs only | `grep 'docker run' scripts/` | Only `drun.sh` |

Negative records are kept (I-7 threshold fixture failure, I-8 driver EOF,
I-9 tmpfs exec), and attribution is honest about the model identity.

## Follow-ups

- **F1 · Walkthrough below the agreed standard.** `docs/walkthrough/phase-3.md`
  has ~300 words against 1,150–1,850 for phases 0–2. It omits most new terms
  (motmetrics vs TrackEval, ID switch, behavioural fixture, determinism, the
  seen-vs-held-out gap) and the result tables. Rewrite to the PROJECT_RULES standard.
- **F2 · Tracker readability.** `cpp/src/tracker/tracker.cpp` is correct but
  compressed (several statements per line, aliases such as `T`, `V8`), unlike
  `detector.cpp`. This is portfolio code that will be read in interviews.
  Reformat without changing behaviour; acceptance: all 22 outputs byte-identical
  to the current ones and the edge-case fixtures still pass.
- **F3 · Report inconsistency.** I-5 states the maximum score difference is
  2.87e-8, but the comparison table shows 0.01 for nano MOT20-02 and tiny
  MOT20-05 (3 rows total, e.g. Python 0.70 vs C++ 0.69). This is two-decimal
  rounding of a score lying on a .xx5 boundary (NumPy float32 rounding vs C
  `printf`). It is harmless (scores are not used by either evaluator), but I-5
  and the report should say so.

## Observations for Phase 4 and the write-up

- Held-out drop: nano MOTA 69.2 → 56.0, IDF1 66.8 → 51.4 (MOT17 seen → MOT20
  held-out, motmetrics); tiny 77.1 → 61.1, 71.6 → 59.5. Part of this is MOT20
  being far more crowded (domain shift), so the gap must not be attributed to
  training-set exposure alone.
- motmetrics (ByteTrack's procedure) and TrackEval disagree substantially on
  MOT20 (nano MOTA 56.0 vs 62.4) because TrackEval removes distractor classes.
  Every number must keep its evaluator label.
- Tracking accuracy runs used 4 ORT threads concurrently, so the logged timings
  are not benchmarks. Phase 4 needs a separate, controlled run.
