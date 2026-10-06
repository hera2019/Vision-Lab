"""ByteTrack motmetrics procedure and unmodified TrackEval, with labelled results."""
import argparse
import hashlib
import importlib.metadata
import json
import shutil
import sys
import time
from pathlib import Path
from phase3_common import ROOT
import numpy as np
import motmetrics as mm

sys.path.insert(0, str(ROOT / 'external/TrackEval'))
import trackeval

mm.lap.default_solver = 'lap'

def sequences(benchmark):
    return sorted((ROOT / 'data' / benchmark / 'train').glob('*-FRCNN' if benchmark == 'MOT17' else 'MOT20-*'))

def motmetrics_score(benchmark, tracks):
    accumulators, names = [], []
    for seq in sequences(benchmark):
        gt = mm.io.loadtxt(seq / 'gt/gt.txt', fmt='mot15-2D', min_confidence=1)
        pred = mm.io.loadtxt(tracks / (seq.name + '.txt'), fmt='mot15-2D', min_confidence=-1)
        accumulators.append(mm.utils.compare_to_groundtruth(gt, pred, 'iou', distth=.5))
        names.append(seq.name)
    metrics = mm.metrics.create().compute_many(accumulators, names=names,
                    metrics=mm.metrics.motchallenge_metrics + ['num_objects'], generate_overall=True)
    return {name: {metric: (float(row[metric]) * 100 if metric in ('mota','idf1') else int(row[metric]))
                  for metric in ('mota','idf1','num_switches','num_false_positives','num_misses','num_objects')}
            for name, row in metrics.iterrows()}

def trackeval_score(benchmark, source, label):
    base = ROOT / 'data/phase-3/eval-input' / benchmark
    dest = base / label / 'data'
    dest.mkdir(parents=True, exist_ok=True)
    for seq in sequences(benchmark):
        shutil.copyfile(source / (seq.name+'.txt'), dest / (seq.name+'.txt'))
    seqmap = ROOT / 'data/phase-3' / (benchmark + '-seqmap.txt')
    seqmap.write_text('name\n' + '\n'.join(s.name for s in sequences(benchmark)) + '\n')
    data_config = {'GT_FOLDER': str(ROOT/'data'/benchmark/'train'),
                   'TRACKERS_FOLDER': str(base), 'OUTPUT_FOLDER': str(ROOT/'data/phase-3/eval-output'/benchmark),
                   'TRACKERS_TO_EVAL': [label], 'BENCHMARK': benchmark, 'SPLIT_TO_EVAL': 'train',
                   'SKIP_SPLIT_FOL': True, 'SEQMAP_FILE': str(seqmap), 'PRINT_CONFIG': False}
    evaluator = trackeval.Evaluator({'USE_PARALLEL': False, 'PRINT_CONFIG': False,
        'PRINT_RESULTS': False, 'DISPLAY_LESS_PROGRESS': True, 'TIME_PROGRESS': False,
        'OUTPUT_SUMMARY': False, 'OUTPUT_DETAILED': False, 'PLOT_CURVES': False,
        'LOG_ON_ERROR': None, 'BREAK_ON_ERROR': True})
    dataset = trackeval.datasets.MotChallenge2DBox(data_config)
    result, status = evaluator.evaluate([dataset], [trackeval.metrics.HOTA(),
                                  trackeval.metrics.CLEAR(), trackeval.metrics.Identity()])
    key = dataset.get_name()
    if status[key][label] != 'Success':
        raise RuntimeError(status[key][label])
    data = result[key][label]
    return {('OVERALL' if name == 'COMBINED_SEQ' else name): {
        'HOTA': float(np.mean(row['pedestrian']['HOTA']['HOTA']))*100,
        'MOTA': float(row['pedestrian']['CLEAR']['MOTA'])*100,
        'IDF1': float(row['pedestrian']['Identity']['IDF1'])*100,
        'IDSW': int(row['pedestrian']['CLEAR']['IDSW'])} for name,row in data.items()}

def self_test():
    output = {}
    for benchmark in ('MOT17', 'MOT20'):
        source = ROOT/'data/phase-3/self-test'/benchmark
        source.mkdir(parents=True,exist_ok=True)
        for seq in sequences(benchmark):
            gt = np.loadtxt(seq/'gt/gt.txt', delimiter=',', ndmin=2)
            gt = gt[(gt[:,6] == 1) & (gt[:,7] == 1)]
            np.savetxt(source/(seq.name+'.txt'), gt[:,:7],delimiter=',',fmt='%.10g')
        scores = trackeval_score(benchmark,source,'ground-truth-self')
        passed = all(abs(row[m]-100)<1e-8 for row in scores.values() for m in ('HOTA','MOTA','IDF1'))
        output[benchmark] = {'TrackEval': scores, 'pass': passed}
        if not passed:
            raise RuntimeError(f'Ground-truth self-test failed: {benchmark}: {scores}')
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--stage',choices=['self','parity','final'],required=True)
    p.add_argument('--benchmark',choices=['MOT17','MOT20'])
    p.add_argument('--model',choices=['nano','tiny'])
    p.add_argument('--fresh', action='store_true', help='Recompute metrics instead of reading earlier evaluator reports.')
    a=p.parse_args(); begin=time.perf_counter()
    if a.stage=='self':
        data=self_test()
    else:
        data={}
        implementations=['python','cpp'] if a.stage=='parity' else ['python','cpp','end-to-end']
        for benchmark in ([a.benchmark] if a.benchmark else ('MOT17','MOT20')):
            data[benchmark]={}
            for impl in implementations:
                data[benchmark][impl]={}
                for model in ([a.model] if a.model else ('nano','tiny')):
                    source=ROOT/'data/phase-3/tracks'/impl/model
                    hashes={s.name:hashlib.sha256((source/(s.name+'.txt')).read_bytes()).hexdigest()
                            for s in sequences(benchmark)}
                    cached=None
                    # A final collection can reuse an earlier measured evaluator
                    # output only when every input file hash still agrees.
                    if a.stage=='final':
                        for file in ([] if a.fresh else sorted((ROOT/'results/phase-3').glob('evaluation-*.json'))):
                            old=json.loads(file.read_text())
                            candidate=old.get('results',{}).get(benchmark,{}).get(impl,{}).get(model)
                            if candidate and candidate['sha256']==hashes:
                                cached={**candidate,'reused_from':file.name};break
                        if impl=='end-to-end' and data[benchmark]['cpp'][model]['sha256']==hashes:
                            cached={**data[benchmark]['cpp'][model],
                                    'reused_from':'cpp evaluation; all end-to-end file bytes identical',
                                    'sha256':hashes}
                    if cached:
                        data[benchmark][impl][model]=cached;scores=cached['scores']
                    else:
                        scores={'motmetrics':motmetrics_score(benchmark,source),
                                'TrackEval':trackeval_score(benchmark,source,impl+'-'+model)}
                        data[benchmark][impl][model]={'scores':scores,'sha256':hashes}
                    print(f'{benchmark} {impl} {model}: {scores["motmetrics"]["OVERALL"]}',flush=True)
    versions={x:importlib.metadata.version(x) for x in ['numpy','scipy','lap','cython_bbox','motmetrics','pandas','onnxruntime']}
    result={'stage':a.stage,'fresh':a.fresh,'seconds':time.perf_counter()-begin,'versions':versions,'results':data}
    suffix=''.join('-'+v for v in (a.benchmark,a.model) if v)
    out=ROOT/'results/phase-3'/f'evaluation-{a.stage}{suffix}.json'
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(f'wrote {out}',flush=True)

if __name__=='__main__':main()
