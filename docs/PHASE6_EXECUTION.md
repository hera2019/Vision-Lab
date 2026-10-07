# Phase 6 execution protocol — reproduction

Author: Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-07.
Owner authorized the next stage. Frozen requirement: a fresh clone and
documented commands reproduce headline results within run-to-run variance.
This executor protocol is not an independent review or an Opus taskbook.

## Scope and preserved boundary

Add README, one-command driver, input preflight, smoke result/report and a
bilingual walkthrough. Build and run without GUI access, new assets, tuning,
pushes. All runtime containers use unchanged `scripts/drun.sh`.
Leave earlier results, datasets, models and external code untouched.

Current HEAD contains only Phases 0–2; Phases 3–5 are uncommitted. A local
clean clone must be inspected and this source-availability failure retained.
Do not label an overlaid clone or source archive as a successful fresh clone.
Commit requires a separate owner instruction under PROJECT_RULES.md.

Owner approval received on 2026-10-07: commit the completed source and evidence
locally, then execute full reproduction in an independent clone of that commit.
The source-availability failure above describes the earlier attempt and stays
in the historical reports. No push is authorized. Full mode creates its output
directories before protected mounts, reruns the evaluator self-test, and uses
`--fresh` to recompute scores rather than reading historical evaluator reports.
An end-to-end score may reuse a newly computed cached-tracker evaluation only
when all corresponding output bytes agree. Original quality/settings/variance
intervals are unchanged. Clone provenance and full-run evidence will be stored
separately from the earlier snapshot report, including failed acceptance checks.

## Bounded local validation

Make an isolated, hashed source snapshot outside the working checkout, without
Git metadata or large assets. Exclude recursive reproduction outputs. Reuse
existing models, datasets and pinned external sources by explicit read-only
submounts. Only new snapshot results/data/phase-6 outputs writable.

Build current C++ from the existing local toolchain image offline. Separately
try the root Dockerfile's build target offline; preserve cache/network failure
if it cannot build. A local-toolchain build is not a fresh dependency build.

Smoke: env_check, official-reference behavioral fixture, first 50 MOT17-02
frames through C++ detector and tracker for nano/tiny FP32, compare exactly
to frozen detection/track rows; native 608×1088 benchmark at four threads and
matching four-CPU quota, 50 warm-up plus 100 measured frames, three repeats
per model. No simultaneous inference. Compare new median FPS to the original
paired FP32 three-repeat min/max interval. Outside the interval is recorded
as a failed strict smoke speed check, not used to widen the criterion.

Preflight verifies ONNX hashes, external Git revision, representative image
hash and required files. Record image ID, source/input/output hashes, CPU,
memory, package/build limitations. Smoke does not replace full quality or
1/2-thread/INT8 replication. Full driver reuses documented original stages
only in a clean checkout, archives original reference reports first, and
keeps smoke/full status distinct. No download command is hidden in runtime.

## Deliverables

`README.md`, `scripts/reproduce.sh`, source-snapshot validation script,
`results/phase-6-reproduction.md` / `.json`, raw logs/manifests,
`docs/walkthrough/phase-6.md`, PLAN/CHANGES/ISSUES updates. Report the fresh
clone gate as pending until the complete source can be cloned and tested.
Prepare all reviewable work before asking for the commit needed for that gate.

## Reporting audit follow-up — 2026-10-07

Owner requested the next review stage. The executor [audit](PHASE6_AUDIT.md)
checks existing evidence without another full run. Full mode now preserves the
previous final reports, marks a started run not finalized, records source/run
identity and automatically finalizes paired reports after all stages. Only the
final aggregate gate decides its numerical exit code. Missing/incomplete or
stale evidence cannot be accepted. The automated source-context check requires
a clean standalone Git directory, no object alternates, recorded origin and
HEAD matching its tracked upstream revision, plus the disposable-clone
declaration. It does not replace independent reviewer approval. Smoke reports
their bounded actual context rather than hardcoded historical source states.
Original min/max intervals and failed outcomes remain unchanged. Targeted
fixture verification does not establish another full clean-clone experiment.

## Reporting-fix full verification — 2026-10-07

The owner requested continuation of the remaining work after the bounded fixes.
Within the existing local-commit/full-reproduction scope, save the reviewed
source locally and run the unchanged full profile once in a new independent
clone. No push or extra reviewer agent is included. Preserve the original
`dcdb81e` experiment, all frozen references and speed intervals. This run
verifies automatic final report collection and current run/source/date labels;
its result is a separate follow-up, including any failed acceptance checks.
Use copy-on-write regular-file assets with no historical detection/track overlay.
Retain entry commit/tree/clean status and the driver's actual exit code.
Existing build caches are permitted; no cold-install claim. Record the new
report pair and raw evidence separately under `results/phase-6/reporting-full/`.

Completed 2026-10-08 (Japan local date), source `e3c4a83`. Host UTC driver
envelope: 2026-10-07 13:36:09–15:15:50; these bound the whole driver, not each
benchmark's absolute measurement time. All stages execute and automatic paired
report collection succeeds. Canonical quality and track hashes reproduce;
speed consistency passes 5/12 and fails 7/12. The driver exits 1 at the final
aggregate gate. No retry or acceptance-rule change. The original experiment
stays separate; independent review and future timing-method decisions remain
open. See the follow-up verification report and review handoff.
