# Phase 6 — first full clean-clone attempt

Author: Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-07.

Source commit `97d7177` was independently cloned with matching Git tree and
clean source. All documented image builds completed, including the separately
approved hash-checked ml_dtypes wheel. No experiment stage executed: macOS
Bash 3.2 with `set -u` rejected an empty optional-mount array expansion before
the first preflight container. Fresh-clone acceptance remains failed/pending.

Fix the optional-array expansion with the guarded form already used by
`scripts/drun.sh`, check both empty and populated cases, commit the correction
and rerun from a new clean clone. No input, threshold or runtime protection
changed. Build layers may be reused; this was not a forced cold dependency
installation. Raw log: `phase-6/full-run-first-attempt.log`; Git provenance:
`phase-6/full-clone-proof.json`. The paired JSON preserves this failed attempt.
