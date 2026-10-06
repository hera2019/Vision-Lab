# Continuity pilot — fixed development experiment

Author: Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-06.
Written before running the variants below. Owner asked to continue after two
reported identity failures; prioritize a bounded continuity experiment.

## Scope and data boundary

Keep the accepted C++/Python Phase 3 baseline, outputs and demos unchanged.
No model/data/toolchain downloads. Prototype with existing Python ByteTrack
and OpenCV; external source remains untouched. This is development diagnosis,
not Phase 4 benchmarking or a new fidelity/accuracy acceptance result.
MOT20 is not run with modified settings or used for variant selection.

Use only the already inspected MOT17-05 nano cache, frames 1–168, with source
images for motion estimation. This exposed, training-seen case can demonstrate
behavioral change but cannot establish generalization. Report all variants,
including regressions; no parameter search or post-result adjustment.

## Variants fixed before outcomes

| Variant | Lost retention (updates) | Camera compensation |
|---|---:|---|
| baseline | 14 | None |
| retention-42 | 42 | None |
| motion-14 | 14 | Translation only |
| motion-retention-42 | 42 | Translation only |

All other tracker settings and the official `frame_rate=30` argument stay
unchanged. Retention 42 is three times this sequence's frozen 14-update
override (one versus three seconds at 14 fps when every frame updates).
Longer retention is an experiment, not a replacement for A1.

## Motion estimator

Estimate background motion between consecutive frames using existing OpenCV
corner detection, pyramidal optical flow and robust partial-affine estimation.
Use half-resolution grayscale; mask detections with score >= 0.1; up to 500
corners, quality 0.01, minimum distance 7, block size 3. Flow: 21×21 window,
three pyramid levels, forward/backward error <= 1 pixel. RANSAC: 3-pixel
threshold, 2,000 iterations, confidence 0.99, refinement 10 iterations.
Seed 0, OpenCV one thread.

Require >=20 valid point pairs, >=15 inliers, inlier fraction >=0.5,
scale in [0.98, 1.02], rotation <=2 degrees and translation <=25% of image
dimensions. Otherwise use identity and log the reason. Convert estimated
translation to full-resolution pixels. Apply it to the predicted track-center
coordinates after the reference Kalman prediction; leave size and velocity
unchanged. No affine rotation/scale correction, appearance matching, or
uncertainty model for the estimated translation is claimed.

Official API references: [optical flow](https://docs.opencv.org/4.x/dc/d6b/group__video__track.html),
[affine estimation](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html).

## Checks and results

1. Baseline replay must have identical frame/ID/box rows to stored C++ for all
   168 frames; stop if it differs. Observation/prototype code must not alter
   baseline behavior.
2. Three synthetic inputs, fixed 40 frames with a persistent anchor to advance
   updates: target in frames 1–3, absent 4–24, present 25–40. Cases: same person
   returns to same box; different person arrives at same box; same person
   returns to a nonoverlapping box. The first two deliberately have identical
   detections but different synthetic identities, demonstrating ambiguity.
   Compare 14/42-update retention; do not use appearance or GT in association.
3. Motion sanity checks on artificial translation, rejection on a blank image,
   and correct application of a known translation to a predicted center.
4. Save every variant's MOT file and the per-frame camera-motion diagnostics.
   Report the exposed target's visible-frame ID history (GT 14, IoU >=0.5),
   plus motmetrics MOTA/IDF1/IDSW/FP/FN on the fixed 168-frame prefix, following
   the existing min_confidence=1/IoU=0.5/lap procedure. These are development
   diagnostics only; not full-sequence or held-out accuracy.
5. Human `.md` and machine `.json` results, input/output hashes, versions,
   limitations and actual author. Optional side-by-side demo uses unchanged
   variant outputs and source playback rate, never repaired identity labels.

Continue to an implementation or broader validation only after assessing the
bounded result. F2 readability cleanup and Phase 4 remain separate work items.
