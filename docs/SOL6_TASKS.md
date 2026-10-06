# Sol 6 taskbook: Phase 3 (tracking)

Framework and review: Claude / Opus 5.5. Execution: Sol 6.1 (or the actual
identified agent). Written 2026-10-06.

Read first, in order: [PROJECT_RULES.md](PROJECT_RULES.md),
[01-phase-0-plan.md](01-phase-0-plan.md) (including amendment **A1**),
[ISSUES.md](ISSUES.md), the Phase 2 result
[`results/phase-2-detector-parity.md`](../results/phase-2-detector-parity.md),
and [`cpp/src/detector.h`](../cpp/src/detector.h).

## Goal

Add ByteTrack tracking in C++, prove it matches ByteTrack's Python tracker, then
reproduce the published MOT17 numbers and measure held-out MOT20 accuracy.

## Starting state (verify before work)

- Branch `main`, clean working tree, Phase 2 committed.
- Present locally (not in git): `models/bytetrack_{nano,tiny}_mot17.{pth.tar,onnx}`,
  `data/MOT17/train/*-FRCNN` (7 sequences, 5,316 frames, with `gt/`),
  `data/MOT20/train/MOT20-0{1,2,3,5}` (8,931 frames, with `gt/`),
  `external/ByteTrack` at `d1bf0191adff59bc8fcfeaa0b33d3d1642552a99`.
- Environment check: `./scripts/phase2_detector_parity.sh` must print
  `pass=True` for nano and tiny. If not, stop and report.

## Tasks

### T1 · Detection cache (C++)

Add a C++ tool (e.g. `cpp/src/detect_sequence.cpp`, reusing `vl::Detector`
unchanged) that runs every frame of one sequence directory in order and writes
`data/phase-3/dets/<model>/<sequence>.txt`, one line per detection:
`frame,-1,x1,y1,x2,y2,score` with `%.9g` precision, original-image pixels. Also
write per-frame stage timings to a sibling `.timing.csv`.

- First check thread determinism: MOT17-02 frames 1–50, `--threads 1` vs
  `--threads 4`. Record in the result whether the detections are bit-identical.
  If identical, accuracy runs may use 4 threads; otherwise use 1.
- Run all 7 MOT17 FRCNN sequences and all 4 MOT20 sequences, for nano and tiny.
  Expected scale at 1 thread: about 77 ms (nano) / 300 ms (tiny) per frame.

### T2 · Python reference tracker

`python/track_reference.py`: read the T1 cache and run ByteTrack's
`yolox.tracker.byte_tracker.BYTETracker`, **unmodified**, exactly as
`yolox/evaluators/mot_evaluator.py` `evaluate()` does:

- fresh tracker per sequence, `frame_rate=30`; the per-sequence
  `track_thresh` / `track_buffer` overrides from that function (MOT17 only);
- pass detections as an N×5 array `[x1, y1, x2, y2, score]` with
  `img_info = img_size = (height, width)` of the sequence, so the internal rescale is 1;
- a frame with no detections does **not** call `update()` (the evaluator skips
  it when `outputs[0] is None`, so the tracker's frame counter does not advance);
  the C++ tracker must do the same;
- keep a track only if `w*h > 100` and not `w/h > 1.6`;
- write results in ByteTrack's `write_results` format.

Output: `data/phase-3/tracks/python/<model>/<sequence>.txt`.

Dependencies: add pinned `lap`, `cython_bbox`, `scipy`, `motmetrics` to
`python/requirements.txt`. If a package needs compiling, add the minimum build
tools to the `pytools` stage and record it. NumPy-2 incompatibilities are handled
with shims in our code (see I-3), never by editing `external/`.

### T3 · C++ tracker

Port ByteTrack's **Python** tracker to C++ under `cpp/src/tracker/`. You may start
from `external/ByteTrack/deploy/ncnn/cpp` (MIT; keep attribution, add it to
`docs/LICENSES.md`), but the Python code is the specification:

- `fuse_score` in the first and the unconfirmed association (missing from the
  official C++ port, see I-2);
- `det_thresh = track_thresh + 0.1`; `buffer_size = int(frame_rate / 30 * track_buffer)`;
- association thresholds: `match_thresh` (first), 0.5 (second, low-score boxes), 0.7 (unconfirmed);
- linear assignment equivalent to `lap.lapjv(cost, extend_cost=True, cost_limit=thresh)`;
- Kalman filter constants and `remove_duplicate_stracks` as in Python.

Two tools: track from the T1 cache (for T4) and end-to-end images → tracks
(detector + tracker, per-stage timing). Same output format as T2, written to
`data/phase-3/tracks/cpp/<model>/<sequence>.txt`. Record every deviation from the
Python behaviour you find in ISSUES.md.

### T4 · Evaluation

- **motmetrics, ByteTrack's procedure:** reproduce `tools/track.py` lines 221–270
  (gt `min_confidence=1`, IoU `distth=0.5`, `lap` solver, motchallenge metrics).
  This is the evaluator for criteria 3a and 3b.
- **TrackEval** at commit `12c8791b303e0a0b50f753af204249e622d0281a`, cloned to
  `external/TrackEval` (record in `assets.json`): HOTA, CLEAR (MOTA), Identity
  (IDF1); MOT17 with a seqmap of the 7 FRCNN sequences; MOT20 train. First
  evaluate ground truth against itself and confirm 100.

### T5 · Criteria (from the test plan, unchanged)

| ID | Check | Pass |
|---|---|---|
| 3a | C++ tracker vs Python tracker, same cached detections, MOT17 train, nano and tiny | Per sequence, \|ΔMOTA\| ≤ 0.1 and \|ΔIDF1\| ≤ 0.1 (motmetrics, percentage points) |
| 3b | C++ end-to-end, MOT17 train overall (motmetrics) | Within ±1.0 of published: nano 69.0 MOTA / 66.3 IDF1, tiny 77.1 / 71.5 |

Also report, without a criterion: the share of identical output lines C++ vs
Python; end-to-end output identical to cache-then-track output (yes/no).

If 3b misses: report the gap, check the procedure against ByteTrack's code, and
record findings. Do **not** tune thresholds or settings to close the gap.

### T6 · MOT20 held-out measurement

C++ end-to-end on MOT20 train with the A1 held-out configuration. Report
TrackEval HOTA / MOTA / IDF1 and motmetrics MOTA / IDF1 per sequence and
overall, for nano and tiny. No pass/fail: this is the accuracy baseline that
Phase 4's INT8 comparison will use.

## Deliverables

- `results/phase-3-tracking.md` + `.json`: per-sequence tables for 3a, 3b, T6;
  evaluator named on every number; thread count; run times; versions.
- Tracker outputs stay in `data/phase-3/` (not in git); record their SHA-256 in the JSON.
- `scripts/phase3_*.sh`: one command per step, runnable from the repo root.
- `docs/walkthrough/phase-3.md` (bilingual, beginner level; see PROJECT_RULES).
- Rows in `docs/CHANGES.md`; issues in `docs/ISSUES.md`; status line in `docs/PLAN.md`.

## Stop and report to the owner when

- a criterion fails (finish the investigation notes first);
- Phase 0–2 code would need to change;
- free disk drops below 10 GiB;
- anything not listed here would need downloading.

Phase 4 (benchmarks, INT8) is out of scope for this taskbook; it will be written
after review of Phase 3.
