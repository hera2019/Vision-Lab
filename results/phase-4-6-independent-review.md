# Independent Phase 4–6 review

Reviewer: **Codex / GPT-6 (exact runtime model ID not exposed), independent read-only review agent**. Date: 2026-10-08.

Reviewed repository HEAD: `e161ef46342e37e85cebbefaa9d96f257e674dc9`. Reviewed implementation and recorded full-run source: `e3c4a83a0e6a461edbfbb2737cac274a31cbc46e`. The implementation files under `python/`, `scripts/` and `cpp/` have no differences between these revisions. Historical full-run evidence identifies `dcdb81e03533045764468305b8a3b07306f4ab98`.

**Verdict: implementation and evidence review passes within the stated single-run reporting scope. Numerical experimental acceptance remains FAIL. R1, R2 and R4 are resolved; R3 remains open. No new actionable implementation defect was established.**

This verdict reviews existing implementation and evidence. It does not accept failed numerical gates, approve a prospective timing protocol, or establish cold dependency installation, edge-device performance or product readiness.

## Findings and disposition

| Item | Severity | Disposition | Evidence and conclusion |
|---|---|---|---|
| R1 — stale full-run report/provenance | Original P1 | Resolved for the reviewed single-run workflow | [reproduce.sh](/Users/Hera/Documents/Vision-Lab/scripts/reproduce.sh:30) records a run ID, retains the previous report pair, and replaces current completion with `started-not-finalized` before builds. Its final stages invoke collection and finalization at lines 104–105. [report_phase6_full.py](/Users/Hera/Documents/Vision-Lab/python/report_phase6_full.py:17) rejects inconsistent run identity and checks source context, evaluator completeness, self-tests and numerical gates before writing the final pair. The recorded full run produced a current report and correctly exited 1. |
| R2 — obsolete smoke claims | Original P2 | Resolved | [phase6_smoke_report.py](/Users/Hera/Documents/Vision-Lab/python/phase6_smoke_report.py:91) reports actual source context and bounded smoke scope. Lines 104–115 explicitly limit what smoke establishes and avoid claiming that full mode has never executed. The existing targeted test and log support this correction; this reviewer did not execute another smoke experiment. |
| R3 — timing-method uncertainty | P2 | **Open** | [phase6_smoke_report.py](/Users/Hera/Documents/Vision-Lab/python/phase6_smoke_report.py:41) implements the fixed original three-repeat min/max rule. That operational rule is not a calibrated statistical interval. The explanation in [phase-6-audit.md](/Users/Hera/Documents/Vision-Lab/results/phase-6-audit.md:24) correctly states its hypothetical IID continuous-measurement assumptions. Independent rank enumeration confirms 8/20 outside-range outcomes under those assumptions. This is not a measured project false-failure rate. |
| R4 — fixed historical generation date | Original P2 | Resolved | [report_phase4.py](/Users/Hera/Documents/Vision-Lab/python/report_phase4.py:85) records current UTC generation time, retains the protocol date separately, and explicitly marks the absolute measurement range unknown. The regenerated report uses these labels. Historical reports remain unchanged. |

The previous-report backup uses one fixed directory at [reproduce.sh](/Users/Hera/Documents/Vision-Lab/scripts/reproduce.sh:33). Evidence establishes preservation of the immediately preceding report for the reviewed run and the recorded build-failure fixture. This review does not establish an unlimited archive across repeated generations. The clean-entry guards prevent treating an ordinary dirty-checkout retry as a supported workflow, so the fixed directory alone is insufficient to substantiate another defect.

## Independent checks performed

All computational checks used the unchanged `scripts/drun.sh`, existing `vision-lab:phase4-pytools`, `VL_RW=' '`, and Python with bytecode writes disabled. Consequently `/work` remained entirely read-only; the wrapper retained its offline, non-root, read-only-root and resource protections. Initial sandbox access to the Docker socket failed; authorized escalation succeeded.

The reviewer independently checked:

- **150 archived file hashes**, the generated report’s eight evidence hashes against actual clone files, and the four protected historical report hashes.
- **108 existing raw timing CSV files**: 36 original, 36 historical `dcdb81e`, and 36 current `e3c4a83`. Recomputed throughput and setting medians agree with their reports. Current metadata confirms frames 51–150, 50 warm-up frames, 100 measured frames, 608×1088 input, OpenCV one thread, and matching thread/CPU budgets.
- **74 actual regenerated track-file hashes and three actual crop hashes** in `data/phase-6-clean-e3c4a83`. Recorded FP32 and INT8 evaluator scores and track hashes equal the frozen references.
- Both recorded dataset self-tests pass. Source inspection confirms that full mode requests fresh evaluation; identical end-to-end output bytes permit documented reuse of the fresh C++ evaluation.
- **18 original Phase 5 source-file hashes and 74 selected observations**, checking GT boxes, visibility, resized height and associated prediction boxes against actual source files. The identity example has five ID-13 matches followed by five ID-22 matches. The small-target example satisfies its stated eight-frame numerical predicates. The upstream CLEAR source hash matches.
- Git revision/tree records, actual clone HEAD/tree, driver exit code, completion log, source-context/report identity, report-generation labels, and the targeted reporting-test source and recorded log.

The current speed result is **5/12 pass and 7/12 fail: two below the original interval and five above it**. The historical result remains **4/12 pass and eight above-range failures**. Faster out-of-range measurements correctly remain failed.

Both INT8 models retain failed usefulness conclusions at every tested budget. Recorded overall motmetrics MOTA losses are **56.1002 percentage points for nano** and **1.0635 for tiny**, both above the fixed 1.0-point cap. Scores reproducing exactly does not make those accuracy outcomes acceptable.

## Evidence boundaries

The Phase 5 reports appropriately present selected cases, not frequency estimates or proven unique causes. The source and observation checks support the numerical case descriptions. The prior occlusion-state report records the retention-limit diagnosis. This reviewer did not replay that tracker diagnosis, rerun the full CLEAR scan, independently rescore metrics, or visually inspect source photographs/crops. Therefore the report’s specific “head entering at the bottom image border” visual description remains executor-observed evidence, rather than a new reviewer visual finding.

No inference, benchmarks, recalibration, downloads, full experiments, UI operations or file modifications were performed. Existing executor measurements and regenerated outputs were reused for independent arithmetic, integrity and source review. The recorded 13-contract suite was inspected, not rerun.

R3 requires a prospective protocol specifying measurement conditions, sampling and uncertainty handling **before** new timing data are collected. This review approves no replacement threshold. Both historical and current failed experimental acceptance remain failed.
