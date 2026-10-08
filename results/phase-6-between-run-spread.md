# Observed speed spread across completed sessions

Codex / GPT-6 (exact runtime model ID not exposed), 2026-10-08.

The original Phase 4 session and two complete clean-clone reproductions provide
three sessions, each with three fresh benchmark processes per setting. For the
12 unchanged model/precision/thread settings, the two rerun medians differ from
their original medians by **−2.7261% to +5.7597%**. This extends the historical
single-rerun comparison in [Opus's review](../docs/reviews/phase-4-6-opus.md).
Quality scores and track hashes reproduce exactly in both full runs.

This is descriptive observed spread, not a confidence interval, future
tolerance or new 6% acceptance rule. The original min/max-of-three gate failed
8/12 settings in the first full run and 7/12 in the second; those reports and
failures remain unchanged. Three repeats within a session do not measure
between-session variance. Opus's ruling changes presentation, not those scores.

[JSON](phase-6-between-run-spread.json) records all 24 paired comparisons and
source reports: [original](phase-4-performance.md),
[first full run](phase-6-full-reproduction.md),
[current reporting-source full run](phase-6-reporting-full-reproduction.md).
