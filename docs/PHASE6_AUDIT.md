# Phase 6 evidence audit protocol

Author: Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-07.

Owner requested the next review stage. This executor cross-check does not
replace an independent reviewer or an Opus verdict. A separate read-only
review agent requires explicit owner authorization and has been proposed.

Scope: read committed source and existing raw results; independently
recompute all 72 original/rerun benchmark FPS values from frame CSV files,
check warm-up exclusion, CPU/thread budgets, hashes and both evaluator score
collections, and verify full-run track files against recorded hashes. Audit
the documented command/report path. No new inference, downloads, GUI access,
held-out tuning, benchmark retries, changes to thresholds or historical
reports. All computational checks run through unchanged scripts/drun.sh.

Keep the existing strict three-repeat min/max rule and its failed verdict.
If useful, enumerate the finite orderings of three reference and three new
independent identically distributed continuous measurements to illustrate
the rule's behavior. This hypothetical calculation is neither a measured
project failure probability nor a replacement acceptance rule. Report raw
observations, assumptions and recommendations separately. Routine reporting
fixes may be implemented and checked with existing artifacts and isolated
fixtures; full experimental acceptance cannot be granted by those checks.

Deliver paired audit results, identified findings and bounded fix evidence.
Preserve existing accepted results. Independent approval and revised future
experimental criteria remain separate reviewer/owner decisions.
