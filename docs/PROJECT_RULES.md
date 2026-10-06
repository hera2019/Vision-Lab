# Shared project rules

`AGENTS.md` and `CLAUDE.md` both point here. Every agent working in this
repository follows the same rules.

## Roles

- **Owner:** decides scope, approves commits, downloads and anything irreversible.
- **Claude (Opus 5.5):** framework design, test plans, review. Writes the taskbook for each executor.
- **Executor (e.g. Sol 6.1):** carries out the current taskbook ([SOL6_TASKS.md](SOL6_TASKS.md)) and owns its changes and measured results.

## Attribution and reporting

- Append one row per change to [CHANGES.md](CHANGES.md): date, actual agent/model, files, reason, verification. Never sign for another agent or guess authorship.
- Distinguish proposals, observations, measurements and hypotheses. Never call an unexecuted command verified.
- Every result is reported twice: `results/<phase>-<name>.md` (human) and `.json` (machine). Negative and unresolved results stay. Superseded conclusions are kept with the reason.
- After each phase, write `docs/walkthrough/phase-N.md`: one English paragraph, then the same in Chinese; explain for a complete beginner; define every new term the first time it appears; end with a term table. Do not re-define terms from earlier walkthroughs.
- All public-facing content (README, docs, reports, commit messages) is in English. Conversation with the owner can be in Chinese.

## Measurement integrity

- Acceptance criteria in [01-phase-0-plan.md](01-phase-0-plan.md) are fixed. Do not change a threshold, metric, frame set or tracker setting to make a result pass. If a criterion looks wrong, write why in [ISSUES.md](ISSUES.md) and leave the decision to review.
- MOT17 train was seen in training: report it as fidelity only, never as accuracy. MOT20 train is held out: never tune anything on it.
- Code in `external/` (ByteTrack, TrackEval) is not edited. Compatibility shims live in our own code and are recorded in ISSUES.md.

## Execution environment

- Everything runs in Docker: `vision-lab:dev` (C++ build, target `build`) and `vision-lab:pytools` (Python, target `pytools`), mounted with `-v "$PWD:/work"`. Docker CLI: `export PATH="$HOME/.docker/bin:$PATH"`.
- Host: Apple M2 Max (8 performance + 4 efficiency cores), 32 GB RAM. Docker Desktop runs with **default settings**: VM with 12 vCPU and ~7.7 GiB RAM, no per-container limits. Do not change Docker Desktop's global settings.
- CPU budgets are set per run, never globally: ONNX Runtime threads via `--threads`; for benchmarks also `docker run --cpus=N` (and `--memory` where stated). Record the thread count in every output.
- Weights, datasets, videos and large intermediate files stay out of git (`models/`, `data/`, `external/`). Record source, revision, SHA-256 and license in [`assets.json`](../assets.json).
- Check free disk (`df -h ~`) before large runs; stop and report if below 10 GiB.

## Boundaries

- Download only what the current taskbook lists.
- Do not modify Phase 0–2 code or results. Propose changes in ISSUES.md.
- Commit only when the owner asks. Never push, force-push, or rewrite history.
- Do not reboot, quit other apps, or change system settings.
