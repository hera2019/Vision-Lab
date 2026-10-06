# Phase 5 — failure cases from held-out MOT20

Author: Codex / GPT-6 (exact runtime model ID not exposed).

**Status: three categories documented; existing FP32 baseline unchanged.** Independent review pending.

TrackEval pedestrian preprocessing and CLEAR IoU 0.5 continuity-aware correspondence; counts cross-checked with upstream.

Deterministic illustrative examples, not prevalence or new overall accuracy estimates.

Each image uses yellow for target GT and cyan for its associated prediction. A missing cyan box means no CLEAR match, not necessarily no prediction anywhere nearby. The images are original source crops with overlays, not generated scene content.

## occlusion-fragmentation

MOT20-03, GT 169, frames 130–185; crop frames 130, 155, 180.

Owner-reported pillar case: GT 169 is emitted as ID 75 through frame 141 and ID 107 from frame 180. Prior reference replay confirms the old ID expires after the 30-update retention limit. Long occlusion and a new ID are established in this case; increasing retention alone can introduce wrong-person recovery.

![occlusion-fragmentation](../data/phase-5/crops/occlusion-fragmentation.png)

| Frame | Visibility | Native input height px | Matched ID | Match IoU | Best cached detection IoU | Detection score |
|---|---:|---:|---|---:|---:|---:|
| 130 | 0.67 | 73.2 | 75 | 0.828 | 0.821 | 0.772 |
| 155 | 0.00 | 73.2 | none | — | 0.006 | 0.020 |
| 180 | 0.37 | 73.9 | 107 | 0.630 | 0.628 | 0.718 |

## identity-switch

MOT20-01, GT 28, frames 185–194; crop frames 189, 190, 194.

The same annotated person corresponds to one predicted ID for five consecutive frames, then a different ID for five. Another annotated person overlaps at the switch. This proves an identity correspondence change in a crowded neighborhood; overlap alone does not identify the precise internal association cause.

![identity-switch](../data/phase-5/crops/identity-switch.png)

| Frame | Visibility | Native input height px | Matched ID | Match IoU | Best cached detection IoU | Detection score |
|---|---:|---:|---|---:|---:|---:|
| 189 | 1.00 | 107.0 | 13 | 0.545 | 0.883 | 0.755 |
| 190 | 1.00 | 107.0 | 22 | 0.870 | 0.897 | 0.790 |
| 194 | 1.00 | 107.0 | 22 | 0.802 | 0.817 | 0.798 |

## small-target-miss

MOT20-01, GT 39, frames 86–93; crop frames 86, 89, 93.

The annotated pedestrian has visibility >=0.75, <=40-pixel annotated height at native detector resize, and no emitted-track match for all eight frames. At least five frames also lack an overlapping cached detection at IoU >=0.5. File inspection shows only a head entering at the bottom image border: small annotated extent and boundary truncation co-occur. The high visibility annotation does not mean the whole body is in the image. Nearby low-confidence detector boxes exist, but they do not overlap the GT sufficiently. This places part of the failure before association; it is not evidence of distant-person failure or a unique small-size cause.

![small-target-miss](../data/phase-5/crops/small-target-miss.png)

| Frame | Visibility | Native input height px | Matched ID | Match IoU | Best cached detection IoU | Detection score |
|---|---:|---:|---|---:|---:|---:|
| 86 | 0.97 | 19.1 | none | — | 0.198 | 0.010 |
| 89 | 0.98 | 23.1 | none | — | 0.111 | 0.016 |
| 93 | 0.98 | 27.6 | none | — | 0.103 | 0.024 |

## Evidence boundaries

Full selected intervals, GT/prediction/detection boxes, source hashes, exact crop rectangles and output hashes are in the JSON. CLEAR count audits agree with upstream on every scanned sequence. Earlier MOTA/IDF1/HOTA results are not recalculated or replaced. These examples do not estimate the relative frequency of the three categories.

No new models, downloads, parameter changes or detector inference. Crops retain MOTChallenge attribution and CC BY-NC-SA 3.0 research-use terms. The mean-shift bonus is deferred. Phase 6 reproduction remains next.

Reproduce with existing baseline data/evaluators/image: `bash scripts/phase5_failures.sh`.
