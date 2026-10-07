# Phase 6 reporting follow-up — report dates (R4)

Date: 2026-10-07. Author: Codex / GPT-6 (exact runtime model ID not exposed).

The Phase 4 generator now records the current report-generation timestamp in UTC and labels the original protocol date separately. Absolute measurement times are absent from the source timing files, so the measurement time range is explicitly unknown. Generation time is not experimental provenance.

An isolated regeneration using existing artifacts verified all original fields except the date are unchanged: 36 benchmark runs, 12 settings, all score/hash/memory/timing values and failed INT8 usefulness gates. The JSON lists compared fields and hashes of four protected historical reports, all unchanged.

Verification log: `phase-6-report-date-fix.log`. First launch failed because the Docker host does not share `/private/tmp`; its log is retained as `phase-6-report-date-fix-first-attempt.log`. Reading the same script from the already shared project directory succeeded with unchanged runtime protections.

This is executor verification of report metadata. No new inference, calibration, rescoring, benchmarks or full experiment ran. Historical full acceptance remains FAIL; independent review is pending.
