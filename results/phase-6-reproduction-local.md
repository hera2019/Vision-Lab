# Phase 6 — reproduction preparation and bounded smoke

**Status: local source-snapshot smoke complete; fresh-clone acceptance pending.**

Author: Codex / GPT-6 (exact runtime model ID not exposed). Date: 2026-10-07.

Isolated source snapshot; reused read-only assets and installed toolchain, two FP32 models only.

Both models reproduce the frozen first-50-frame detection and track slices byte for byte. Fresh Python/C++ synthetic behavior agrees under the original fixture criteria. Native 608×1088 benchmarks retain 50 warm-up /100 measured frames, three repeats, four ORT threads and four-CPU quota. The strict speed check uses the original paired three-repeat FPS interval; a failure is not relaxed.

| Model | Original median FPS | Original repeat min/max | New median FPS | New median inside original interval |
|---|---:|---|---:|---|
| nano FP32 | 27.344 | 26.425–27.816 | 27.215 | True |
| tiny FP32 | 9.757 | 9.740–9.896 | 10.131 | False |

The source snapshot is not a clean Git clone. HEAD currently contains only Phase 0–2; actual clone inventory is recorded separately. Earlier scores and files remain untouched. Snapshot outputs are copied back as new Phase 6 records only. Full mode is prepared but unexecuted; it requires committed source, staged licensed inputs, explicit dependency-build networking when no cache exists, and considerable CPU time. Fresh-clone acceptance and independent review remain pending.

Source/model/image/output hashes, CPU quotas, repeats and peak process memory are in the JSON. Reproduce smoke with the installed images/assets: `bash scripts/reproduce.sh smoke`. See README for full prerequisites and limits.
