"""Keep source-snapshot smoke distinct from the frozen fresh-clone gate."""
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from compare_tracking import compare
from phase3_common import ROOT

mode = sys.argv[1]
base = ROOT/'results/phase-6'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
if mode == 'full':
    # Full mode has regenerated Phase 3 evaluation and Phase 4 reports.
    new = json.loads((ROOT/'results/phase-3/evaluation-final.json').read_text())
    old = json.loads((base/'reference-evaluation.json').read_text())
    for collection in (new, old):
        assert set(collection['results']) == {'MOT17','MOT20'}, 'Both datasets required'
        for dataset, implementations in collection['results'].items():
            assert set(implementations) == {'python','cpp','end-to-end'}
            for models in implementations.values():
                assert set(models) == {'nano','tiny'}
                for row in models.values():
                    assert len(row['sha256']) == (7 if dataset == 'MOT17' else 4)
                    assert set(row['scores']) == {'motmetrics','TrackEval'}
    assert new['fresh'] is True
    equality = all(new['results'][d][impl][model][key] == row[key]
        for d, implementations in old['results'].items() for impl, models in implementations.items()
        for model, row in models.items() for key in ('scores','sha256'))
    old_speed = json.loads((base/'reference-phase4.json').read_text())
    new_speed = json.loads((ROOT/'results/phase-4-performance.json').read_text())
    required = {(m,p,t) for m in ('nano','tiny') for p in ('fp32','int8') for t in (1,2,4)}
    for collection in (old_speed, new_speed):
        assert len(collection['settings']) == 12
        assert {(s['model'],s['precision'],s['threads']) for s in collection['settings']} == required
    budgets = []
    for s in old_speed['settings']:
        observed = next(v for v in new_speed['settings'] if all(v[k] == s[k] for k in ('model','precision','threads')))
        low, high = min(s['repeat_fps']), max(s['repeat_fps'])
        budgets.append({'model':s['model'],'precision':s['precision'],'threads':s['threads'],
            'median_fps':observed['median_repeat_fps'],'reference_interval':[low,high],
            'inside_interval':low <= observed['median_repeat_fps'] <= high})
    int8_equal = all(new_speed['int8_evaluation']['models'][model]['scores'] == old_speed['int8_evaluation']['models'][model]['scores']
        and new_speed['int8_evaluation']['models'][model]['sha256'] == old_speed['int8_evaluation']['models'][model]['sha256']
        for model in ('nano','tiny'))
    result = {'status': 'full-stages-executed', 'exact_evaluation_equal': equality,
        'int8_evaluation_equal':int8_equal, 'benchmark_settings':budgets,
        'numerical_reproduction_checks_passed':equality and int8_equal and all(s['inside_interval'] for s in budgets),
        'fresh_clone_gate_passed': False,
        'note': 'All full-driver stages executed. Independent Git clone provenance is required before accepting the fresh-clone gate.'}
    context_path = base/'source-context.json'
    if context_path.exists():
        result['run_id'] = json.loads(context_path.read_text())['run_id']
    (base/'full-check.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result)); sys.exit(0 if '--collect-only' in sys.argv or result['numerical_reproduction_checks_passed'] else 1)

reference = json.loads((ROOT/'results/phase-4-performance.json').read_text())
models = {}
for model in ('nano', 'tiny'):
    outputs = {}
    for kind, frozen in [('detections', ROOT/'data/phase-3/dets'/model/'MOT17-02-FRCNN.txt'),
                         ('tracks', ROOT/'data/phase-3/tracks/end-to-end'/model/'MOT17-02-FRCNN.txt')]:
        expected = b''.join(line for line in frozen.read_bytes().splitlines(keepends=True)
                            if int(line.split(b',', 1)[0]) <= 50)
        actual = ROOT/'data/phase-6'/f'{model}-{kind}.txt'
        assert actual.read_bytes() == expected, f'{model} {kind} first-50 slice differs'
        outputs[kind] = {'byte_identical': True, 'sha256': sha(actual),
            'reference_slice_sha256': hashlib.sha256(expected).hexdigest()}
    runs = []
    for repeat in (1, 2, 3):
        path = base/f'{model}-r{repeat}.csv'
        with path.open() as handle:
            rows = list(csv.DictReader(handle))
        meta = json.loads(path.with_suffix('.json').read_text())
        assert [int(r['frame']) for r in rows] == list(range(51, 151))
        assert meta['warmup'] == 50 and meta['measured'] == 100 and meta['threads'] == 4
        quota, period = map(int, meta['cpu_max'].split()); assert quota/period == 4
        times = np.array([float(r['end_to_end_ms']) for r in rows])
        assert np.isfinite(times).all() and (times > 0).all() and meta['peak_rss_kib'] > 0
        runs.append({'fps': float(100000/times.sum()), 'csv_sha256': sha(path), 'metadata': meta})
    old = next(s for s in reference['settings'] if (s['model'], s['precision'], s['threads']) == (model, 'fp32', 4))
    median = float(np.median([r['fps'] for r in runs])); low, high = min(old['repeat_fps']), max(old['repeat_fps'])
    models[model] = {'outputs': outputs, 'runs': runs, 'median_fps': median,
        'original_median_fps': old['median_repeat_fps'], 'original_repeat_interval': [low, high],
        'median_inside_original_repeat_interval': low <= median <= high}
edge = compare(ROOT/'data/phase-6/edge-python.txt', ROOT/'data/phase-6/edge-cpp.txt')
edge_pass = edge['same_frame_and_id'] and edge.get('max_box_difference', 0) <= .100001 and edge.get('max_score_difference', 0) < 1e-6
assert edge_pass
source_context = json.loads((base/'source-context.json').read_text()) if (base/'source-context.json').exists() else None
context = 'working-checkout' if (ROOT/'.git').exists() else 'source-snapshot'
result = {'status': f'local-{context}-smoke-complete', 'fresh_clone_gate_passed': False,
    'author': 'Codex / GPT-6 (exact runtime model ID not exposed)',
    'date': (source_context['captured_at_utc'] if source_context else datetime.now(timezone.utc).isoformat())[:10],
    'scope': f'Local {context}; reused read-only assets and installed toolchain, two FP32 models only.',
    'source_context': source_context,
    'models': models, 'edge_fixture': edge, 'edge_fixture_pass': edge_pass,
    'preflight': json.loads((base/'preflight.json').read_text()),
    'built_image': (base/'built-image.txt').read_text().strip(),
    'toolchain_image': (base/'toolchain-image.txt').read_text().strip(),
    'code_sha256': {str(p.relative_to(ROOT)): sha(p) for folder in ('cpp','python','scripts')
                   for p in sorted((ROOT/folder).rglob('*')) if p.is_file() and '__pycache__' not in str(p)},
    'limitations': ['This smoke run does not establish fresh dependency installation or full fresh-clone acceptance.',
                    'Only FP32 four-thread speed, 50-frame outputs and synthetic behavior checked; no new full-quality/INT8/1/2-thread replication.']}
(ROOT/'results/phase-6-reproduction.json').write_text(json.dumps(result, indent=2)+'\n')
lines = ['# Phase 6 — reproduction preparation and bounded smoke', '',
         f'**Status: local {context} smoke complete; full acceptance is outside this smoke scope.**', '',
         'Author: '+result['author']+'. Date: '+result['date']+'.', '', result['scope'], '',
         'Both models reproduce the frozen first-50-frame detection and track slices byte for byte. Fresh Python/C++ synthetic behavior agrees under the original fixture criteria. Native 608×1088 benchmarks retain 50 warm-up /100 measured frames, three repeats, four ORT threads and four-CPU quota. The strict speed check uses the original paired three-repeat FPS interval; a failure is not relaxed.', '',
         '| Model | Original median FPS | Original repeat min/max | New median FPS | New median inside original interval |',
         '|---|---:|---|---:|---|']
for model, m in models.items():
    lines.append(f'| {model} FP32 | {m["original_median_fps"]:.3f} | {m["original_repeat_interval"][0]:.3f}–{m["original_repeat_interval"][1]:.3f} | {m["median_fps"]:.3f} | {m["median_inside_original_repeat_interval"]} |')
lines += ['', 'This report describes only the current bounded smoke run. Source context is captured separately; a snapshot does not prove clean-clone provenance. Existing full-run evidence and historical acceptance remain separate. This smoke result makes no claim about whether full mode has executed. Earlier scores and files remain untouched.', '',
          'Source/model/image/output hashes, CPU quotas, repeats and peak process memory are in the JSON. Reproduce smoke with the installed images/assets: `bash scripts/reproduce.sh smoke`. See README for full prerequisites and limits.']
(ROOT/'results/phase-6-reproduction.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status': result['status'], 'models': {k: {'fps':v['median_fps'], 'speed_check':v['median_inside_original_repeat_interval']} for k,v in models.items()}, 'fresh_clone_gate_passed':False}), flush=True)
