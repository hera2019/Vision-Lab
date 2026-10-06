"""Unchanged evaluator procedures, with Phase 4 outputs kept separate."""
import csv
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
import numpy as np
from phase3_common import ROOT, sequence_info
from evaluate_tracking import motmetrics_score, sequences

sys.path.insert(0, str(ROOT/'external/TrackEval'))
import trackeval


def score_trackeval(source, label):
    base = ROOT/'data/phase-4/eval-input/MOT20'
    target = base/label/'data'
    target.mkdir(parents=True, exist_ok=True)
    for sequence in sequences('MOT20'):
        shutil.copyfile(source/(sequence.name+'.txt'), target/(sequence.name+'.txt'))
    seqmap = ROOT/'data/phase-4/MOT20-seqmap.txt'
    seqmap.write_text('name\n'+'\n'.join(s.name for s in sequences('MOT20'))+'\n')
    config = {'GT_FOLDER': str(ROOT/'data/MOT20/train'), 'TRACKERS_FOLDER': str(base),
        'OUTPUT_FOLDER': str(ROOT/'data/phase-4/eval-output/MOT20'),
        'TRACKERS_TO_EVAL': [label], 'BENCHMARK': 'MOT20', 'SPLIT_TO_EVAL': 'train',
        'SKIP_SPLIT_FOL': True, 'SEQMAP_FILE': str(seqmap), 'PRINT_CONFIG': False}
    evaluator = trackeval.Evaluator({'USE_PARALLEL': False, 'PRINT_CONFIG': False,
        'PRINT_RESULTS': False, 'DISPLAY_LESS_PROGRESS': True, 'TIME_PROGRESS': False,
        'OUTPUT_SUMMARY': False, 'OUTPUT_DETAILED': False, 'PLOT_CURVES': False,
        'LOG_ON_ERROR': None, 'BREAK_ON_ERROR': True})
    dataset = trackeval.datasets.MotChallenge2DBox(config)
    result, status = evaluator.evaluate([dataset], [trackeval.metrics.HOTA(),
        trackeval.metrics.CLEAR(), trackeval.metrics.Identity()])
    assert status[dataset.get_name()][label] == 'Success'
    return {('OVERALL' if name == 'COMBINED_SEQ' else name): {
        'HOTA': float(np.mean(row['pedestrian']['HOTA']['HOTA']))*100,
        'MOTA': float(row['pedestrian']['CLEAR']['MOTA'])*100,
        'IDF1': float(row['pedestrian']['Identity']['IDF1'])*100,
        'IDSW': int(row['pedestrian']['CLEAR']['IDSW'])}
        for name, row in result[dataset.get_name()][label].items()}


sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
baseline = json.loads((ROOT/'results/phase-3/evaluation-final.json').read_text())['results']['MOT20']['end-to-end']
measured = {}
for model in ('nano', 'tiny'):
    source = ROOT/'data/phase-4/tracks'/model
    hashes, counts = {}, {}
    for sequence in sequences('MOT20'):
        path = source/(sequence.name+'.txt')
        timings = list(csv.DictReader(path.with_suffix('.txt.timing.csv').open()))
        expected = int(sequence_info(sequence)['seqlength'])
        assert len(timings) == expected
        assert [int(r['frame']) for r in timings] == list(range(1, expected+1))
        assert all(int(r['threads']) == 4 for r in timings)
        values = np.loadtxt(path, delimiter=',', ndmin=2)
        assert np.isfinite(values).all() and (values[:, 0] >= 1).all() and (values[:, 0] <= expected).all()
        hashes[sequence.name] = sha(path)
        counts[sequence.name] = {'processed_frames': expected, 'emitted_rows': len(values)}
        old = ROOT/'data/phase-3/tracks/end-to-end'/model/path.name
        assert sha(old) == baseline[model]['sha256'][sequence.name], 'Stored baseline changed.'
    started = time.perf_counter()
    scores = {'motmetrics': motmetrics_score('MOT20', source),
              'TrackEval': score_trackeval(source, 'int8-'+model)}
    measured[model] = {'scores': scores, 'sha256': hashes, 'coverage': counts,
        'seconds_evaluation': time.perf_counter()-started,
        'baseline': baseline[model]['scores'],
        'overall_delta_pp': {
            'motmetrics': {m: scores['motmetrics']['OVERALL'][m]-baseline[model]['scores']['motmetrics']['OVERALL'][m]
                          for m in ('mota', 'idf1')},
            'TrackEval': {m: scores['TrackEval']['OVERALL'][m]-baseline[model]['scores']['TrackEval']['OVERALL'][m]
                          for m in ('MOTA', 'IDF1', 'HOTA')}}}
    print(json.dumps({'model': model, 'int8_overall': scores['motmetrics']['OVERALL'],
                      'delta_pp': measured[model]['overall_delta_pp']}), flush=True)
result = {'status': 'complete-held-out-int8-evaluation', 'threads': 4,
    'configuration': 'Frozen A1; original tracker; 608x1088; no tuning/recalibration.',
    'models': measured, 'baseline_evaluation': 'results/phase-3/evaluation-final.json',
    'baseline_evaluation_sha256': sha(ROOT/'results/phase-3/evaluation-final.json')}
(ROOT/'results/phase-4/evaluation-int8.json').write_text(json.dumps(result, indent=2)+'\n')
