# Continuity pilot — development diagnostics

Date: 2026-10-06. Author: Codex / GPT-6 (exact runtime model ID not exposed).

**Bounded result:** translation compensation preserves ID 3 across the visible observations of the exposed person in this clip. Longer retention alone does not prevent the observed identity chain from changing. This is one development case, not evidence of general accuracy or a replacement for the accepted C++ baseline.

The settings were fixed in `docs/CONTINUITY_PILOT.md` before variant runs. Existing nano cache and MOT17-05 frames 1–168 only; no parameter search, MOT20 variant run, model download, or C++ improvement port. Original baseline inputs/outputs remain unchanged.

## Synthetic retention cases

A target appears in frames 1–3, disappears for frames 4–24, and a target appears from 25. A continuously detected anchor advances the tracker every frame. These are controlled synthetic examples, not videos or held-out accuracy.

| Synthetic case | 14-update retention | 42-update retention |
|---|---|---|
| same-person-same-position | ID 2 → 3; identity relation wrong | ID 2 → 2; identity relation correct |
| different-person-same-position | ID 2 → 3; identity relation correct | ID 2 → 2; identity relation wrong |
| same-person-displaced | ID 2 → 3; identity relation wrong | ID 2 → 3; identity relation wrong |

The same-person/same-position and different-person/same-position cases intentionally have byte-identical detector inputs (hashes checked). Longer retention correctly recovers the former but incorrectly assigns the old identity to the newcomer in the latter. Without additional evidence, retention cannot distinguish the two. A nonoverlapping return also fails even when the old identity is retained.

## Fixed MOT17-05 prefix — motmetrics development diagnostics

This training-seen, already inspected 168-frame prefix is not an independent validation set or a full-sequence result. The existing min_confidence=1, IoU distance=0.5 and lap scoring procedure is unchanged. The person-specific chain below uses GT person 14 only on annotated visible frames with box IoU ≥0.5; missing frames remain missing.

| Variant | MOTA | IDF1 | IDSW | FP | FN | Person 14 ID chain | Matching / visible frames |
|---|---:|---:|---:|---:|---:|---|---:|
| baseline | 51.10 | 65.36 | 10 | 95 | 587 | 3 → 4 → 18 | 31/33 |
| retention-42 | 51.52 | 65.60 | 8 | 110 | 568 | 3 → 4 → 12 | 31/33 |
| motion-14 | 51.73 | 69.80 | 3 | 94 | 586 | 3 | 30/33 |
| motion-retention-42 | 51.31 | 68.06 | 2 | 104 | 583 | 3 | 30/33 |

ID values are local to each run: a different final number alone is not an improvement. Both motion variants keep the exposed target on ID 3 when its box is matched, but detections are still missing in some frames. Longer retention with motion reduces the overall prefix switch count further, while increasing false positives and lowering IDF1 relative to motion alone. All four outcomes are retained; no winner was installed as the new baseline.

## Checks and limitations

- Baseline replay: all 168 frames’ emitted IDs and rounded boxes equal the stored C++ outputs.
- Motion checks: known translation recovered within 0.5 original-resolution pixels; blank input rejected; a known correction changes only the state center.
- Camera-motion estimates accepted on 142/167 frame pairs; rejected estimates fall back to identity. Detailed diagnostics and hashes are saved.
- The prototype estimates background translation with existing OpenCV features/optical flow/RANSAC. It does not handle full affine motion, appearance identity, or estimated-motion uncertainty.
- No measured claim about the MOT20 pillar case, general scenes, C++ speed, memory or INT8. Wider independent validation is still required.

Official API references: [optical flow](https://docs.opencv.org/4.x/dc/d6b/group__video__track.html), [affine estimation](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html).

## Reproduce

```sh
bash scripts/continuity_pilot.sh
scripts/drun.sh vision-lab:pytools -- python /work/python/report_continuity_pilot.py
```

The paired JSON contains all predeclared variants, protected-input/source-image/output hashes, synthetic cases, per-frame target correspondence, motion checks and dependency versions. Variant MOT outputs and motion diagnostics are under `data/continuity-pilot/`; no repaired labels or new demo is presented.
