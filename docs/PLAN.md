# Vision Lab — Work Plan

Status: **Phases 3–6 accepted by Opus; mean-shift bonus measured, separate review pending; accelerated INT8 repair unresolved** · Started 2026-10-06 · Target 2026-10-13

Review lead's [2026-10-08 verdict](reviews/phase-4-6-opus.md): measurements
accepted after the final follow-up; R-A, R-B and R-C resolved. The initial
requests were a MOT20 failure diagnosis and separately declared MOT17-selected
control, descriptive speed interpretation, and a short README/results index.
[Observed spread](../results/phase-6-between-run-spread.md)
includes both completed reruns. README and index have been rewritten; the
[new bounded experiment](PHASE4_REPAIR.md) preserves original INT8 failures.
It is complete: [diagnosis/control report](../results/phase-4-nano-repair.md).
Both mixed candidates fail MOT17; the fixed-weight floating control reaches
MOT20 MOTA 55.3158 (loss 0.7049 pp) but all three speed budgets fail >=1.3x.
Activation/bias effects are not separately isolated; no accelerated INT8
repair or baseline replacement is claimed. Twenty-five track hashes, 18 raw
benchmark runs, original report preservation and documentation links pass
the bounded final verification.
Opus's final review records the prior work committed, merged and pushed.
The subsequent mean-shift additions are uncommitted and outside that verdict;
their [review brief](reviews/phase-5-meanshift-handoff.md) is ready.

Detailed test plan and acceptance criteria: [01-phase-0-plan.md](01-phase-0-plan.md).
Detector: ByteTrack's YOLOX nano/tiny checkpoints (decided 2026-10-06).

Phase 4–6: [independent Codex review](reviews/phase-4-6.md), completed
2026-10-08 after explicit owner authorization for a separate read-only agent.

Review: [Opus verdict](reviews/phase-3.md); [follow-up verification](../results/phase-3-review-fixes.md).
The reviewer has not re-reviewed the follow-up changes. The separately
[predeclared continuity pilot](CONTINUITY_PILOT.md) and its
[results](../results/continuity-pilot.md) use exposed MOT17 development footage
and synthetic examples, not new held-out accuracy evidence. The accepted
baseline settings, outputs and demos stay unchanged. Owner-reported failures:
[pillar](../results/phase-3-occlusion-case-75-107.md),
[moving street](../results/phase-3-mobile-case-3-4-18.md).

Phase 4: [executor execution protocol](PHASE4_EXECUTION.md),
[complete measurements](../results/phase-4-performance.md),
[initial FP32 results](../results/phase-4-performance-fp32.md), and
[approved dependency installation](../results/phase-4-dependency.md). All 18 initial
FP32 runs completed with fixed warm-up/repeats/quotas. The owner authorized the
missing dependency on 2026-10-06; both INT8 models are generated using the same
112 MOT17 calibration frames. Paired speed tests and full MOT20 accuracy are
complete: 36 paired repeats and all 8,931 held-out MOT20 frames per model.
At four threads, nano FP32/INT8 measures 27.34/25.46 FPS and tiny 9.76/18.25 FPS.
Nano INT8 loses 56.1002 pp MOTA; tiny loses 1.0635 pp, above the fixed 1.0 pp cap.
Neither INT8 model is accepted at any tested budget; baseline unchanged.
[Read-only development diagnostics](../results/phase-4-int8-diagnostic.md) confirm
matching input preprocessing and identical original/preprocessed FP32 outputs
on three frames; the specific INT8 failure cause remains unisolated.
Final speed ratios use the paired matrix.

Phase 5: [executor protocol](PHASE5_EXECUTION.md),
[three-category failure report](../results/phase-5-failures.md), and
[beginner walkthrough](walkthrough/phase-5.md). Owner-reported MOT20-03
occlusion (75→107), MOT20-01 identity correspondence switch (13→22), and
small/truncated target detection misses each include frame intervals, crops,
per-frame GT/detection/track evidence and provenance. CLEAR audit counts match
upstream on the three scanned sequences. These are illustrative examples,
not frequency estimates or tuned improvements. Mandatory Phase 5 evidence is
complete; independent review supports the numerical case descriptions within
its stated limits (no new visual inspection or tracker-state replay).
The optional [mean-shift comparison](../results/phase-5-meanshift.md) now covers
all 8,931 MOT20 frames under the same TrackEval settings: MOTA −252.30,
IDF1 3.11, versus nano 62.42/53.31 and tiny 68.05/61.88. It receives annotated
first-appearance boxes but no later correction, scale adaptation or retirement;
drift and stale boxes remain failures. The 135.69 FPS sparse-clip timing is
illustrative, not a paired speedup or the shipping gate. The bonus has its own
[protocol](MEANSHIFT_EXECUTION.md); no new threshold, tuning or baseline
replacement. Its fresh-clone execution and independent review remain unverified.
Phase 6 full clean-clone reproduction has executed for the earlier scope.

Phase 6: [README](../README.md), [execution protocol](PHASE6_EXECUTION.md),
[historical snapshot record](../results/phase-6-reproduction.md),
[full clean-clone record](../results/phase-6-full-reproduction.md), and
[walkthrough](walkthrough/phase-6.md). One-command smoke/full profiles added;
the historical isolated source snapshot reproduces
both FP32 models' first-50-frame detections/tracks byte for byte and passes
Python/C++ synthetic behavior. Nano four-thread FPS 27.215 is inside the
original repeat interval; tiny 10.131 is outside, despite being faster, and
that strict check failure stays. Standalone root C++ dependency build succeeds
after the authorized download and produces identical 50-frame outputs.
Initial offline-build and mount failures remain recorded. Actual clean HEAD
clone was `6f0e68f` and lacked current Phase 3–6 source; that historical failure
is retained. Owner approved local commits and full reproduction on 2026-10-07.
Source/evidence commit `97d7177` failed before runtime on Bash 3.2 empty-array
handling. Fix commit `dcdb81e` was independently cloned with matching Git tree
and clean source, using copy-on-write licensed inputs. Full image builds,
fresh evaluator self-tests, all detection/tracking/evaluation stages, fixed
INT8 calibration, 36 paired benchmarks and failure crops executed. All FP32
and INT8 canonical scores and track hashes equal the reference. Strict speed
consistency passes 4/12 settings and fails 8/12, all above the old intervals;
no interval was widened. Four-thread FP32 nano/tiny medians are 28.134/10.298
FPS. Overall fresh-clone acceptance remains FAIL. No push performed. Cached
dependency layers were permitted; a cold installation remains unverified.
Independent evidence review was completed subsequently; its scope is linked
above. Earlier results in the main checkout remain unchanged.

Review follow-up: [executor evidence audit](../results/phase-6-audit.md)
recomputed 72 original/rerun benchmarks and verified 74 actual track files plus
three regenerated crops. Scores/hashes agree and the 8/12 failed speed checks
are correctly reported. [Reporting fixes](../results/phase-6-reporting-fixes.md)
close three output defects: full mode now generates current paired reports with
run/source identity, while interrupted builds invalidate current completion;
smoke removes obsolete uncommitted/unexecuted claims; Phase 4 separates report
generation time from the protocol date and explicitly unknown measurement times.
Thirteen bounded contracts and isolated report-date regeneration pass. The
subsequent [complete reporting-fix verification](../results/phase-6-reporting-full-verification.md)
ran once from clean commit `e3c4a83`, automatically producing current paired
reports. All quality scores and track hashes equal the original; 36 raw timing
files, 74 actual track files and three crops were checked. Speed consistency
passes 5/12 and fails 7/12: two below and five above the original intervals.
Overall acceptance remains FAIL, with no retrospective criterion change.
Historical `dcdb81e` results stay unchanged. Local source/evidence commits only;
no push. Owner explicitly authorized the separate read-only reviewer on
2026-10-08. Its implementation/evidence verdict passes within the reviewed
single-run reporting scope: R1, R2 and R4 are resolved, no new actionable defect
was established, and R3 remains open. Independently checked 108 existing timing
files, 150 archive hashes, 74 tracks, three crops and selected failure-case
source observations. No new experiment or replacement acceptance rule was
approved. See the paired [review result](../results/phase-4-6-independent-review.md).

## Goal

A one-week, reproducible study of **object detection + multi-object tracking on
CPU-only edge-class compute**, answering the same three questions as
[AI-Lab](https://github.com/hera2019/AI-Lab):

> Can this pipeline ship? What does it cost? How does it fail?

It provides evidence for: deep-learning vision, C++ inference (ONNX Runtime),
Linux, and Docker.

## Scope

- **Detection:** YOLOX nano (primary) and tiny, using the ByteTrack authors' pedestrian checkpoints.
- **Tracking:** ByteTrack-style association.
- **Inference:** model exported to ONNX and run from **C++ via ONNX Runtime**.
  Python is used for export, calibration, evaluation and reporting, and for
  the separate OpenCV mean-shift classical control.
- **Runtime:** everything runs inside a **Linux Docker container, CPU only**
  (Docker on macOS runs a Linux VM, so this stands in for an edge device).
- **Data:** public videos / MOT benchmark sequences with licenses recorded.

## Measurements

| Category | Metrics |
|---|---|
| Speed | FPS, per-frame latency (mean / p50 / p95), split into pre-process / inference / post-process / tracking |
| Cost | Peak RSS memory, model file size, CPU thread count used |
| Precision trade-off | FP32 vs INT8 (ONNX Runtime quantization): speed, size, and detection/tracking accuracy delta |
| Tracking quality | MOTA, IDF1 (HOTA if cheap), ID switches |
| Failure cases | Occlusion, ID switches, small objects — kept with frame references |

**Bonus:** a classical mean-shift tracker baseline, compared against
detection + tracking on the same sequences.

## Phases

| Phase | Work | Acceptance |
|---|---|---|
| 0 | Test plan; choose model, tracker, data; record licenses; Docker base image | Written plan with acceptance criteria before any model download |
| 1 | Export detector to ONNX; Python reference inference | ONNX output matches the source model within a stated tolerance |
| 2 | C++ ONNX Runtime detector inside Docker | C++ detections match the Python reference on fixed frames |
| 3 | Add tracker in C++; write MOT-format results | Tracking output scores with a standard evaluator (e.g. TrackEval) |
| 4 | Benchmark: FPS / latency / memory, FP32 vs INT8 | Results in `.md` + `.json`, re-runnable with one command |
| 5 | Failure-case analysis; mean-shift baseline (bonus) | Failure cases documented, negative results kept |
| 6 | README, license notes, one-command reproduction | Fresh clone → `docker build` + one run command reproduces the headline numbers |

## Method (inherited from AI-Lab)

1. Test plan first, with acceptance criteria.
2. Every result is reported twice: human-readable `.md` and machine-readable `.json`.
3. "It runs" is kept separate from "it passes".
4. Negative and unresolved results are kept.
5. Pinned versions, checksums, fixed seeds; model weights and datasets live outside the repository.

## Licensing notes (to verify in Phase 0)

- MOT17 / MOT20: non-commercial research use only.
- Ultralytics YOLO models: AGPL-3.0. YOLOX and RT-DETR (official repo): Apache-2.0.
- ByteTrack: MIT. ONNX Runtime: MIT.

## Out of scope

GPU / NPU acceleration, training or fine-tuning, multi-camera tracking.
