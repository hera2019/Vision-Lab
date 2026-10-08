# Review — Phases 4–6 (Opus)

Reviewer: Claude / Opus 5.5 · 2026-10-08 · Executor: Codex / GPT-6 ("Sol 6.1")
Scope: branch `codex/vision-lab-reproduction` at `e161ef4` plus the uncommitted
working tree on that date. Complements the separate Codex review in
[phase-4-6.md](phase-4-6.md); this one is the review lead's verdict.

**Verdict: measurements accepted; two conclusions need correction before the
work is presented (R-A, R-B); the README is not yet presentable (R-C).**

## Independent checks

| Claim | Reviewer check | Result |
|---|---|---|
| Fixed criteria and Phase 0–2 files unchanged | `git diff 6f0e68f` on the test plan, detector sources, Phase 0–2 results, `drun.sh`, PROJECT_RULES | No changes |
| 4-thread FPS (nano FP32 27.34, INT8 25.46; tiny FP32 9.76, INT8 18.25) | Recomputed from raw per-frame CSVs (frames 51–150, median of 3 repeats) | Identical |
| INT8 nano MOT20 collapse (MOTA −0.08, IDF1 1.32) | Own motmetrics re-score of the INT8 tracks | Identical |
| Calibration used MOT17 only; one INT8 scheme, run once on MOT20 | `assets.json`, `python/quantize_phase4.py` | Yes: static QDQ, S8S8, per-channel, MinMax, Conv only, 112 MOT17 inputs |

## Findings

### R-A · The INT8 nano diagnosis looked at the wrong data (open)

On MOT20 the INT8 nano model emits almost nothing: 116 track rows on MOT20-01
against 15,405 for FP32; over all of MOT20, 17,426 matches against 773,259. The
failure is **missed detections**, not extra ones. The diagnosis examined three
MOT17 frames, where the INT8 model shows the *opposite* symptom (2–3× more
candidate boxes). So it never observed the failure it was meant to explain.

The current wording ("this INT8 scheme is not worthwhile") is true for the
artifact measured, but presenting a 56-point collapse without a cause reads as a
broken pipeline. Proposed next step:

1. Diagnose **read-only** on a few MOT20 frames (failure analysis, not tuning):
   score distributions FP32 vs INT8, and which quantized tensor saturates
   (MinMax ranges from MOT17 vs MOT20 activations, especially the output head).
2. Any remedy (e.g. keep the detection-head convolutions in FP32, asymmetric
   U8 activations, percentile/entropy calibration) is selected **on MOT17 data
   only**, written down before a single MOT20 run, and reported as a post-hoc
   variant. The original INT8 failure stays on record.

### R-B · The Phase 6 speed gate was mis-specified (decision by reviewer)

The plan asked for headline numbers "within run-to-run variance". The executor
operationalised this as "inside the min–max of the original three repeats".
Three repeats from one session measure *within-session* spread, not
*between-run* variance. The full rerun lands within **−0.3% to +5.5%** of the
original medians (e.g. nano FP32 4 threads 27.34 → 28.13 FPS), and quality
metrics and track hashes reproduce **exactly**.

Ruling: as with Phase 1, the strict-gate failure stays on record and is not
re-scored. The headline wording changes from "overall acceptance FAIL" to:
*quality reproduces exactly; speed reproduces within +6%; the original speed gate
was too narrow (see this review)*. Future speed claims carry the observed
between-run spread.

### R-C · README and results are not presentable yet

The README (~1,250 words) is dominated by process detail (gate IDs, reporting
contracts, review rounds); its key results are hard to find. `results/` holds
~70 files at the top level. Needed: a short README for a reader (what, headline
table, one demo frame, one honest limitation, how to reproduce), with the audit
trail one link away; and an index of results grouped by phase.

## What is solid

- Speed table with stage breakdown, p50/p95, peak memory and CPU quota per budget.
- FP32 nano meets the pre-registered real-time bar (≥ 25 FPS) at 4 threads only;
  tiny never does in FP32.
- Tiny INT8: 1.9–2.5× faster, MOTA −1.06 (cap 1.0). A genuine near-miss, honestly reported.
- Failure cases are tied to frames and ground-truth IDs; the owner's two
  observations (75→107, 3→4→18) were investigated rather than explained away.
- Negative records and attribution are kept throughout.

Mean-shift baseline: deferred by the executor (bonus item).

## Follow-up check · 2026-10-08 (light, budget-limited)

- **R-A resolved.** Diagnosis now covers the failure itself (coarse stem
  activation step 0.716; negative activations rounding to zero; error growing
  into the head). The variant was selected on MOT17 only and run once on MOT20:
  MOTA 55.32 (−0.70) but speed 0.97–1.03×, so INT8 nano is still not worthwhile.
  The original failure stays on record. Process and wording accepted.
- **R-B resolved.** Between-run speed spread is reported (−2.73% to +5.76%);
  the strict-interval failure is retained and explained.
- **R-C resolved at first reading.** README is 442 words and leads with a results
  table; `results/README.md` indexes the evidence.
- Not re-verified in this pass: the new numbers above were read from the
  executor's reports, not recomputed; walkthroughs 4–6 were not reviewed.

## Final check · 2026-10-08 (full, after the weekly budget reset)

The items left open by the light follow-up are now verified independently:

- Repaired nano on MOT20: own motmetrics re-score of
  `data/phase-4-repair/tracks/MOT20/weight-control` gives MOTA 55.3158 /
  IDF1 51.8449, identical to the report. Only this one variant exists for MOT20.
- Selection order: candidate list fixed at 01:21:51 and MOT20 tracks written at
  01:26:07 on 2026-10-08; the three candidates were scored on MOT17 only.
- Between-run speed spread: recomputed from the raw per-frame CSVs of the
  original run and both full reruns (12 settings × 2 reruns): −2.73% to +5.76%.
- Walkthroughs 3–6: bilingual, sectioned, terms defined, result tables included.
  Denser than phases 0–2, but they meet the PROJECT_RULES standard.
- Pre-merge hygiene: no files from `data/`, `models/` or `external/`; largest
  file 420 KB; no credentials found; demo image carries MOTChallenge attribution.

**Final verdict: Phases 3–6 accepted.** Retained failures (Phase 1 nano raw
tolerance, original INT8 gates, strict speed intervals) stay on record as written.
