# Phase 6 — full clean-clone reproduction

**Experiment complete. Fresh-clone acceptance: FAIL.**

Author: Codex / GPT-6 (exact runtime model ID not exposed). Report generated (UTC): 2026-10-07T15:15:50.277349+00:00.

Tested source commit: e3c4a83a0e6a461edbfbb2737cac274a31cbc46e. Run: 20261007T133609Z-76914.

Clone context: True. Fresh evaluator procedure: True. Ground-truth self-test: True.

All FP32 canonical evaluator scores and track hashes equal the frozen reference: True. INT8 scores and track hashes equal the frozen reference: True.

All documented full-driver experiment stages completed. No benchmark retry, tuning, acceptance interval change or replacement baseline is implied by this report.

| Model | Precision | Threads / CPU quota | Original FPS interval | New median FPS | Within interval |
|---|---|---:|---|---:|---|
| nano | fp32 | 1 | 11.594–11.679 | 11.353 | False |
| nano | fp32 | 2 | 18.638–19.171 | 18.900 | True |
| nano | fp32 | 4 | 26.425–27.816 | 27.785 | True |
| nano | int8 | 1 | 15.070–15.349 | 14.864 | False |
| nano | int8 | 2 | 19.905–21.505 | 20.952 | True |
| nano | int8 | 4 | 24.045–25.992 | 25.832 | True |
| tiny | fp32 | 1 | 3.042–3.196 | 3.152 | True |
| tiny | fp32 | 2 | 5.400–5.829 | 5.956 | False |
| tiny | fp32 | 4 | 9.740–9.896 | 10.284 | False |
| tiny | int8 | 1 | 7.653–8.027 | 8.080 | False |
| tiny | int8 | 2 | 11.658–13.197 | 13.215 | False |
| tiny | int8 | 4 | 18.094–18.517 | 18.842 | False |

The original three-repeat min/max rule remains fixed. A faster out-of-interval result still fails; source provenance and quality equality do not override it.

This report describes the current disposable-clone run. Historical reports were retained before replacement; original main-checkout evidence stays separate. Raw evidence is in this checkout under results/phase-3/, results/phase-4/ and results/phase-6/.

Limitations: Cached Docker build layers are allowed; a cold dependency install is not established. Mac Docker Linux VM speed; no edge hardware or real-camera acceptance. Independent review remains separate; original INT8 failures remain failed.

The paired JSON records current run/source identity, individual gates and evidence hashes.
