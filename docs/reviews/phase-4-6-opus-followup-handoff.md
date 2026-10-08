# Opus follow-up review handoff

Prepared by Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-08.
Executor summary, not a reviewer verdict. This supplements the earlier
[independent-review brief](phase-4-6-handoff.md) after
[Opus's R-A/R-B/R-C findings](phase-4-6-opus.md).

## Source and scope

Branch: `codex/vision-lab-reproduction`; HEAD: `e161ef4`. The new work is
**uncommitted**, including the earlier review/status files. Review the working
tree, not HEAD alone. Original Phase 0–2 code/results, fixed criteria,
`scripts/drun.sh`, original models and historical experiment reports remain
unchanged. The new post-hoc additions have not undergone clean-clone execution
or final independent review. No commit, merge or push was performed.

## R-A: diagnosis and bounded remedy/control

Read, in order:

1. [Frozen protocol and conditional control](../PHASE4_REPAIR.md).
2. [Diagnosis](../../results/phase-4-nano-diagnosis.md) and its JSON.
3. [Remedy/control report](../../results/phase-4-nano-repair.md) and its JSON.
4. `python/phase4_nano_repair.py`, `scripts/phase4_nano_repair.sh`, and
   [raw evidence](../../results/phase-4-repair/).

Findings and measurements:

- Selected MOT20 frames show high-confidence missed boxes. The same MOT17
  diagnostic frames show a 0.7163 stem step and all observed negative FP32
  activations rounding to zero. Outside-window values are not synonymous
  with integer-clamp saturation; the latter is negligible at that tensor.
- Head-FP32 and neck/head-FP32 candidates process all 5,316 MOT17 frames but
  fail development fidelity: MOTA 10.6681 and 37.3153.
- The conditional control retains all 113 original INT8 weight arrays/scales
  while restoring FP32 activations and biases. MOT17 MOTA/IDF1 losses are
  0.0570/0.4315 pp. Its hash/selection are recorded before a single full
  8,931-frame MOT20 evaluation.
- Control MOT20 MOTA/IDF1: **55.3158/51.8449**; MOTA loss **0.7049 pp**.
  Paired speed ratios at 1/2/4 threads: **1.030/0.995/0.969x**, from 18 fresh
  benchmark processes. All fail the original >=1.3x speed requirement.
- This is **INT8 weight storage with FP32 convolution computation**, not an
  accelerated INT8 solution. Restoring both activations and biases leaves
  their effects confounded; original bias dequantization error reaches
  0.013972. No individual causal layer is isolated. Original static INT8
  nano failure and accepted FP32 baseline remain unchanged.

Review questions:

- Do the graph instrumentation, corresponding tensor names and integer
  round/clamp calculations support the diagnosis without overclaiming cause?
- Do the archived protocols/model metadata/declarations support MOT17-only
  candidate selection and the chronology before the new MOT20 evaluation?
- Does the weight-control graph retain exact quantized weights, remove
  activation quantizers and preserve original FP32 biases/other operations?
- Are quality recovery, failed acceleration and causal limits clearly stated?

Useful raw records: `protocol-v1.md`, `protocol-control-at-build.md`,
`candidate-models.json`, `selection-original-candidates.json`, `selection.json`,
`evaluation-MOT17-original-candidates.json`, `evaluation-MOT17.json`,
`evaluation-MOT20.json`, `control-invariants.json`,
`bias-quantization-error.json`, `benchmark/`, and `final-verification.json`.
Full track/model files remain in ignored `data/phase-4-repair/`; reports record
their hashes. Inspect existing evidence before deciding whether new computation
is needed.

Execution limitations are retained: the first candidate build tried to write
an inferred helper beside a read-only input; the correction uses an identical
copy in the new writable directory. Editing the running development shell
caused a trailing exit 127 after both scores/null selection were saved.
Subsequent control and held-out/benchmark drivers exit 0. Diagnostic v1 and
initial link-check failure are archived; corrected checks pass.

## R-B: presentation follows the ruling

[Observed between-run spread](../../results/phase-6-between-run-spread.md)
includes both completed clean-clone reproductions: 24 comparisons over the
12 original settings, **-2.7261% to +5.7597%** from original speed medians.
Quality scores and track hashes reproduce exactly. Historical strict interval
failures are preserved; 6% is not a new acceptance threshold. This comparison
does not include the new weight-control benchmark as another full reproduction.
A prospective future timing protocol remains unwritten.

Review the arithmetic/source labels and consistency of README, PLAN, ISSUES,
Phase 6 protocol and walkthrough with your ruling. Earlier Codex review text
remains a dated historical verdict, not silently rewritten as an Opus verdict.

## R-C: reader-facing material

- [README](../../README.md): shorter purpose/results table, existing demo
  still, limitations and reproduction links.
- [Results index](../../results/README.md): grouped by phase; negative and
  historical reports retained.
- [Execution guide](../REPRODUCTION.md): earlier detailed process/audit notes
  moved out of the reader summary, with current interpretation at the top.
- [Phase 4](../walkthrough/phase-4.md) and
  [Phase 6](../walkthrough/phase-6.md): bilingual learning updates.
- `docs/images/mot17-tracking.jpg`: byte-identical existing MOT17-02 frame
  180 demonstration still; MOTChallenge attribution and CC BY-NC-SA 3.0 in
  README/LICENSES/assets. Models and datasets remain unbundled.

## Verification and next decision

Executor verification checks 25 actual new track hashes, 18 benchmark records,
three candidate-model hashes, weight-control graph invariants, preservation of
four old report hashes, unchanged pre-existing asset registration, shell/Python
syntax, changed document links and Git diff formatting. It reuses executor
measurements; it is not independent acceptance or a new full experiment.

Please record the actual checks, findings and limitations in your own final
review. Diagnose whether further work is required; do not call the floating
control an accepted INT8 acceleration repair. Current work is ready for that
review, not already approved. Local commit/merge/push remain separate owner
decisions; the owner has reserved approval of merge/push. This brief does not
schedule work, message another chat or authorize more experiments.
