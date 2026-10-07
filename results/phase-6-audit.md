# Phase 6 — executor evidence cross-check

Author: Codex / GPT-6 (exact runtime model ID not exposed). Date: 2026-10-07.

**Independent approval remains pending. Historical overall acceptance stays FAIL.**

Source findings describe baseline `7b5f978` before reporting fixes. See the
separate reporting-fix report for current disposition; rerunning the arithmetic
check is not a new source review.

Independently recomputed arithmetic from 72 original/rerun benchmark CSV files; frame ranges, thread/CPU budgets and hashes pass. All FP32/INT8 evaluator scores equal their references. Verified 74 actual regenerated track files and three regenerated crop files against their recorded hashes. No new inference or scoring was run.

Strict speed check: 4/12 pass, 8/12 fail. Every failure is above the original upper bound. This is not a measured slowdown or a changed quality result. Cause of the session shift is not isolated.

## Reporting findings

- **R1 (P1)**: Full command omits final paired report/provenance collector; copied old reports may be mistaken for the current run.
- **R2 (P2)**: Smoke reporter hardcodes source-uncommitted/full-unexecuted claims even on the current complete commit.
- **R3 (P2)**: Three-repeat range is not a calibrated statistical acceptance interval. Existing verdict remains failed; any future rule requires review before new data.
- **R4 (P2)**: Phase 4 subreport generator uses a fixed historical date even for rerun artifacts. Overall full-run provenance identifies the tested commit/date separately; future subreports should distinguish generation and measurement dates. This metadata follow-up remains open; historical files are not rewritten.

## Method illustration, not a replacement criterion

Under the hypothetical IID continuous-measurement assumptions, exhaustive enumeration gives 8/20 equally likely orderings in which the new three-repeat median is outside the original three-repeat min/max range. That is 40% even without an underlying distribution change. Actual VM/host timings can be correlated and do not establish these assumptions; this is not a measured project false-failure rate or significance claim.

The predeclared rule and its eight failures are preserved. Review may specify a prospective timing protocol and uncertainty rule before collecting new measurements; no retrospective tolerance change or favorable-repeat selection is authorized.

Reporter corrections can use existing artifacts and isolated missing/stale-evidence fixtures. Those checks do not rerun or accept the full experiment. Separate independent reviewer authorization/verdict remains required.
