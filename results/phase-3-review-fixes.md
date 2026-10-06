# Phase 3 review follow-ups

Date: 2026-10-06. Author: Codex / GPT-6 (exact runtime model ID not exposed).

All three non-blocking follow-ups in `docs/reviews/phase-3.md` are addressed
and checked by the executor. This is not a new independent review verdict.

- **F1:** expanded the walkthrough to English/Chinese paragraph pairs, covering
  tracker mechanics, both evaluators, fixtures, determinism, domain shift,
  labelled result tables, and the two owner-reported failures. New terms have
  a glossary. Earlier-phase explanations are not redefined.
- **F2:** expanded compressed statements and loops, replaced opaque type/local
  aliases with readable names, and added comments aligning stages with Python.
  Built a separate offline `vision-lab:review-fixes` image. All 22 nano/tiny
  complete-sequence cache-track outputs are byte-identical to the accepted
  C++ baseline. The behavioral fixture, including exact float32 boundaries,
  still passes against Python. No settings or arithmetic order changed.
- **F3:** clarified that the tiny representation-difference bound applied to
  the initial MOT17-02 sequence. Verified all three decimal-half boundary rows
  across nano MOT20-02 and tiny MOT20-05: score difference about 0.01, identical
  frames/IDs/boxes. Both configured evaluators ignore emitted prediction scores.
  Corrected I-5 and the report generator; original numeric result tables remain.

Verification uses existing detector caches; no model inference, asset download,
threshold tuning, or replacement of accepted track files was necessary.
Image/source/output provenance and the three score examples are in the paired JSON.

The first attempt to rebuild the full Dockerfile with network disabled missed
the dependency-layer cache and failed during package installation. Its log
is retained. `Dockerfile.review-fixes` instead reuses the accepted local
runtime image and installs nothing; this offline build succeeded.

Reproduce after building the separate image:

```sh
docker build --network=none -f Dockerfile.review-fixes -t vision-lab:review-fixes .
bash scripts/phase3_review_verify.sh
```

The baseline runtime image and original tracking outputs remain available.
