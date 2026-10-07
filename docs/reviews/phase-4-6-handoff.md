# Phase 4–6 independent review handoff

Prepared by Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-08.
This is a review brief, not a reviewer verdict. The reviewer should not have
implemented the changes and must record their actual identity and methods.

## Start with the evidence

1. [Shared rules](../PROJECT_RULES.md) and [work plan](../PLAN.md): fixed criteria,
   attribution and data boundaries.
2. [Reporting-fix full verification](../../results/phase-6-reporting-full-verification.md)
   and its paired JSON: tested commit, actual driver exit, raw timing/hash checks
   and links to the automatically generated current report.
3. [Original Phase 4](../../results/phase-4-performance.md),
   [Phase 5](../../results/phase-5-failures.md), and
   [historical full reproduction](../../results/phase-6-full-reproduction.md):
   these remain separate from the new reporting verification.
4. [Executor audit](../../results/phase-6-audit.md),
   [reporting corrections](../../results/phase-6-reporting-fixes.md), and
   [date verification](../../results/phase-6-report-date-fix.md).

## Questions requiring an independent conclusion

- Do the actual source/clone/run records and fresh evaluations support the
  current reports, including the failed speed checks and INT8 accuracy gates?
- Does `scripts/reproduce.sh full` preserve old reports, invalidate completion
  on interrupted runs, and automatically write the current final pair? Inspect
  `phase6_context.py`, `phase6_smoke_report.py`, `report_phase6_full.py`, and the
  bounded test evidence. Source provenance is not reviewer approval.
- Do Phase 4 generation dates remain distinct from protocol dates and unknown
  measurement timestamps? Do the three Phase 5 examples support only their
  stated case-specific claims?
- R3 remains a method question: the three-repeat range is an operational rule,
  not a calibrated statistical interval. Review the audit's hypothetical rank
  enumeration and its explicit assumptions. Any proposal for future timing
  measurements must be specified before collecting new data; historical
  failed acceptance remains failed.

## Scope and output

Read source, recorded raw timings and existing artifacts first. No new full
experiment is needed merely to start review. No tuning, benchmark retries,
new downloads, interface control or historical-result edits are authorized by
this brief. Use unchanged `scripts/drun.sh` if computational checks are needed;
record any fixture or executor-data reuse rather than calling it independent
measurement. Extra agents require explicit owner authorization.

Write the independent verdict under `docs/reviews/` with findings, evidence,
what was actually checked, and limitations. Distinguish review of implementation
and evidence from experimental acceptance, prospective method approval, cold
dependency installation and real-device readiness. This brief grants no new
acceptance and attributes nothing to an absent reviewer.
