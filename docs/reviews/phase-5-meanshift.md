# Review — mean-shift baseline (Opus)

Reviewer: Claude / Opus 5.5 · 2026-10-08 · Executor: Codex / GPT-6

**Verdict: accepted.**

## Checks

| Point | Reviewer check | Result |
|---|---|---|
| Ground truth used only at birth | Read `python/meanshift_baseline.py` | `seed_rows` keeps each person's first valid row (class 1, considered); `del gt` before the frame loop; nothing later reads annotations |
| Evaluator adapter | Independent motmetrics re-score of the mean-shift tracks, separate from the executor's TrackEval adapter | MOTA −254.138 / IDF1 3.101, identical to the report's motmetrics row |
| Protocol matches the test plan | Phase 0 plan: "initialised from first-appearance ground truth boxes, scored with the same TrackEval settings" | Yes; no retirement rule was specified, and none was added |

## Reviewer diagnostic: stale boxes or drift?

Mean-shift never retires a track, so boxes stay after a person leaves. To
separate that from drift, each track was cut after its person's last
ground-truth frame. This uses annotation information no real tracker has, so
it is an **oracle diagnostic, not a result**:

| Variant (motmetrics, MOT20 train) | MOTA | IDF1 | False positives | Misses | ID switches |
|---|---:|---:|---:|---:|---:|
| As run | −254.1 | 3.1 | 3,046,542 | 956,072 | 15,485 |
| Oracle retirement | −72.1 | 3.9 | 893,107 | 1,053,672 | 5,666 |

Stale boxes cause about 70% of the false positives, but even with perfect
retirement MOTA stays at −72 and misses rise: windows leave their targets
early. Drift, not only missing retirement, explains the gap to the detector-based
trackers. This supports the report's wording.
