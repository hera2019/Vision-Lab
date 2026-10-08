# Mean-shift bonus — executor handoff for Opus

Author: Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-08.
This is a review request brief, not an independent verdict. Earlier Phases
3–6 remain accepted by Opus; this addition is outside that review.

## Completed scope

The owner requested the missing original mean-shift comparison.
[Predeclared protocol](../MEANSHIFT_EXECUTION.md),
[report](../../results/phase-5-meanshift.md),
[JSON](../../results/phase-5-meanshift.json).
All four MOT20 sequences, 8,931 frames, one fixed implementation; no tuning.
TrackEval overall HOTA/MOTA/IDF1: mean-shift 4.239/−252.300/3.108,
nano 42.069/62.422/53.315, tiny 48.779/68.054/61.882.
Separately scored motmetrics values stay separate. Fresh reference scores
and track hashes agree exactly with original Phase 3 evidence.

Mean-shift gets the first valid GT appearance/box for each person, arbitrary
tracker IDs, fixed hue histogram/window size, no later GT correction or
retirement. This gives it initial annotation information unavailable to a
normal video. It leaves stale boxes and can drift to similar clothes; unchanged
numeric IDs do not establish identity continuity. Negative MOTA is a valid
outcome, not a failed evaluator. No bonus quality gate was defined.

## Focused review points

- Check GT is restricted to the birth schedule and initial boxes. No later
  visibility, disappearance, position or re-entry annotation controls tracking.
- Check the fixed tutorial-style protocol and its limitations are explicit;
  no general conclusion about all classical trackers or vehicle tracking.
- `python/meanshift_baseline.py` computes local backprojection before each
  native one-iteration OpenCV call. The final windows equal standard full-image
  meanShift on 120 synthetic and 40 MOT17 cases, before the main experiment.
- `python/meanshift_trackeval.py` lazily computes raw float64 overlaps. All
  preprocessing and metrics remain upstream; 5,022 arrays/dtypes and every
  metric field equal the eager implementation on 837 MOT17-05 frames.
  Original nano/tiny MOT20 metrics also reproduce exactly. Check the adapter
  and MIT attribution; no edits in `external/` or raised memory limit.
- Three one-thread MOT17-02 repeats yield 135.693 FPS, excluding annotation
  work/output/drawing. Existing C++ timing comes from a different session;
  input checksums pre-read bytes. This is illustrative sparse-clip speed,
  not paired acceleration or dense-scene/edge-device acceptance.
- Review bilingual Phase 5 explanation, README/index/status, asset hashes,
  report source identity and the executor's bounded output audit.

## Evidence and rerun boundary

[Raw records](../../results/phase-5-meanshift/): fixed-protocol preflight,
evaluator equivalence, three benchmark CSV/metadata pairs, fresh quality JSON,
image ID and execution log. Full prediction/seed/timing files are ignored
under `data/phase-5-meanshift/tracks/`; hashes and workload summaries are in
the main JSON and `assets.json`. The
[executor output audit](../../results/phase-5-meanshift/verification.json)
checks complete frame/timing coverage, first eligible GT seeds, every row's
shape/finite values/order/birth/window size, and hashes; it is not independent.

`bash scripts/phase5_meanshift.sh` uses the existing Python image, licensed
inputs and pinned TrackEval. Track outputs must be absent: overwrite is
rejected. Runtime stays offline, non-root, read-only except explicit outputs,
one CPU and six GiB. No download, dependency, UI access, model change, commit,
merge or push. The original tracking/evaluation run completed; report and
bounded audit steps were subsequently attached to the entry point and run
separately. The final entry point has not been rerun end to end in a fresh
clone. Earlier clean-clone evidence does not cover this new bonus.

No autonomous improvement or new acceptance threshold is claimed. Requested
next action: review this bonus and decide whether its evidence is sufficient.
