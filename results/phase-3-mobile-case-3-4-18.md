# MOT17-05 nano: owner-reported identity chain 3 → 4 → 18

Date: 2026-10-06. Investigator: Codex / GPT-6 (exact runtime model ID not exposed).

**Confirmed tracking failure:** annotated person 14 is associated successively
with tracker IDs 3, 4 and 18 in the moving-street demo. This includes an ID
being transferred between different people, rather than only a lost track
expiring and being recreated.

## Evidence

The following GT correspondence uses the highest continuous-box IoU to
marked pedestrian annotations. The paired JSON retains every inspected row,
including ambiguous overlapping boxes during full occlusion; correspondence
is not an appearance-based identity measurement or a new benchmark score.

| Source frames | Measured identity correspondence |
|---|---|
| 4–20 | ID 3 follows GT person 14 on 16 of 17 rows with IoU ≥ 0.5. The frame-19 best match is another fully occluded annotation; it is retained as ambiguous evidence. |
| 5–19 | ID 4 initially follows a different person, GT 4, on all 15 rows with IoU ≥ 0.5. Thus IDs 3 and 4 initially coexist on different people. |
| 31–41 | ID 4 is reactivated on GT person 14 instead, on all 11 rows with IoU ≥ 0.5. |
| 50–51 | ID 4 is reactivated on yet another person, GT 117, with IoU 0.681 and 0.668. |
| 65–168 | ID 18 follows GT person 14 on all 78 emitted rows with IoU ≥ 0.5; missing-output intervals remain present. |

## Reference replay and association mechanism

- ID 3 last matches at frame 20 and becomes lost at 21. At frame 31 it is
  **still retained**; it is only removed at frame 35. Extending retention alone
  cannot explain or fix the already observed 3 → 4 misassociation.
- At frame 31, the detection best corresponding to GT 14 has score 0.665.
  ID 3's predicted box has zero inclusive IoU with it, giving assignment cost
  1.000 (outside the unchanged 0.9 limit). The lost ID 4 has inclusive IoU
  0.247 and score-fused cost 0.836; the assignment selects ID 4 and reactivates
  it on this detection.
- ID 4 loses GT 14 after frame 41. At frame 50 it is assigned a detection
  corresponding to GT 117 (detection/GT IoU 0.687), with score-fused cost
  0.819. This is another incorrect recovery of the old ID.
- ID 18 is created at frame 64 and confirmed/emitted at 65. ID 4 remains
  lost until removal at 66, with its last successful match at 51 now belonging
  to GT 117. The 4 → 18 observation is not simply expiration of a correctly
  tracked identity immediately before its return.

The frozen MOT17-05 override uses `track_buffer=14` and `frame_rate=30`, so
lost-track retention is 14 updates (approximately one second at source
14 fps). Replay source frames and tracker updates agree through this case.
The reference associates using motion-predicted boxes, overlap and detection
scores. This path does not use appearance matching or camera-motion
compensation. The inspected costs prove prediction/association failure;
the relative contribution of camera motion versus individual motion and
occlusion was not isolated by an experiment.

Observation hooks returned the original matching results unchanged. All
168 replayed frames' emitted IDs and rounded boxes match the stored C++
outputs exactly. Python/C++ segment comparisons also agree. This is a shared
tracking limitation, not a C++ port or demo-label error.

## Scope

No model, thresholds, buffer, demo labels or earlier results were changed.
Phase 3 fidelity acceptance remains distinct from continuous-identity quality.
Camera-motion compensation and appearance-assisted association are possible
future improvements, not tested fixes. Any variant requires an agreed
development/validation protocol; held-out MOT20 must not be tuned on.

## Reproduce

```sh
export PATH="$HOME/.docker/bin:$PATH"
scripts/drun.sh vision-lab:pytools -- python /work/python/analyze_mobile_case.py
```

This offline replay uses existing cached detections and the unmodified official
tracker. `phase-3-mobile-case-3-4-18.json` records input SHA-256 hashes,
per-row GT correspondence, reference state transitions, association costs
at frames 31/50, and the complete-demo replay equality check.
