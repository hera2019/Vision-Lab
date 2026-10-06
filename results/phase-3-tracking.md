# Phase 3 — C++ ByteTrack tracking

Date: 2026-10-06 · Result: **pass** · ONNX Runtime threads: **4**

The C++ tracker follows the upstream Python tracker, including score fusion, inclusive-pixel association IoU, empty-frame skipping and list-update order. No thresholds were tuned. External source trees and prior-phase source/results remain unchanged.

This is Phase 3 acceptance only. The earlier nano Phase 1 raw-output tolerance failure stays on record; speed/INT8 acceptance is deferred to Phase 4.

## Fixed criteria — motmetrics 1.4.0

MOT17 train was seen during training: these are fidelity checks, not held-out accuracy.

Published reference scores are from ByteTrack README lines 157–158 at the source revision in `assets.json`.

| Model | 3a: every sequence ΔMOTA / ΔIDF1 ≤ 0.1 pp | 3b: overall vs published ±1.0 pp |
|---|---|---|
| nano | pass | pass |
| tiny | pass | pass |

### Criterion 3a per sequence — motmetrics 1.4.0

| Model | Sequence | Python MOTA | C++ MOTA | ΔMOTA pp | Python IDF1 | C++ IDF1 | ΔIDF1 pp | Pass |
|---|---|---:|---:|---:|---:|---:|---:|---|
| nano | MOT17-02-FRCNN | 41.9353 | 41.9353 | 0.0000 | 43.5574 | 43.5574 | 0.0000 | True |
| nano | MOT17-04-FRCNN | 87.3016 | 87.3016 | 0.0000 | 79.4209 | 79.4209 | 0.0000 | True |
| nano | MOT17-05-FRCNN | 64.6089 | 64.6089 | 0.0000 | 61.2610 | 61.2610 | 0.0000 | True |
| nano | MOT17-09-FRCNN | 75.3427 | 75.3427 | 0.0000 | 63.6933 | 63.6933 | 0.0000 | True |
| nano | MOT17-10-FRCNN | 59.6074 | 59.6074 | 0.0000 | 56.3667 | 56.3667 | 0.0000 | True |
| nano | MOT17-11-FRCNN | 70.3158 | 70.3158 | 0.0000 | 71.2235 | 71.2235 | 0.0000 | True |
| nano | MOT17-13-FRCNN | 48.6772 | 48.6772 | 0.0000 | 52.8318 | 52.8318 | 0.0000 | True |
| tiny | MOT17-02-FRCNN | 55.9335 | 55.9335 | 0.0000 | 50.5419 | 50.5419 | 0.0000 | True |
| tiny | MOT17-04-FRCNN | 92.2998 | 92.2998 | 0.0000 | 84.6092 | 84.6092 | 0.0000 | True |
| tiny | MOT17-05-FRCNN | 69.0328 | 69.0328 | 0.0000 | 69.9797 | 69.9797 | 0.0000 | True |
| tiny | MOT17-09-FRCNN | 79.6620 | 79.6620 | 0.0000 | 60.6814 | 60.6814 | 0.0000 | True |
| tiny | MOT17-10-FRCNN | 68.8138 | 68.8138 | 0.0000 | 59.4022 | 59.4022 | 0.0000 | True |
| tiny | MOT17-11-FRCNN | 76.4731 | 76.4731 | 0.0000 | 71.7934 | 71.7934 | 0.0000 | True |
| tiny | MOT17-13-FRCNN | 62.3948 | 62.3948 | 0.0000 | 62.8335 | 62.8335 | 0.0000 | True |

### Criterion 3b — C++ end-to-end, motmetrics 1.4.0

| Model | MOTA | Published MOTA | Δ pp | IDF1 | Published IDF1 | Δ pp | Pass |
|---|---:|---:|---:|---:|---:|---:|---|
| nano | 69.2325 | 69.0 | +0.2325 | 66.8414 | 66.3 | +0.5414 | True |
| tiny | 77.1347 | 77.1 | +0.0347 | 71.5651 | 71.5 | +0.0651 | True |

## MOT20 held-out accuracy — C++ end-to-end

A1 configuration: 608×1088 input, track_thresh 0.6, track_buffer 30, match_thresh 0.9, score fusion on; no sequence-specific overrides. These are the Phase 4 INT8 baselines; no pass/fail threshold applies.

| Model | Sequence | motmetrics MOTA | motmetrics IDF1 | TrackEval HOTA | TrackEval MOTA | TrackEval IDF1 | TrackEval ID switches |
|---|---|---:|---:|---:|---:|---:|---:|
| nano | MOT20-01 | 59.1444 | 57.2644 | 47.2305 | 64.2124 | 59.1179 | 114 |
| nano | MOT20-02 | 57.1105 | 48.2232 | 41.0724 | 61.7176 | 49.5971 | 839 |
| nano | MOT20-03 | 63.9598 | 65.5991 | 48.8623 | 67.7276 | 67.0016 | 805 |
| nano | MOT20-05 | 51.8111 | 44.9316 | 38.1824 | 59.9611 | 47.0982 | 2840 |
| nano | OVERALL | 56.0207 | 51.3699 | 42.0693 | 62.4221 | 53.3148 | 4598 |
| tiny | MOT20-01 | 63.4927 | 59.8191 | 51.5627 | 70.4831 | 62.3031 | 85 |
| tiny | MOT20-02 | 64.4318 | 55.7506 | 47.7105 | 69.5241 | 57.3878 | 651 |
| tiny | MOT20-03 | 66.9599 | 72.3134 | 54.2064 | 71.2260 | 74.0083 | 513 |
| tiny | MOT20-05 | 57.3416 | 54.0741 | 45.8033 | 66.0873 | 56.8331 | 2063 |
| tiny | OVERALL | 61.0752 | 59.4906 | 48.7788 | 68.0535 | 61.8822 | 3312 |

## MOT17 TrackEval — C++ end-to-end (fidelity only)

| Model | Sequence | HOTA | MOTA | IDF1 | ID switches |
|---|---|---:|---:|---:|---:|
| nano | MOT17-02-FRCNN | 35.0505 | 42.9686 | 43.8654 | 90 |
| nano | MOT17-04-FRCNN | 67.2747 | 87.3142 | 79.4209 | 131 |
| nano | MOT17-05-FRCNN | 48.7919 | 64.7969 | 61.3320 | 71 |
| nano | MOT17-09-FRCNN | 53.3261 | 75.6244 | 63.8200 | 25 |
| nano | MOT17-10-FRCNN | 44.0700 | 59.7165 | 56.4167 | 127 |
| nano | MOT17-11-FRCNN | 61.4760 | 70.7291 | 71.3907 | 20 |
| nano | MOT17-13-FRCNN | 42.1685 | 49.1582 | 52.9798 | 83 |
| nano | OVERALL | 55.9842 | 69.5308 | 66.9605 | 547 |
| tiny | MOT17-02-FRCNN | 41.7466 | 56.5847 | 50.6998 | 108 |
| tiny | MOT17-04-FRCNN | 74.7807 | 92.3586 | 84.6712 | 102 |
| tiny | MOT17-05-FRCNN | 55.7373 | 69.2641 | 70.0707 | 59 |
| tiny | MOT17-09-FRCNN | 53.0592 | 79.7371 | 60.7065 | 22 |
| tiny | MOT17-10-FRCNN | 46.8271 | 68.8060 | 59.4022 | 135 |
| tiny | MOT17-11-FRCNN | 64.0124 | 77.2679 | 72.0878 | 38 |
| tiny | MOT17-13-FRCNN | 49.8195 | 62.5752 | 62.9371 | 73 |
| tiny | OVERALL | 61.8502 | 77.3698 | 71.6667 | 537 |

## Output comparisons

End-to-end output equals cache-then-track output byte-for-byte for every sequence/model: **True**.

Literal matching is kept separate from numeric matching. The Python writer expands rounded float32 scores; C++ writes two decimal places (I-5). Most score differences are below 2.87e-8, but three rows in nano MOT20-02 and tiny MOT20-05 differ by 0.01 at decimal-half rounding boundaries (NumPy float32 rounding vs C++ decimal formatting). Frames, IDs and boxes agree; neither configured evaluator uses these emitted prediction scores. The percentages below compare literal lines, without normalization.

| Dataset | Model | Sequence | Literal line share | Same frame/ID order | Max box difference px | Max score difference |
|---|---|---|---:|---|---:|---:|
| MOT17 | nano | MOT17-02-FRCNN | 2.996% | True | 0.0000 | 2.86e-08 |
| MOT17 | nano | MOT17-04-FRCNN | 1.794% | True | 0.0000 | 2.86e-08 |
| MOT17 | nano | MOT17-05-FRCNN | 1.490% | True | 0.0000 | 2.86e-08 |
| MOT17 | nano | MOT17-09-FRCNN | 1.083% | True | 0.0000 | 2.86e-08 |
| MOT17 | nano | MOT17-10-FRCNN | 2.900% | True | 0.0000 | 2.86e-08 |
| MOT17 | nano | MOT17-11-FRCNN | 1.594% | True | 0.0000 | 2.86e-08 |
| MOT17 | nano | MOT17-13-FRCNN | 4.004% | True | 0.0000 | 2.86e-08 |
| MOT17 | tiny | MOT17-02-FRCNN | 2.388% | True | 0.0000 | 2.86e-08 |
| MOT17 | tiny | MOT17-04-FRCNN | 1.111% | True | 0.0000 | 2.86e-08 |
| MOT17 | tiny | MOT17-05-FRCNN | 1.741% | True | 0.0000 | 2.86e-08 |
| MOT17 | tiny | MOT17-09-FRCNN | 0.693% | True | 0.0000 | 2.86e-08 |
| MOT17 | tiny | MOT17-10-FRCNN | 2.714% | True | 0.0000 | 2.86e-08 |
| MOT17 | tiny | MOT17-11-FRCNN | 0.893% | True | 0.0000 | 2.86e-08 |
| MOT17 | tiny | MOT17-13-FRCNN | 3.662% | True | 0.0000 | 2.86e-08 |
| MOT20 | nano | MOT20-01 | 3.077% | True | 0.0000 | 2.86e-08 |
| MOT20 | nano | MOT20-02 | 3.005% | True | 0.0000 | 0.01 |
| MOT20 | nano | MOT20-03 | 3.692% | True | 0.0000 | 2.86e-08 |
| MOT20 | nano | MOT20-05 | 4.109% | True | 0.0000 | 2.86e-08 |
| MOT20 | tiny | MOT20-01 | 2.284% | True | 0.0000 | 2.86e-08 |
| MOT20 | tiny | MOT20-02 | 2.553% | True | 0.0000 | 2.86e-08 |
| MOT20 | tiny | MOT20-03 | 2.631% | True | 0.0000 | 2.86e-08 |
| MOT20 | tiny | MOT20-05 | 3.455% | True | 0.0000 | 0.01 |

## Validation, timing and provenance

- Both models have bit-identical 1-thread/4-thread detections on MOT17-02 frames 1–50.
- TrackEval ground-truth self-tests score exactly 100 HOTA/MOTA/IDF1 on every MOT17 and MOT20 sequence.
- Behavioral fixtures for confidence tiers, empty frames, recovery, expiry, unconfirmed removal and exact float32 thresholds: pass=True.
- An initial threshold-equality fixture failed (I-7). The score comparisons were corrected to match NumPy float32 semantics; the negative result and actual cached boundary counts are preserved in the JSON. All final C++ cache outputs were regenerated with the corrected tracker and checked against stored end-to-end outputs.
- Two driver/artifact failures are retained (I-8/I-9): editing a running shell driver caused an EOF error after every output was written; executing an encoder from the protected tmpfs was refused. Final drivers pass syntax checks, regenerated tracking files agree, and the encoder uses the normal image build. Container protections were preserved.
- Evaluators intentionally differ: motmetrics follows ByteTrack's procedure (gt min_confidence=1, IoU distance threshold 0.5, lap solver). TrackEval uses its standard pedestrian/distractor preprocessing. Their scores must not be mixed.
- These are concurrent accuracy runs. Per-stage time totals and Python tracker run times are in the JSON/raw files; they are observations, not Phase 4 benchmarks. Image decoding is excluded from stage sums. No realtime or INT8 claim is made.
- Scores from an earlier evaluator run are reused only when all its input file hashes still match. End-to-end scores can reuse cached-C++ evaluation only when every end-to-end output byte is identical; each reuse is recorded in the JSON.
- Detection and tracker output SHA-256 values, dependency versions and per-sequence stage time totals are in the JSON. Models/data are excluded from git; sources and revisions are in `assets.json`.

## Reproduction

Run from the repository root. The existing local models and MOT17/MOT20 sequences are required; TrackEval must exist at the revision in `assets.json`. Fresh-clone asset setup is Phase 6, not validated here.

```bash
./scripts/phase3_build.sh
./scripts/phase3_determinism.sh
./scripts/phase3_edge_cases.sh
./scripts/phase3_evaluate.sh self
./scripts/phase3_detect.sh 4
./scripts/phase3_track.sh
./scripts/phase3_end_to_end.sh 4
./scripts/phase3_demo.sh
./scripts/phase3_finalize.sh
```

All runs go through the hardened container wrapper. Accuracy settings are fixed by amendment A1.

## Demonstrations

Three 12-second clips were selected before held-out scores were available: MOT17-02 (fixed street camera), MOT17-05 (moving street camera), MOT20-03 (crowded scene). Each uses measured C++ nano end-to-end output, fixed ID colors and 2-second image-space trails. All frames in each output video were decoded successfully; three preview frames per video were saved. Only pedestrian identities are drawn. Playback rate is the source rate, not measured inference throughput.

| Sequence | Frames | Source FPS | Video |
|---|---|---:|---|
| MOT17-02-FRCNN | 1–360 | 30 | [`MOT17-02-FRCNN-nano.mp4`](../data/phase-3/demos/MOT17-02-FRCNN-nano.mp4) |
| MOT17-05-FRCNN | 1–168 | 14 | [`MOT17-05-FRCNN-nano.mp4`](../data/phase-3/demos/MOT17-05-FRCNN-nano.mp4) |
| MOT20-03 | 1–300 | 25 | [`MOT20-03-nano.mp4`](../data/phase-3/demos/MOT20-03-nano.mp4) |

Source: MOTChallenge. Clips retain CC BY-NC-SA 3.0 attribution and are research-only. No external video or additional model was downloaded.

## Next step

Phase 4 benchmarks and INT8 are not started. The next taskbook is written after review of this phase. Any failed criterion remains failed and requires review; thresholds are not adjusted to make it pass.
