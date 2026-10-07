"""Archive and cross-check the completed reporting-fix full run, without inference."""
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics

ROOT = Path('/work')
CLONE = ROOT/'data/phase-6-clean-e3c4a83'
ARCHIVE = ROOT/'results/phase-6/reporting-full'
load = lambda p: json.loads(p.read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
report = load(CLONE/'results/phase-6-full-reproduction.json')
proof = load(ARCHIVE/'host-clone-proof.json')
context = load(CLONE/'results/phase-6/source-context.json')
assert report['status'] == 'full-clean-clone-experiment-complete'
assert report['tested_source_commit'] == proof['source_commit'] == proof['clone_commit']
assert context['source_tree'] == proof['source_tree'] == proof['clone_tree']
assert report['run_id'] == context['run_id'] == (CLONE/'results/phase-6/run-id.txt').read_text().strip()
assert report['fresh_clone_context_passed'] and proof['clone_clean_after_assets']
assert report['fresh_evaluator_procedure_passed'] and report['ground_truth_self_test_passed']
assert not proof['source_overlay'] and not proof['historical_detection_or_tracking_overlay']
for relative, digest in report['evidence_sha256'].items():
    assert sha(CLONE/relative) == digest

original = load(ROOT/'results/phase-4-performance.json')
new = load(CLONE/'results/phase-4-performance.json')
assert len(new['runs']) == 36 and len(new['settings']) == 12
observed = {}
for record in new['runs']:
    timing = CLONE/record['timing_csv']
    with timing.open() as handle:
        rows = list(csv.DictReader(handle))
    meta = load(timing.with_suffix('.json'))
    assert [int(r['frame']) for r in rows] == list(range(51,151))
    assert meta['warmup'] == 50 and meta['measured'] == 100
    assert meta['opencv_threads'] == 1 and meta['peak_rss_kib'] > 0
    assert [meta['input_height'],meta['input_width']] == [608,1088]
    quota, period = map(int,meta['cpu_max'].split())
    assert quota/period == meta['threads'] == record['threads']
    times = [float(r['end_to_end_ms']) for r in rows]
    assert all(math.isfinite(t) and t > 0 for t in times)
    assert sha(timing) == record['timing_sha256']
    fps = 100000/math.fsum(times)
    assert math.isclose(fps,record['fps'],rel_tol=1e-12)
    key = (record['model'],record['precision'],record['threads'])
    observed.setdefault(key,[]).append((record['repeat'],fps))
for setting in new['settings']:
    key = (setting['model'],setting['precision'],setting['threads'])
    repeats = sorted(observed[key])
    assert [r for r,_ in repeats] == [1,2,3]
    median = statistics.median(value for _,value in repeats)
    assert math.isclose(median,setting['median_repeat_fps'],rel_tol=1e-12)
    check = next(row for row in report['full_checks']['benchmark_settings']
                 if (row['model'],row['precision'],row['threads']) == key)
    old = next(row for row in original['settings']
               if (row['model'],row['precision'],row['threads']) == key)
    assert check['reference_interval'] == [min(old['repeat_fps']),max(old['repeat_fps'])]
    assert math.isclose(check['median_fps'],median,rel_tol=1e-12)
    low,high = check['reference_interval']
    assert check['inside_interval'] == (low <= check['median_fps'] <= high)
assert new['date'] == new['report_generated_at_utc'][:10]
assert new['measurement_time_range_utc'] is None
assert new['report_generated_at_utc'] in (CLONE/'results/phase-4-performance.md').read_text()
assert not any(g['worth_it_per_fixed_gate'] for g in new['int8_usefulness_gates'])

old_eval = load(ROOT/'results/phase-3/evaluation-final.json')
new_eval = load(CLONE/'results/phase-3/evaluation-final.json')
assert new_eval['fresh']
files = 0
for dataset in ('MOT17','MOT20'):
    for impl in ('python','cpp','end-to-end'):
        for model in ('nano','tiny'):
            old = old_eval['results'][dataset][impl][model]
            current = new_eval['results'][dataset][impl][model]
            assert old['scores'] == current['scores'] and old['sha256'] == current['sha256']
            if impl != 'end-to-end':
                assert 'reused_from' not in current
            for seq,digest in current['sha256'].items():
                assert sha(CLONE/'data/phase-3/tracks'/impl/model/(seq+'.txt')) == digest
                files += 1
for model in ('nano','tiny'):
    old = original['int8_evaluation']['models'][model]
    current = new['int8_evaluation']['models'][model]
    assert old['scores'] == current['scores'] and old['sha256'] == current['sha256']
    assert sum(v['processed_frames'] for v in current['coverage'].values()) == 8931
    for seq,digest in current['sha256'].items():
        assert sha(CLONE/'data/phase-4/tracks'/model/(seq+'.txt')) == digest
        files += 1
assert files == 74
old_cases = load(ROOT/'results/phase-5-failures.json')['cases']
new_cases = load(CLONE/'results/phase-5-failures.json')['cases']
assert set(old_cases) == set(new_cases) and len(new_cases) == 3
for name,case in new_cases.items():
    assert case['crop']['sha256'] == old_cases[name]['crop']['sha256']
    assert sha(CLONE/case['crop']['path']) == case['crop']['sha256']
protected = load(ROOT/'results/phase-6-report-date-fix.json')['protected_report_sha256']
for relative,digest in protected.items():
    assert sha(ROOT/relative) == digest

exit_code = int((ARCHIVE/'driver-exit-code.txt').read_text())
assert exit_code == (0 if report['fresh_clone_gate_passed'] else 1)
old_report = load(CLONE/'results/phase-6/previous-full-report/report.json')
assert old_report == load(ROOT/'results/phase-6-full-reproduction.json')
assert report['run_id'] not in (None,old_report.get('run_id'))
assert report['full_checks']['exact_evaluation_equal'] and report['full_checks']['int8_evaluation_equal']

# Copy only report/raw metadata; large inference outputs remain in the disposable clone.
for phase,names in {
    'phase-3': ['evaluation-self.json','evaluation-final.json','environment.txt','image-versions.txt','python-environment.txt','edge-cases.json','thread-determinism.json','score-boundaries.json'],
    'phase-4': ['evaluation-int8.json','quantization-nano.json','quantization-tiny.json','int8-thread-check.json','environment.json','hardware.txt','all-image-versions.txt','container-safety.json','container-safety.md']
}.items():
    dest = ARCHIVE/phase; dest.mkdir(exist_ok=True)
    for name in names:
        source = CLONE/'results'/phase/name
        if source.exists():
            shutil.copyfile(source,dest/name)
shutil.copytree(CLONE/'results/phase-4/benchmark-paired',ARCHIVE/'phase-4/benchmark-paired',dirs_exist_ok=True)
for name in ['source-context.json','source-commit.txt','source-tree.txt','source-upstream.txt','source-origin.txt','source-status-before.txt','run-id.txt','preflight.json','full-check.json','python-environment.txt','external-revisions.txt']:
    shutil.copyfile(CLONE/'results/phase-6'/name,ARCHIVE/name)
for name in ['phase-4-performance.json','phase-4-performance.md','phase-5-failures.json','phase-5-failures.md']:
    shutil.copyfile(CLONE/'results'/name,ARCHIVE/name)
for suffix in ('md','json'):
    shutil.copyfile(CLONE/f'results/phase-6-full-reproduction.{suffix}',ROOT/f'results/phase-6-reporting-full-reproduction.{suffix}')
shutil.copytree(CLONE/'results/phase-6/previous-full-report',ARCHIVE/'previous-full-report',dirs_exist_ok=True)
result = {'date':datetime.now(timezone.utc).date().isoformat(),
    'author':'Codex / GPT-6 (exact runtime model ID not exposed)',
    'status':'automatic-full-reporting-verified',
    'tested_source_commit':report['tested_source_commit'], 'run_id':report['run_id'],
    'run_started_at_utc':(ARCHIVE/'run-started-at-utc.txt').read_text().strip(),
    'run_finished_at_utc':(ARCHIVE/'run-finished-at-utc.txt').read_text().strip(),
    'run_time_scope':'Host timestamps bound the whole driver execution; they are not per-benchmark absolute timestamps.',
    'host_clone_proof':proof,
    'complete_driver_executed_once':True, 'automatic_current_report_pair_generated':True,
    'previous_completed_report_retained':True,
    'fresh_clone_context_passed':True,'fresh_evaluator_procedure_passed':True,'self_test_passed':True,
    'raw_benchmarks_recomputed':36,'actual_track_files_hash_verified':files,'crop_files_hash_verified':3,
    'all_fp32_int8_scores_and_track_hashes_equal':True,
    'phase4_report_date_metadata_verified':True,
    'speed_settings_passed':report['speed_settings_passed'],'speed_settings_failed':report['speed_settings_failed'],
    'full_acceptance': 'PASS' if report['fresh_clone_gate_passed'] else 'FAIL',
    'driver_exit_code':exit_code,'historical_full_acceptance':'FAIL',
    'original_report_sha256_unchanged':protected,
    'independent_review':'Pending; these are executor results, not independent acceptance.',
    'cold_dependency_install_verified':False,'push_performed':False,
    'limitations':report['limitations'],
    'evidence_archive':'results/phase-6/reporting-full/',
    'automatic_report':'results/phase-6-reporting-full-reproduction.json'}
out = ROOT/'results/phase-6-reporting-full-verification'
out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
lines = ['# Phase 6 — complete verification of reporting fixes','',
    f'Author: {result["author"]}. Date: {result["date"]}.','',
    f'**Automatic reporting verified. Full experiment acceptance: {result["full_acceptance"]}.**','',
    f'Tested source `{result["tested_source_commit"]}`; run `{result["run_id"]}`. The unchanged full profile ran once from an independent clean clone with copy-on-write licensed input files and no historical detection/track overlay. No extra reviewer agent or push.','',
    f'All stages completed; the driver automatically emitted a current paired final report and exited {exit_code}. The previous completed report is retained separately. Current source/run identity, fresh evaluations, both self-tests and Phase 4 date labels are verified.','',
    f'Recomputed 36 raw benchmarks and verified 74 actual regenerated track files plus three crops. All FP32/INT8 canonical scores and track hashes equal the original reference. The strict speed rule passes {result["speed_settings_passed"]}/12 and fails {result["speed_settings_failed"]}/12. No retry, interval widening, favorable-repeat selection or baseline replacement. Original historical acceptance remains FAIL.','',
    'The original Phase 4 and completed historical Phase 6 report pairs remain byte-identical. The JSON retains their hashes. The generated follow-up report is [here](phase-6-reporting-full-reproduction.md); raw evidence and actual exit/start/finish records are under `phase-6/reporting-full/`. Large regenerated artifacts remain in the disposable clone.','',
    'This completes executor verification of the changed command/report path. Independent review and prospective timing-method review remain open; cached builds do not establish cold dependency installation.']
out.with_suffix('.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k:result[k] for k in ('status','tested_source_commit','raw_benchmarks_recomputed','actual_track_files_hash_verified','speed_settings_passed','speed_settings_failed','full_acceptance','driver_exit_code')}))
