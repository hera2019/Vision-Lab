# Mean-shift bonus: fixed comparison protocol

Author: Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-08.
Owner requested the remaining mean-shift comparison after Opus's review.
Implements the unchanged Phase 0 bonus: OpenCV mean-shift initialized from
first-appearance ground-truth boxes, scored with the same TrackEval settings.
This protocol is written before the new tracking/evaluation outcomes.

## Algorithm, initialization and limits

- Use the existing pinned Python/OpenCV image, one OpenCV thread, CPU only.
  No downloads, dependencies, UI access or baseline modifications.
- Decode and resize/letterbox to 608x1088, same aspect ratio, top-left placement
  and 114 padding as the detector input; HSV processing uses uint8 pixels.
- For each valid pedestrian GT identity (`mark=1`, `class=1`), initialize once
  at its first annotated frame with the clipped, integer-rounded resized box.
  Assign a new arbitrary tracker ID; record seed/GT mapping separately.
  No visibility-based selection. Invalid/empty clipped boxes are reported.
- Follow OpenCV's hue-histogram tutorial: initial HSV mask S>=60/V>=32,
  180 hue bins over [0,180), normalize to [0,255], fixed histogram,
  `EPS|COUNT` termination (10 iterations, epsilon 1). No histogram updates,
  scale changes, re-detection, cross-target association or GT-based correction.
- Keep each initialized tracker until sequence end. No future GT lifetime,
  disappearance/re-entry label, visibility, or later box controls updates or
  retirement. Empty histograms remain stationary and are explicitly counted.
  This simple classical baseline can emit stale boxes after a person leaves;
  that limitation is part of the comparison, not corrected after scoring.
- Emit MOT-format boxes in original pixels, score 1.0, with the same >100
  area / <=1.6 aspect-ratio output filter as ByteTrack. Initialization-frame
  predictions are the provided seed boxes. Their annotation advantage is
  disclosed: this is an oracle-initialized baseline, not autonomous detection.

## Exact computation optimization and preflight

For every mean-shift iteration, compute backprojection only inside the current
window and call OpenCV's own one-iteration `meanShift` on a reusable full-size
zero canvas. Values outside the current window cannot affect that iteration's
moments. Repeat up to ten iterations, stopping at the same convergence rule.
Verify final windows equal direct full-image backprojection plus standard
OpenCV meanShift on synthetic edge/zero/moving cases and fixed MOT17 images
before running MOT20. If equivalence fails, stop and correct implementation,
not algorithm parameters. This optimization preserves the tutorial algorithm.

## Data, scoring and speed

- Quality comparison: all four MOT20 sequences / all 8,931 frames, once;
  no MOT20 tuning or parameter selection. Store seed provenance, GT/input
  hashes, full track files, frame coverage, counts and timings.
- Score mean-shift and existing nano/tiny FP32 track files in a separate
  TrackEval input/output directory, using the same pedestrian preprocessing
  and HOTA/CLEAR/Identity settings as Phase 3. Check reference scores/hashes
  against the original evaluation. Report per-sequence and overall
  HOTA/MOTA/IDF1/ID switches, with evaluator named. Also report motmetrics
  separately using the unchanged project helper; do not mix evaluators.
- The raw all-GT overlap matrices alone can occupy about 3.96 GiB on MOT20-05,
  before preprocessing creates another set. An own `MotChallenge2DBox` dataset
  adapter computes each raw float64 overlap matrix on demand with the same
  upstream function. Preprocessing and all metrics stay upstream/unchanged.
  Verify every preprocessed array/dtype and every HOTA/CLEAR/Identity field
  against the eager dataset on full MOT17-05 before full evaluation; also
  require fresh nano/tiny scores to equal original per-sequence/overall scores.
  Do not raise container memory limits. Record the adapter and equivalence.
- Speed: MOT17-02 frames 51–150, 50 warm-up frames, three fresh processes,
  one CPU quota / one OpenCV thread. Compare with original one-thread nano/
  tiny pipeline measurements, clearly separated sessions and initialization
  workloads. Include decoding, resizing, HSV and tracking; exclude file
  writing/drawing and human GT-annotation cost. This does not establish an
  autonomous real-time detector or count as the original shipping criterion.
- No new pass threshold; this bonus is a reported comparison, not a model
  replacement or evidence of universal superiority.

## Outputs and boundary

Use unchanged `scripts/drun.sh`; writable `results` and
`data/phase-5-meanshift` only. Check disk before full execution and stop below
10 GiB. New main report pair: `results/phase-5-meanshift.{md,json}`; raw
evidence `results/phase-5-meanshift/`; ignored tracks/evaluator intermediates
`data/phase-5-meanshift/`. Update walkthrough, results index, README, PLAN,
ISSUES/CHANGES and asset provenance. No commit, merge or push in this task.

Method sources: [OpenCV tutorial](https://docs.opencv.org/4.x/d7/d00/tutorial_meanshift.html)
and [OpenCV meanShift implementation](https://github.com/opencv/opencv/blob/4.x/modules/video/src/camshift.cpp).
