# Phase 5 execution protocol — failure evidence

Author: Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-06.
Owner requested the next work after Phase 4. This executor protocol implements
the frozen Phase 0 requirement: at least three failure categories, each with
a MOT20 sequence, frame range and crop. It is not an Opus taskbook or review.

Use existing accepted nano FP32 detections/tracks and original MOT20 images/GT.
No detector inference, model download, tuning, baseline replacement or changes
to Phase 0–4 results. All analysis runs offline through `scripts/drun.sh` with
only `results` and `data/phase-5` writable. Check free disk first.

## Case selection fixed before the new scan

- Occlusion/fragmentation: retain the owner-reported MOT20-03 GT-169 case,
  IDs 75 through frame 141 and 107 from frame 180. Audit frames 130–185;
  crops at 130/155/180. Reuse the recorded reference-state diagnosis.
- Identity correspondence switch: scan MOT20 sequences in name order, frames
  in order, GT IDs in order. Use TrackEval pedestrian preprocessing and its
  CLEAR correspondence rule at IoU 0.5. Select the first switch with five
  consecutive old-ID matches before it and five consecutive new-ID matches
  from it, target visibility >=0.6 throughout and another GT box overlapping
  the target at the switch. Crop before/at/after; do not infer causality from
  a switch alone.
- Small-image target missed: same scan order. First eight-frame interval with
  pedestrian GT visibility >=0.75, height <=40 pixels at native 608×1088
  resize and no matched emitted track throughout. At least five of those
  frames must also have no cached detection at IoU >=0.5. Crop first/middle/
  last. This describes image size, not measured real-world distance.

Selection is illustrative, not random or a failure-prevalence estimate. If a
selector finds no case, report that result before changing or replacing it.
The old occlusion case is deliberate and is labelled as owner-reported.
Frame ranges and selected GT identities may be read from held-out outputs to
document errors; they must not be used to tune or recalibrate the model.

## Evidence and deliverables

Keep original IDs in case records. Match using the upstream CLEAR logic in
our own read-only helper; cross-check counts against upstream CLEAR on each
scanned sequence. Store per-frame target GT box/visibility, associated ID/IoU,
best cached-detection IoU/score, neighboring GT boxes and input hashes.
GT boxes are annotation evidence, not predictions. Crops clearly distinguish
GT yellow from prediction cyan, retain context and carry frame/ID labels.
Check generated images by file inspection; no app/browser or screen access.

Write `results/phase-5-failures.md` and `.json`, rerunnable script, image/track
provenance in `assets.json`, bilingual beginner `docs/walkthrough/phase-5.md`,
and actual-author ledger/plan updates. Preserve limitations and negative
evidence. Existing demos and accepted baseline remain unchanged. Mean-shift
is an optional bonus and is not included in this mandatory failure-case pass.
Phase 6 fresh-clone reproduction remains subsequent work. No commit or push.
