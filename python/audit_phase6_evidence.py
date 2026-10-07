"""Bounded executor audit from raw existing files; no inference or rescoring."""
import csv
import hashlib
import itertools
import json
import math
import statistics
from pathlib import Path

ROOT = Path('/work')
ARCHIVE = ROOT/'results/phase-6/full'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
original = json.loads((ROOT/'results/phase-4-performance.json').read_text())
rerun = json.loads((ARCHIVE/'phase-4-performance.json').read_text())
benchmarks = []
for label, report, base in [('original', original, ROOT), ('rerun', rerun, ARCHIVE)]:
    observed = {}
    assert len(report['runs']) == 36 and len(report['settings']) == 12
    for record in report['runs']:
        path = base/record['timing_csv'] if label == 'original' else base/record['timing_csv'].removeprefix('results/')
        rows = list(csv.DictReader(path.open()))
        metadata = json.loads(path.with_suffix('.json').read_text())
        assert len(rows) == 100 and [int(row['frame']) for row in rows] == list(range(51, 151))
        assert metadata['warmup'] == 50 and metadata['measured'] == 100
        assert metadata['opencv_threads'] == 1 and metadata['peak_rss_kib'] > 0
        assert [metadata['input_height'], metadata['input_width']] == [608, 1088]
        quota, period = map(int, metadata['cpu_max'].split())
        assert quota/period == metadata['threads'] == record['threads']
        times = [float(row['end_to_end_ms']) for row in rows]
        assert all(math.isfinite(t) and t > 0 for t in times)
        assert sha(path) == record['timing_sha256']
        fps = 100000/math.fsum(times)
        assert math.isclose(fps, record['fps'], rel_tol=1e-12)
        key = (record['model'], record['precision'], record['threads'])
        observed.setdefault(key, []).append((record['repeat'], fps))
    for setting in report['settings']:
        key = (setting['model'], setting['precision'], setting['threads'])
        repeats = sorted(observed[key])
        assert [r for r, _ in repeats] == [1, 2, 3]
        fps = [value for _, value in repeats]
        assert math.isclose(statistics.median(fps), setting['median_repeat_fps'], rel_tol=1e-12)
        benchmarks.append({'collection': label, 'model': key[0], 'precision': key[1],
            'threads': key[2], 'repeat_fps': fps, 'median_fps': statistics.median(fps)})

old_eval = json.loads((ROOT/'results/phase-3/evaluation-final.json').read_text())
new_eval = json.loads((ARCHIVE/'phase-3/evaluation-final.json').read_text())
assert new_eval['fresh']
clone = ROOT/'data/phase-6-clean-dcdb81e'
files = 0
for dataset in ('MOT17', 'MOT20'):
    assert set(new_eval['results'][dataset]) == {'python', 'cpp', 'end-to-end'}
    for implementation in ('python', 'cpp', 'end-to-end'):
        for model in ('nano', 'tiny'):
            old = old_eval['results'][dataset][implementation][model]
            new = new_eval['results'][dataset][implementation][model]
            assert old['scores'] == new['scores'] and old['sha256'] == new['sha256']
            assert len(new['sha256']) == (7 if dataset == 'MOT17' else 4)
            if implementation != 'end-to-end':
                assert 'reused_from' not in new
            for sequence, digest in new['sha256'].items():
                assert sha(clone/'data/phase-3/tracks'/implementation/model/(sequence+'.txt')) == digest
                files += 1
for model in ('nano', 'tiny'):
    old = original['int8_evaluation']['models'][model]
    new = rerun['int8_evaluation']['models'][model]
    assert old['scores'] == new['scores'] and old['sha256'] == new['sha256']
    assert sum(v['processed_frames'] for v in new['coverage'].values()) == 8931
    for sequence, digest in new['sha256'].items():
        assert sha(clone/'data/phase-4/tracks'/model/(sequence+'.txt')) == digest
        files += 1
old_cases = json.loads((ROOT/'results/phase-5-failures.json').read_text())['cases']
new_cases = json.loads((ARCHIVE/'phase-5-failures.json').read_text())['cases']
assert set(new_cases) == set(old_cases) and len(new_cases) == 3
for key, case in new_cases.items():
    assert case['crop']['sha256'] == old_cases[key]['crop']['sha256']
    assert sha(clone/case['crop']['path']) == case['crop']['sha256']

speed = []
for new in [row for row in benchmarks if row['collection'] == 'rerun']:
    old = next(row for row in benchmarks if row['collection'] == 'original'
        and all(row[k] == new[k] for k in ('model', 'precision', 'threads')))
    low, high = min(old['repeat_fps']), max(old['repeat_fps'])
    speed.append({k: new[k] for k in ('model','precision','threads','median_fps')} | {
        'original_interval': [low, high], 'inside_interval': low <= new['median_fps'] <= high,
        'median_change_percent': (new['median_fps']/old['median_fps']-1)*100,
        'above_old_upper_percent': (new['median_fps']/high-1)*100})
assert sum(not row['inside_interval'] for row in speed) == 8
assert all(row['median_fps'] > row['original_interval'][1] for row in speed if not row['inside_interval'])

# Hypothetical IID continuous measurements: all 20 label orderings equally likely.
orders = []
for old_positions in itertools.combinations(range(6), 3):
    new_positions = [p for p in range(6) if p not in old_positions]
    orders.append({'old_ranks': old_positions, 'new_median_rank': new_positions[1],
        'inside': min(old_positions) <= new_positions[1] <= max(old_positions)})
rejected = sum(not row['inside'] for row in orders)
result = {'author': 'Codex / GPT-6 (exact runtime model ID not exposed)', 'date': '2026-10-07',
    'review_class': 'executor evidence cross-check; not independent approval',
    'reviewed_source_baseline': '7b5f978',
    'finding_scope': 'Source findings below were recorded against the pre-fix baseline; rerunning the arithmetic audit does not perform a new source review.',
    'scope': 'Existing raw artifacts only; no inference, tuning or benchmark retries.',
    'benchmarks_recomputed': 72, 'actual_track_files_hash_verified': files,
    'score_and_hash_equality': True, 'failure_crop_files_hash_verified': 3,
    'speed_settings': speed, 'strict_speed_failed': 8, 'strict_speed_passed': 4,
    'historical_acceptance_unchanged': 'FAIL',
    'hypothetical_rule_illustration': {'assumptions': 'Six IID continuous measurements; three old, three new; equally likely rank labelings. Not a project-data model.',
        'possible_orderings': len(orders), 'rejected_orderings': rejected,
        'rejection_fraction': rejected/len(orders), 'orderings': orders},
    'findings': [
        {'id': 'R1', 'priority': 1, 'status': 'confirmed-source-review',
         'summary': 'Full command omits final paired report/provenance collector; copied old reports may be mistaken for the current run.',
         'files': ['scripts/reproduce.sh','python/report_phase6_full.py']},
        {'id': 'R2', 'priority': 2, 'status': 'confirmed-source-review',
         'summary': 'Smoke reporter hardcodes source-uncommitted/full-unexecuted claims even on the current complete commit.',
         'files': ['python/phase6_smoke_report.py']},
        {'id': 'R3', 'priority': 2, 'status': 'method-review-needed',
         'summary': 'Three-repeat range is not a calibrated statistical acceptance interval. Existing verdict remains failed; any future rule requires review before new data.',
         'files': ['docs/PHASE6_EXECUTION.md']},
        {'id': 'R4', 'priority': 2, 'status': 'metadata-follow-up-open',
         'summary': 'Phase 4 subreport generator uses a fixed historical date even for rerun artifacts. Overall full-run provenance identifies the tested commit/date separately; future subreports should distinguish generation and measurement dates.',
         'files': ['python/report_phase4.py']}],
    'evidence_sha256': {str(p.relative_to(ROOT)): sha(p) for p in (ROOT/'results/phase-4-performance.json',
        ARCHIVE/'phase-4-performance.json', ARCHIVE/'phase-3/evaluation-final.json')}}
(ROOT/'results/phase-6-audit.json').write_text(json.dumps(result, indent=2)+'\n')
lines = ['# Phase 6 — executor evidence cross-check', '',
    'Author: '+result['author']+'. Date: 2026-10-07.', '',
    '**Independent approval remains pending. Historical overall acceptance stays FAIL.**', '',
    'Source findings describe baseline 7b5f978 before reporting fixes. See the separate reporting-fix report for current disposition; rerunning the arithmetic check is not a new source review.', '',
    'Independently recomputed arithmetic from 72 original/rerun benchmark CSV files; frame ranges, thread/CPU budgets and hashes pass. All FP32/INT8 evaluator scores equal their references. Verified 74 actual regenerated track files and three regenerated crop files against their recorded hashes. No new inference or scoring was run.', '',
    'Strict speed check: 4/12 pass, 8/12 fail. Every failure is above the original upper bound. This is not a measured slowdown or a changed quality result. Cause of the session shift is not isolated.', '',
    '## Reporting findings', '']
for finding in result['findings']:
    lines.append(f'- **{finding["id"]} (P{finding["priority"]})**: {finding["summary"]}')
lines += ['', '## Method illustration, not a replacement criterion', '',
    f'Under the hypothetical IID continuous-measurement assumptions, exhaustive enumeration gives {rejected}/{len(orders)} equally likely orderings in which the new three-repeat median is outside the original three-repeat min/max range. That is {100*rejected/len(orders):.0f}% even without an underlying distribution change. Actual VM/host timings can be correlated and do not establish these assumptions; this is not a measured project false-failure rate or significance claim.', '',
    'The predeclared rule and its eight failures are preserved. Review may specify a prospective timing protocol and uncertainty rule before collecting new measurements; no retrospective tolerance change or favorable-repeat selection is authorized.', '',
    'Reporter corrections can use existing artifacts and isolated missing/stale-evidence fixtures. Those checks do not rerun or accept the full experiment. Separate independent reviewer authorization/verdict remains required.']
(ROOT/'results/phase-6-audit.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k: result[k] for k in ('benchmarks_recomputed','actual_track_files_hash_verified','strict_speed_failed','historical_acceptance_unchanged')}), flush=True)
