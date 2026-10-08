# Results index

Reports link machine-readable evidence or a JSON companion. Negative results stay;
models, full track files and footage live in ignored `data/` directories.

| Phase | Main evidence | Follow-up / raw evidence |
|---|---|---|
| 0 · Environment | [Environment](phase-0-environment.md) | [Machine-readable checks](phase-0-env-check.json) |
| 1 · Export | [Export parity](phase-1-export-parity.md), including nano raw-tolerance failure | [Per-frame comparisons](phase-1-export-parity.json) |
| 2 · Detection | [C++ detector parity](phase-2-detector-parity.md) | [Per-frame checks](phase-2/) |
| 3 · Tracking | [Reference fidelity and MOT20 baseline](phase-3-tracking.md) | [Review fixes](phase-3-review-fixes.md), [evaluations](phase-3/) |
| 3 · Owner observations | [Pillar 75→107](phase-3-occlusion-case-75-107.md), [moving camera 3→4→18](phase-3-mobile-case-3-4-18.md) | [Development-only continuity pilot](continuity-pilot.md) |
| 4 · Performance / original INT8 | [Paired performance and held-out quality](phase-4-performance.md) | [Earlier FP32 measurements](phase-4-performance-fp32.md), [raw timing / calibration](phase-4/) |
| 4 · Dependencies / early diagnosis | [Approved dependency](phase-4-dependency.md), [initial failure](phase-4-dependency-initial.md) | [Earlier MOT17-only diagnostic](phase-4-int8-diagnostic.md); does not explain MOT20 collapse |
| 4 · Post-hoc nano investigation | [Remedy / floating diagnostic control](phase-4-nano-repair.md), [fixed-frame diagnosis](phase-4-nano-diagnosis.md) | [Protocol](../docs/PHASE4_REPAIR.md), [raw evidence](phase-4-repair/); quality restored within 0.705 pp, acceleration fails |
| 5 · Failure analysis | [Three documented cases](phase-5-failures.md) | [Raw evidence](phase-5/) |
| 5 · Classical control | [Mean-shift versus ByteTrack](phase-5-meanshift.md) | [JSON](phase-5-meanshift.json), [protocol](../docs/MEANSHIFT_EXECUTION.md), [raw evidence](phase-5-meanshift/); bonus review pending |
| 6 · Full reproduction | [Current tested reporting source](phase-6-reporting-full-reproduction.md), [verification](phase-6-reporting-full-verification.md) | [Archived raw run](phase-6/reporting-full/), [earlier full run](phase-6-full-reproduction.md) |
| 6 · Speed interpretation | [Observed between-run spread](phase-6-between-run-spread.md) | Original strict interval failures remain; [Opus ruling](../docs/reviews/phase-4-6-opus.md) |
| 6 · Reporting audit | [Arithmetic/hash audit](phase-6-audit.md), [reporting fixes](phase-6-reporting-fixes.md), [date fix](phase-6-report-date-fix.md) | [Read-only independent review](phase-4-6-independent-review.md) |
| 6 · Historical attempts | [Snapshot / old HEAD check](phase-6-reproduction.md), [local snapshot](phase-6-reproduction-local.md), [first full attempt](phase-6-full-first-attempt.md) | Historical failures preserved; not current full-run acceptance |

Interpretation and source navigation: [README](../README.md),
[reproduction guide](../docs/REPRODUCTION.md),
[fixed acceptance criteria](../docs/01-phase-0-plan.md),
[review lead's verdict](../docs/reviews/phase-4-6-opus.md),
[learning walkthroughs](../docs/walkthrough/).
