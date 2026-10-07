# Phase 6 — bounded reporting corrections

Author: Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-07.

**Executor verification complete. Independent review pending. Historical
full-experiment acceptance remains FAIL.**

The [evidence audit](phase-6-audit.md) recomputes 72 benchmark runs and verifies
74 regenerated track files plus three crops. Existing quality/hash claims are
supported, and all eight strict speed failures are above their old upper bounds.
No model inference, metric rescoring, benchmark retry or threshold change.

R1 corrected: the full command now records the entry Git revision/tree,
upstream revision, source cleanliness and run ID; automatically captures
standalone tracking-checkout context and generates its paired final reports.
The source-provenance check is separate from independent reviewer approval.
Previous reports are retained before replacement. An unfinished build/run is
explicitly not finalized, so it cannot display a previous completed result as
current. Final acceptance requires complete current numerical checks, complete
fresh evaluation, both evaluator self-tests and verified source context.

R2 corrected: smoke output describes the actual bounded run, source context and
generation date. It no longer says HEAD contains only Phases 0–2 or that full
mode is unexecuted. Smoke still cannot establish full acceptance.

Validation: 13 targeted contracts pass. They cover the archived eight-failure
outcome, a synthetic all-pass branch, dirty source, wrong upstream, stale run
identity, missing/empty/failed self-tests, reused metrics, missing benchmark
configuration, historical manual proof, current smoke scope, and a simulated
build failure preserving the previous report while invalidating current
completion. The real dirty-checkout guard rejects before builds/experiments.
Shell syntax and whitespace checks pass. An initial syntax typo in the test
fixture was corrected before the tests ran; no experimental result changed.

Logs: `phase-6-reporting-tests.log`, `phase-6-reporting-dirty-guard.log`.
These bounded checks do not establish a new full clean-clone experiment with
the changed reporter. The only completed full experiment remains source
`dcdb81e`, with its failed acceptance untouched. R3 timing-method review remains
open: any future uncertainty rule requires approval before new measurements.
No independent reviewer verdict or new Opus acceptance is claimed.
R4 corrected: Phase 4 reports label current UTC generation time separately
from the historical protocol date. Absolute measurement timestamps are absent
from the source timing files, so the measurement time range is explicitly
unknown. [Isolated report regeneration](phase-6-report-date-fix.md) verifies
all original fields except date unchanged, including 36 runs, 12 settings and
failed usefulness gates; four historical report hashes are preserved.
These edits are uncommitted review work.
