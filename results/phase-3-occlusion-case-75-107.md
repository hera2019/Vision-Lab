# MOT20-03 nano: owner-reported identity switch 75 → 107

Date: 2026-10-06. Investigator: Codex / GPT-6 (exact runtime model ID not exposed).

**Confirmed failure:** the two track segments correspond to the same annotated
person, ground-truth ID 169. The owner identified the right-side pillar as the
occluder in the dense-crowd demo. Tracking that person continuously failed.

## Evidence

| Source frame | Measured event |
|---|---|
| 130 | Track 75 matches GT 169 with IoU 0.828; annotated visibility 0.674. |
| 141 | Last emitted box for 75; matches GT 169 with IoU 0.584; visibility 0.021. |
| 142 | Official reference marks 75 lost; last successful match remains frame 141. |
| 172 | Official reference marks 75 removed: 31 updates since its last match exceeds the frozen 30-update limit. |
| 179 | Official reference creates new, unconfirmed track 107. |
| 180 | First emitted box for 107; matches GT 169 with IoU 0.630; visibility 0.374. |

The video runs at 25 frames/s. Frames 142–179 have neither segment's emitted
box: 38 frames, or 1.52 seconds. The time between the last 75 box and first 107
box is 39 frames, or 1.56 seconds. The frozen reference configuration passes
`frame_rate=30` and `track_buffer=30`, retaining lost tracks for 30 tracker
updates (approximately 1.2 seconds in this clip). Replay confirms that tracker
update numbers equal source frame numbers through this event; an empty-frame
update skip does not explain it.

The disappearance outlasts retention. When detection returns, the old track
is already removed and the tracker assigns a new ID. This is an association
failure under occlusion, rather than a label/color rendering problem. The
official Python and C++ outputs have identical frames, IDs and rounded boxes
for both segments within the 300-frame demo.

## Acceptance scope and improvement boundary

Phase 3 acceptance establishes implementation fidelity to the official tracker
and the fixed aggregate metric criteria. It does not establish uninterrupted
identity tracking through all occlusions. This concrete negative example stays
alongside the accepted implementation results.

Longer lost-track retention and appearance-based re-identification are possible
improvement directions, not verified fixes. Longer retention can also attach
an old ID to the wrong nearby person. Any future variant needs separate
development/validation footage and both identity-switch and false-association
evaluation. MOT20 remains held out; no thresholds, model, tracking settings,
demo labels, or previous results were changed after observing this case.

## Reproduce

```sh
export PATH="$HOME/.docker/bin:$PATH"
scripts/drun.sh vision-lab:pytools -- python /work/python/analyze_occlusion_case.py
```

This replays the first 185 cached frames through the unmodified official
Python tracker without inference or network access. The paired
`phase-3-occlusion-case-75-107.json` contains input SHA-256 hashes, box/GT
correspondence, output endpoints and internal reference state transitions.
