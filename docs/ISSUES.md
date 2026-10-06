# Issues

Record each issue before changing code: observation, reproduction, proposed
minimal fix, status. Append; do not delete resolved entries.

## I-1 · Phase 1 raw-output tolerance is badly specified (open, accepted as-is)

- **Observed:** nano PyTorch vs ONNX Runtime max abs diff 1.18e-3 > 1e-3 on raw outputs.
- **Cause:** the criterion spans all 13,566 anchors; the worst diff is on a background anchor (score 7.8e-10). Diff is identical at every ORT optimisation level. On anchors with score > 0.1 the diff is ≤ 2.4e-5.
- **Decision:** keep "fail" on record; no re-scoring. Later criteria are stated on post-NMS detections. See `results/phase-1-export-parity.md`.

## I-2 · ByteTrack's official C++ tracker port differs from its Python tracker (known before Phase 3)

- **Observed (code reading, ByteTrack commit `d1bf019`):** `yolox/tracker/byte_tracker.py` applies `matching.fuse_score` (IoU similarity multiplied by detection score) in the first and the unconfirmed association when not MOT20. `deploy/ncnn/cpp/src/BYTETracker.cpp` has no equivalent.
- **Consequence:** a port copied from `deploy/ncnn/cpp` will not reproduce the Python results. Phase 3 must follow the Python tracker; any deviation is recorded here.

## I-3 · TrackEval master is incompatible with NumPy ≥ 1.24 (known before Phase 3)

- **Observed (code reading, TrackEval commit `12c8791`):** uses removed aliases `np.float`, `np.int` (e.g. `trackeval/datasets/mot_challenge_2d_box.py` lines 228, 359, 413, 420). The pytools image has NumPy 2.1.3.
- **Proposed minimal fix:** in our own runner, before importing TrackEval, set `np.float = float`, `np.int = int`, `np.bool = bool` if missing. Do not edit `external/TrackEval`. Verify by evaluating the ground truth against itself (expect MOTA = IDF1 = 100).

## I-4 · Phase 3 motmetrics NumPy-2 compatibility (resolved in our runner)

- **Observed by source inspection:** motmetrics 1.4.0 uses `np.asfarray`, removed in NumPy 2. ByteTrack also uses the `np.float` alias described in I-3.
- **Fix:** `python/phase3_common.py` supplies the aliases and equivalent floating-array conversion before importing the trackers/evaluators. External source trees remain unmodified.
- **Verified:** TrackEval ground-truth self-tests score 100 HOTA/MOTA/IDF1 on all MOT17 and MOT20 sequences; motmetrics successfully scores the first complete MOT17-02 sequence. See `results/phase-3/evaluation-self.json` and `parity-nano-MOT17-02-FRCNN.json`.
- **Build support:** `build-essential` and `python3-dev` were added to the pytools image to compile the pinned `cython_bbox==0.1.5`. `pandas` is required by motmetrics; `matplotlib` by TrackEval's import path. This adds no model or dataset download.

## I-5 · ByteTrack output serialization is not byte-identical (observed)

- **Observed:** ByteTrack's writer serializes rounded NumPy float32 scores as expanded decimal doubles (e.g. `0.8700000047683716`); the C++ writer uses two decimal places (`0.87`).
- **Effect:** On the first complete MOT17-02 nano sequence, IDs and all rounded box coordinates match exactly, but only 3.0% of literal lines match; maximum score representation difference is 2.87e-8. Both motmetrics scores are identical. Literal and numeric comparisons are reported separately, without normalizing away the literal mismatch.
- **Decision:** preserve the C++ MOT-format two-decimal score writer. Scores are not used by the fixed evaluation procedure beyond the confidence filter. Full-sequence comparisons remain to be measured.
- **Full-sequence correction after review (F3):** the small bound above describes the first MOT17-02 sequence, not every sequence. Across all 22 pairs, three rows at decimal-half boundaries differ by 0.01 (nano MOT20-02 and tiny MOT20-05) because NumPy float32 rounding and C++ decimal formatting differ. Frames, IDs and boxes are identical. Neither configured evaluator uses the emitted prediction score to compute these metrics. The final tables already retain the 0.01 maximum; it is not normalized away.

## I-6 · Tracker details preserved from Python (implementation notes)

- Association IoU uses inclusive pixel geometry (`+1`) from `cython_bbox`, rather than the detector's NMS geometry. Kalman arithmetic uses double precision, matching Python's `np.float` conversion.
- First and unconfirmed association fuse detection scores (I-2). The cost-limit assignment extends to a square matrix of size rows + columns with `limit/2` dummy costs, as `lap.lapjv` does.
- Empty-detection frames skip tracker updates; newly removed lost tracks remain in the lost list for one update, matching Python's list-update order. These quirks are deliberately preserved rather than corrected.
- Each sequence runs in a new process in both languages, making IDs local to the sequence. The upstream evaluator can carry its global ID counter across sequences; ID offset does not change within-sequence metrics. No thresholds are tuned.

## I-7 · Float32 score equality at thresholds (implementation correction)

- **Observed in review:** comparing a float32 detection score to a double C++ threshold can differ from NumPy's float32-array / weak-scalar comparison. Examples are scores exactly stored as float32 0.1, 0.6 or 0.7.
- **Reproduction:** the extended behavioral fixture gives an already tracked person scores of exactly 0.6 and 0.1, and introduces a person at exactly 0.7. The initial C++ implementation differed from Python. The pre-fix log is `results/phase-3/edge-cases-threshold-investigation.log`.
- **Fix:** compare scores to float32 threshold representations (including the new-track threshold), matching the pinned NumPy-2 reference. Numeric thresholds and tracker configuration stay unchanged.
- **Verification:** the rebuilt boundary fixture passes, with identical frame/ID order and box coordinates. Every cache for both models contains zero scores whose classification differs under the corrected comparisons. All C++ cache outputs were regenerated with the corrected build; all 22 end-to-end outputs match them byte-for-byte. See `results/phase-3/score-boundaries.json` and the final phase report.

## I-8 · Streaming shell driver edited while running (resolved; error retained)

- **Observed:** `phase3_track.sh --wait` wrote all 22 sequence/model results, then exited 2 with an unexpected-EOF quote error. It had been edited during execution; the failure is consistent with Bash reading a changed file at its old offset. The log is `results/phase-3/tracking-run.log`.
- **Correction:** the final on-disk script passes `bash -n`; all C++ cache outputs were regenerated using the completed script (nano separately, tiny in `phase3_finalize.sh`). Python loop metadata exists for every complete sequence. Both fixed MOT17 criteria pass and all final end-to-end files match regenerated C++ files byte-for-byte. No inference was skipped or metric re-scored to conceal this driver failure.

## I-9 · Temporary artifact encoder cannot execute from hardened tmpfs (resolved by image build)

- **Observed:** the first artifact-only H.264 encoder compiled in `/tmp` but execution was refused. The failure is retained in the first demo-encoding log.
- **Correction:** add an artifact-only CMake target and build its executable into the normal image. The existing container flags, tmpfs, mounts and network protections stay unchanged. No package, model or dataset was downloaded for video encoding; the already installed OpenCV video backend is used.

## I-10 · Dense-crowd pillar occlusion splits person 75 into 107 (confirmed limitation)

- **Owner report:** the person marked 75 on the right of the MOT20-03 nano demo becomes 107 after passing a pillar.
- **Measured:** both segments match GT person 169. Track 75 last matches at frame 141, becomes lost at 142, and is removed at 172 after exceeding the frozen 30-update retention. Track 107 starts at 179 and is first emitted at 180. The 38 missing output frames span 1.52 seconds at 25 fps. Python and C++ segment frames, IDs and rounded boxes agree.
- **Implication:** Phase 3 fidelity acceptance does not establish uninterrupted identity tracking under long occlusion. This is a shared reference/port limitation, not a demo color error.
- **Boundary:** no tuning on held-out MOT20. Longer retention and appearance-based re-identification remain unverified future variants requiring separate development/validation footage. No settings or previous results changed.
- **Evidence:** `results/phase-3-occlusion-case-75-107.md` and `.json`; reproducible offline cache replay in `python/analyze_occlusion_case.py`.

## I-11 · Moving-street demo transfers IDs across people: 3 → 4 → 18 (confirmed limitation)

- **Owner report:** one person in the MOT17-05 nano demo is marked successively 3, 4 and 18.
- **Measured:** GT person 14 corresponds to ID 3 initially, ID 4 at frames 31–41, and ID 18 from frame 65. ID 4 originally belongs to GT person 4 (frames 5–19) and later switches to GT 117 (50–51). Ambiguous overlap during full occlusion is preserved in the case JSON.
- **Mechanism:** at frame 31, ID 3 is still retained but its predicted box has zero overlap with the returning GT-14 detection; lost ID 4 is selected with score-fused cost 0.836 under the frozen 0.9 limit. Thus simply extending lost-track retention cannot resolve this example. Camera-motion compensation and appearance assistance are absent from the reference path; their benefits are not yet measured.
- **Verification:** unchanged official-reference replay produces identical frame/ID/box rows to C++ for the complete 168-frame demo. This is a shared association limitation. No model, tracking settings or prior results changed.
- **Evidence:** `results/phase-3-mobile-case-3-4-18.md` and `.json`; offline replay/probes in `python/analyze_mobile_case.py`.

## I-12 · Full-Dockerfile offline rebuild misses dependency cache (resolved without downloads)

- **Observed during F2:** setting `docker build --network=none` on the full Dockerfile missed the dependency-layer cache. Its apt layer failed with unavailable packages; the initial log is retained at `results/phase-3/review-fixes-build.log`.
- **Resolution:** `Dockerfile.review-fixes` reuses the accepted local `vision-lab:dev` runtime/toolchain and copies only C++ sources. The offline build succeeded with no package or model download; all hardened run flags stay unchanged.
- **Verification:** all 22 nano/tiny cache-tracker outputs are byte-identical to the accepted baseline and the behavioral fixture passes. See `results/phase-3-review-fixes.md` / `.json` and `review-fixes-offline-rebuild.log`.

## I-13 · ORT 1.30 quantization cannot import without ml_dtypes (resolved after owner-approved download)

- **Observed:** original pytools image has onnxruntime 1.30.0 and onnx 1.17.0, but importing `onnxruntime.quantization` fails with `ModuleNotFoundError: No module named 'ml_dtypes'`. The module imports float8/int4 types unconditionally even for the planned INT8 experiment. Local pip-cache checks found no matching wheel.
- **Prepared:** pinned/hash-checked `ml_dtypes==0.6.0` container-only proposal, no-deps/only-binary install; Linux ARM64 wheel 360.2 kB from PyPI. Existing NumPy/packages and host environment preserved. No package download or install has occurred.
- **Boundary:** asked owner because new downloads require approval; elapsed time is not approval. INT8 remains unmeasured. FP32 work proceeded independently: all 18 fixed benchmark runs completed and reported.
- **Evidence:** `results/phase-4-dependency.md` / `.json`, `results/phase-4/quantization-dependency-inspection.txt`, `Dockerfile.phase4-pytools`, `python/requirements-phase4.txt`.
- **Resolved after owner approval (2026-10-06):** the separately pinned/hash-checked image build installs only ml_dtypes 0.6.0; quantization import passes. Initial boundary records retained as `phase-4-dependency-initial.*`.

## I-14 · ORT calibration intermediate cap discards samples (corrected without data/scheme changes)

- **Observed:** initial nano quantization fails with `ValueError: No data is collected.` at `CalibMaxIntermediateOutputs=1`.
- **Source inspection:** installed ORT 1.30 MinMaxCalibrater clears intermediate outputs when the cap is hit, without computing/merging their range. A cap below the dataset size can silently omit earlier samples, so simply leaving a final nonempty batch would be invalid.
- **Correction:** cap 128 is above all 112 fixed MOT17 samples. Reader count equals 112 for each model; no cap flush occurs. Both models produce finite native-shaped outputs and preserve original FP32 hashes. Calibration images, scheme, thresholds and container memory limit unchanged; third-party source not edited.
- **Evidence:** `results/phase-4/quantization-first-attempt.log` / `.json`; successful `quantization-{nano,tiny}.json` and run log.

## I-15 · Safety probe assumed loopback was the only named interface (probe correction)

- **Observed:** the first protection probe fails an assertion because the VM kernel also exposes down tunnel devices in the isolated namespace.
- **Investigation:** UID 502, CapEff zero and NoNewPrivs 1 were correct; tunnel-interface flags show they are down, no active non-loopback interface or IPv4 route exists, and an external connection probe returns ENETUNREACH.
- **Correction:** validate actual connectivity constraints, not interface names alone. Runtime Docker flags and permissions unchanged. Root/project write probes and tmpfs direct-execution probe are denied; memory/pid/quota values match.
- **Evidence:** `results/phase-4/container-safety-first-attempt.json`, final `container-safety.md` / `.json`.

## I-16 · Static QDQ INT8 fails the frozen quality gate (negative result retained)

- **Measured:** complete MOT20, 8,931 frames per model with unchanged A1 settings. Nano MOTA drops from 56.0207 to -0.0795 (56.1002 pp loss), IDF1 from 51.3699 to 1.3235. Tiny MOTA drops from 61.0752 to 60.0117 (1.0635 pp loss), IDF1 from 59.4906 to 57.9299. Both fail the fixed <=1.0 pp MOTA-loss cap; tiny's faster throughput does not override its failed accuracy gate.
- **Read-only diagnosis:** fixed MOT17-02 frames 1/51/150, no MOT20 input. Official calibration/reference preprocessing agrees with an independent C++ formula within 4.77e-7. Original and preprocessed FP32 raw outputs are identical on these frames for both models. Nano INT8 emits many more boxes after NMS; disabling runtime optimization does not restore the original outputs/counts. Shapes and finite outputs alone were insufficient acceptance evidence.
- **Limit:** observations locate the change in the INT8 computation path on this development slice, not a specific operator or proven general cause. No alternative scheme search, threshold change, held-out recalibration, excluded layer, modified baseline or substituted acceptance result. Layer-level diagnosis is deferred.
- **Evidence:** `results/phase-4-performance.md` / `.json`, complete `phase-4/evaluation-int8.json`, `phase-4-int8-diagnostic.md` / `.json` and diagnostic run log.

## I-17 · Phase 6 clone lacks uncommitted source (open acceptance boundary)

- **Measured:** actual local clone of HEAD `6f0e68fbb5addcd0158330cb3bccb5a2641d8535` is clean but lacks README, reproduction entry point, C++ tracker and benchmark source. Working-tree Phases 3–6 are uncommitted. An independent source snapshot includes these files but is not a clone of committed history.
- **Boundary:** `PROJECT_RULES.md` requires the owner to request commits. No commit or push. Prepare reviewable source/docs/results first, then request a local commit before the full fresh-clone test. Full driver refuses dirty/untracked source and requires a disposable-clone declaration; numerical results never establish clone context by themselves.
- **Other limits:** smoke covers FP32 four threads, 50-frame outputs and synthetic behavior. Nano speed is within the old three-repeat interval; tiny is faster but outside its interval and retains a failed strict speed-consistency check. Fresh Python dependency installation and the full quality/INT8/budget matrix remain unexecuted. Ubuntu apt and Python transitive dependencies are not fully locked.
- **Evidence:** `results/phase-6-reproduction.md` / `.json`, clone inventory and raw timings under `results/phase-6/`.

## I-18 · Phase 6 isolated validation environment failures (corrected; failures retained)

- **Observed:** offline root Dockerfile build lacks the apt cache and fails; `/private/tmp` snapshot is not shared by this Docker host; a later snapshot run cannot create absent input-submount destinations under the read-only project mount.
- **Correction:** retained all logs; placed the independent snapshot under the already shared project's ignored data directory and created empty mount destinations before read-only mounting. No global Docker setting or runtime protection changed. Do not repeat the same offline build with unchanged inputs to chase a pass.
- **Standalone build:** after using existing owner download authorization for the original C++ dependencies and SHA-checked ORT, root build succeeds. Fresh root env_check passes, two models' first-50-frame detection/track outputs are byte-identical to frozen slices. This is not a fresh Python installation or a full-clone acceptance verdict.
- **Evidence:** first/mountpoint attempt logs, offline/network root-build logs, root-package/env records and `root-check.json` under `results/phase-6/`.

## I-19 · Full driver empty-array expansion on macOS Bash (corrected; failure retained)

- **Observed:** first full attempt from clean commit `97d7177` builds all images, then Bash 3.2 `set -u` rejects an empty optional mount array before preflight. No experimental stage ran.
- **Correction:** use the guarded optional-array form already used by unchanged `scripts/drun.sh`; empty and populated cases pass on the host Bash, with spaces retained. Commit correction and use another independent clean clone, without overlaying the failed one.
- **Evidence:** `results/phase-6-full-first-attempt.md` / `.json`, `results/phase-6/full-run-first-attempt.log`, Git clone proof.

## I-20 · Full clone reproduces quality, but strict speed gate fails (open review)

- **Measured:** complete clean-clone execution at `dcdb81e`. Matching source commit/tree, clean entry state, fresh evaluator procedure and ground-truth self-test pass. Every FP32/INT8 canonical evaluator score and track hash equals the original reference; failure crops regenerate.
- **Failed check:** 8/12 new benchmark medians are above their original three-repeat min/max intervals; 4/12 are inside. Four-thread FP32 nano/tiny are 28.134/10.298 FPS. Faster out-of-interval results still fail the preregistered consistency rule. Full driver exits 1 only at its final gate after all stages execute.
- **Boundary:** source availability in I-17 is resolved by owner-approved commits; its historical failure remains. Overall Phase 6 acceptance remains FAIL, not pending execution. No tolerance widening, favorable-repeat selection or tracker/model change. Independent review of evidence remains pending; cached builds do not establish a cold dependency installation.
- **Evidence:** `results/phase-6-full-reproduction.md` / `.json`, `results/phase-6/full-run.log`, preserved raw rerun metadata under `results/phase-6/full/`. Original Phase 3–5 evidence in the main checkout unchanged; no push.
