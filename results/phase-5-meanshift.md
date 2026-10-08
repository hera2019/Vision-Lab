# Classical mean-shift versus detection + ByteTrack

Author: Codex / GPT-6 (exact runtime model ID not exposed); generated 2026-10-08T05:51:35.528268+00:00.

[JSON companion](phase-5-meanshift.json), [fixed protocol](../docs/MEANSHIFT_EXECUTION.md). The optional Phase 5 comparison is now measured; earlier mandatory failure reports and model baselines stay unchanged.

## Quality on all four MOT20 sequences

All 8,931 frames. Same pinned TrackEval pedestrian preprocessing, HOTA/CLEAR/Identity settings. Mean-shift receives a GT box for every person at first valid appearance; ByteTrack uses the detector. This is an **oracle-initialized classical control**, not autonomous person detection or an equal-input contest. No later GT correction, visibility-based removal, appearance update, scale adaptation or re-detection.

| Sequence / method | HOTA | MOTA | IDF1 | ID switches |
|---|---:|---:|---:|---:|
| MOT20-01 / meanshift | 7.823 | -99.190 | 5.356 | 131 |
| MOT20-01 / nano | 47.231 | 64.212 | 59.118 | 114 |
| MOT20-01 / tiny | 51.563 | 70.483 | 62.303 | 85 |
| MOT20-02 / meanshift | 3.515 | -265.978 | 2.362 | 1093 |
| MOT20-02 / nano | 41.072 | 61.718 | 49.597 | 839 |
| MOT20-02 / tiny | 47.710 | 69.524 | 57.388 | 651 |
| MOT20-03 / meanshift | 5.168 | -184.280 | 3.042 | 2613 |
| MOT20-03 / nano | 48.862 | 67.728 | 67.002 | 805 |
| MOT20-03 / tiny | 54.206 | 71.226 | 74.008 | 513 |
| MOT20-05 / meanshift | 3.930 | -286.741 | 3.256 | 12185 |
| MOT20-05 / nano | 38.182 | 59.961 | 47.098 | 2840 |
| MOT20-05 / tiny | 45.803 | 66.087 | 56.833 | 2063 |
| OVERALL / meanshift | 4.239 | -252.300 | 3.108 | 16022 |
| OVERALL / nano | 42.069 | 62.422 | 53.315 | 4598 |
| OVERALL / tiny | 48.779 | 68.054 | 61.882 | 3312 |

TrackEval percentages above are not interchangeable with motmetrics. The latter uses the project's original procedure and is reported separately:

| Method | motmetrics MOTA | motmetrics IDF1 |
|---|---:|---:|
| meanshift | -254.138 | 3.101 |
| nano | 56.021 | 51.370 |
| tiny | 61.075 | 59.491 |

Fresh nano/tiny scores for every sequence and overall match the original report exactly, and source track hashes remain unchanged. Negative MOTA means false positives, misses and switches together exceed the annotated-target count; it is a valid metric outcome.

## Initialization and workload

| Sequence | Seeded identities | Empty histograms | Emitted rows | Mean active trackers | Peak RSS KiB |
|---|---:|---:|---:|---:|---:|
| MOT20-01 | 74 | 0 | 23045 | 54.5 | 84436 |
| MOT20-02 | 270 | 0 | 436426 | 157.5 | 93332 |
| MOT20-03 | 702 | 23 | 653378 | 334.8 | 118264 |
| MOT20-05 | 1169 | 8 | 2112235 | 710.2 | 195344 |

The algorithm has no retirement rule. Tracks persist after exits/occlusion and may drift to similar colors. This can cause many false positive boxes; fixed window sizes cannot follow scale changes. An unchanged numerical ID does not prove the box follows the same person. These findings characterize this fixed tutorial-style baseline, not every classical tracker or a tuned alternative.

## One-thread illustrative speed check

Same MOT17-02 measured frames 51–150, 50 warm-up frames, three fresh processes, one CPU quota, 608×1088. Mean-shift times include JPEG decoding, resize, HSV and tracking/filtering, excluding file output/drawing and manual annotation cost.

| Method | Median repeat FPS |
|---|---:|
| Mean-shift (OpenCV Python, 1 thread) | 135.693 |
| nano FP32 detector + ByteTrack (original C++, 1 thread) | 11.610 |
| tiny FP32 detector + ByteTrack (original C++, 1 thread) | 3.175 |

Mean-shift combined p50/p95: 7.220/8.225 ms. This is a different-session, different-implementation comparison with oracle initialization and different target workloads, not a paired acceleration claim or the original real-time acceptance test. Image checksums pre-read filesystem bytes outside timing, so cold I/O is not controlled. Sparse MOT17 timing does not establish throughput in a dense street scene. Full-sequence timing summaries and raw CSVs are retained in the JSON.

## Verification and scope

Lazy window backprojection matches standard full-image meanShift on 120 synthetic and 40 fixed MOT17 windows; input preprocessing matches exactly. The on-demand raw-IoU dataset adapter uses unchanged upstream overlap arithmetic, preprocessing and metrics. Every preprocessed array/dtype and every metric field equals the eager implementation on all 837 MOT17-05 frames; original nano/tiny MOT20 scores also reproduce exactly. External source remains unchanged. The adapter avoids simultaneously retaining raw and preprocessed dense IoU matrices without raising the six-GiB container limit.

Full predictions/seeds and evaluator intermediates: ignored `data/phase-5-meanshift/`; [raw metadata/timings](phase-5-meanshift/). No downloads, new dependencies, GUI access, MOT20 parameter search, baseline replacement, commit, merge or push. These uncommitted additions have not undergone a fresh-clone full reproduction or independent bonus review. The established full-reproduction profile remains historical scope and does not execute this new bonus.
