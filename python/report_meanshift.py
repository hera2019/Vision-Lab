"""Report the fixed mean-shift bonus without changing original evidence."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from phase3_common import ROOT

RAW=ROOT/'results/phase-5-meanshift'
BASE=ROOT/'data/phase-5-meanshift'
AUTHOR='Codex / GPT-6 (exact runtime model ID not exposed)'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())


def timing_summary(path):
    rows=list(csv.DictReader(path.open()))
    values=np.asarray([float(x['end_to_end_ms']) for x in rows])
    assert np.isfinite(values).all() and (values>0).all()
    return {'frames':len(rows),'fps':float(1000/np.mean(values)),
        'mean_ms':float(np.mean(values)),'p50_ms':float(np.quantile(values,.5)),
        'p95_ms':float(np.quantile(values,.95)),
        'mean_active_tracks':float(np.mean([int(x['active_tracks']) for x in rows])),
        'max_active_tracks':max(int(x['active_tracks']) for x in rows),
        'timing_sha256':sha(path)}


def main():
    evaluation=read(RAW/'evaluation.json')
    assert evaluation['original_baselines_exact']
    baseline=read(ROOT/'results/phase-4-performance.json')
    sequences={}
    for path in sorted((BASE/'tracks').glob('MOT20-*.json')):
        if path.name.endswith('.seeds.json'):continue
        meta=read(path);name=meta['sequence']
        assert sha(BASE/'tracks'/f'{name}.txt')==meta['tracks_sha256']
        timing=timing_summary(BASE/'tracks'/f'{name}.timing.csv')
        assert timing['frames']==meta['processed_frames']
        seeds=read(BASE/'tracks'/f'{name}.seeds.json')
        assert len(seeds)==meta['initialized_tracks']
        sequences[name]={'metadata':meta,'timing':timing,'seeds_sha256':sha(BASE/'tracks'/f'{name}.seeds.json')}
    assert len(sequences)==4 and sum(x['metadata']['processed_frames'] for x in sequences.values())==8931
    runs=[]
    for repeat in (1,2,3):
        path=RAW/'benchmark'/f'r{repeat}.csv'
        meta=read(path.with_suffix('.json'))
        assert meta['cpu_max']=='100000 100000' and meta['opencv_threads']==1
        rows=list(csv.DictReader(path.open()))
        assert [int(x['frame']) for x in rows]==list(range(51,151))
        runs.append({'repeat':repeat,'metadata':meta,**timing_summary(path)})
    originals={row['model']:row for row in baseline['settings']
               if row['precision']=='fp32' and row['threads']==1}
    fps=float(np.median([x['fps'] for x in runs]))
    combined=np.concatenate([np.asarray([float(x['end_to_end_ms']) for x in csv.DictReader((RAW/'benchmark'/f'r{repeat}.csv').open())]) for repeat in (1,2,3)])
    result={'author':AUTHOR,'generated_at_utc':datetime.now(timezone.utc).isoformat(),
        'status':'complete-mean-shift-bonus-comparison','protocol':'docs/MEANSHIFT_EXECUTION.md',
        'protocol_sha256':sha(ROOT/'docs/MEANSHIFT_EXECUTION.md'),
        'source_sha256':{str(p.relative_to(ROOT)):sha(p) for p in
            (ROOT/'python/meanshift_baseline.py',ROOT/'python/meanshift_trackeval.py',Path(__file__),ROOT/'python/verify_meanshift.py',ROOT/'scripts/phase5_meanshift.sh')},
        'preflight':read(RAW/'preflight.json'),'evaluator_equivalence':read(RAW/'evaluator-equivalence.json'),
        'sequences':sequences,'quality':evaluation['results'],
        'evaluation_sha256':sha(RAW/'evaluation.json'),
        'original_baselines_exact':True,'baseline_replaced':False,'parameters_tuned_on_MOT20':False,
        'benchmark':{'sequence':'MOT17-02-FRCNN','input_size':[608,1088],'warmup':50,
            'measured_frames_per_repeat':100,'repeats':runs,'median_repeat_fps':fps,
            'combined_p50_ms':float(np.quantile(combined,.5)),'combined_p95_ms':float(np.quantile(combined,.95)),
            'original_fp32_one_thread_settings':originals,
            'comparison_scope':'Different sessions and implementations; GT-seeded workload, no human annotation cost; not a paired speed-up or shipping test.',
            'cache_note':'Image checksums are read outside timing immediately before decoding; filesystem bytes are pre-read. Comparisons do not control cold I/O.'},
        'oracle_initialization':'First eligible pedestrian GT appearance/box; arbitrary tracker ID; no later GT correction or retirement.',
        'loss_policy':'Keep fixed histogram/window size and every initialized tracker until sequence end; stale tracks count against quality.',
        'negative_results_retained':True,'fresh_clone_bonus_execution_verified':False}
    (ROOT/'results/phase-5-meanshift.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    text='# Classical mean-shift versus detection + ByteTrack\n\n'
    text+=f'Author: {AUTHOR}; generated {result["generated_at_utc"]}.\n\n'
    text+='[JSON companion](phase-5-meanshift.json), [fixed protocol](../docs/MEANSHIFT_EXECUTION.md). The optional Phase 5 comparison is now measured; earlier mandatory failure reports and model baselines stay unchanged.\n\n'
    text+='## Quality on all four MOT20 sequences\n\nAll 8,931 frames. Same pinned TrackEval pedestrian preprocessing, HOTA/CLEAR/Identity settings. Mean-shift receives a GT box for every person at first valid appearance; ByteTrack uses the detector. This is an **oracle-initialized classical control**, not autonomous person detection or an equal-input contest. No later GT correction, visibility-based removal, appearance update, scale adaptation or re-detection.\n\n'
    text+='| Sequence / method | HOTA | MOTA | IDF1 | ID switches |\n|---|---:|---:|---:|---:|\n'
    for sequence in [*sequences,'OVERALL']:
        for label in ('meanshift','nano','tiny'):
            m=result['quality'][label]['TrackEval'][sequence]
            text+=f'| {sequence} / {label} | {m["HOTA"]:.3f} | {m["MOTA"]:.3f} | {m["IDF1"]:.3f} | {m["IDSW"]} |\n'
    text+='\nTrackEval percentages above are not interchangeable with motmetrics. The latter uses the project\'s original procedure and is reported separately:\n\n| Method | motmetrics MOTA | motmetrics IDF1 |\n|---|---:|---:|\n'
    for label in ('meanshift','nano','tiny'):
        m=result['quality'][label]['motmetrics']['OVERALL']
        text+=f'| {label} | {m["mota"]:.3f} | {m["idf1"]:.3f} |\n'
    text+='\nFresh nano/tiny scores for every sequence and overall match the original report exactly, and source track hashes remain unchanged. Negative MOTA means false positives, misses and switches together exceed the annotated-target count; it is a valid metric outcome.\n'
    text+='\n## Initialization and workload\n\n| Sequence | Seeded identities | Empty histograms | Emitted rows | Mean active trackers | Peak RSS KiB |\n|---|---:|---:|---:|---:|---:|\n'
    for name,row in sequences.items():
        m,t=row['metadata'],row['timing']
        text+=f'| {name} | {m["initialized_tracks"]} | {m["empty_histograms"]} | {m["emitted_rows_including_warmup"]} | {t["mean_active_tracks"]:.1f} | {m["peak_rss_kib"]} |\n'
    text+='\nThe algorithm has no retirement rule. Tracks persist after exits/occlusion and may drift to similar colors. This can cause many false positive boxes; fixed window sizes cannot follow scale changes. An unchanged numerical ID does not prove the box follows the same person. These findings characterize this fixed tutorial-style baseline, not every classical tracker or a tuned alternative.\n'
    text+='\n## One-thread illustrative speed check\n\nSame MOT17-02 measured frames 51–150, 50 warm-up frames, three fresh processes, one CPU quota, 608×1088. Mean-shift times include JPEG decoding, resize, HSV and tracking/filtering, excluding file output/drawing and manual annotation cost.\n\n| Method | Median repeat FPS |\n|---|---:|\n'
    text+=f'| Mean-shift (OpenCV Python, 1 thread) | {fps:.3f} |\n'
    for name,row in originals.items():text+=f'| {name} FP32 detector + ByteTrack (original C++, 1 thread) | {row["median_repeat_fps"]:.3f} |\n'
    text+=f'\nMean-shift combined p50/p95: {result["benchmark"]["combined_p50_ms"]:.3f}/{result["benchmark"]["combined_p95_ms"]:.3f} ms. '
    text+='This is a different-session, different-implementation comparison with oracle initialization and different target workloads, not a paired acceleration claim or the original real-time acceptance test. Image checksums pre-read filesystem bytes outside timing, so cold I/O is not controlled. Sparse MOT17 timing does not establish throughput in a dense street scene. Full-sequence timing summaries and raw CSVs are retained in the JSON.\n'
    text+='\n## Verification and scope\n\nLazy window backprojection matches standard full-image meanShift on 120 synthetic and 40 fixed MOT17 windows; input preprocessing matches exactly. The on-demand raw-IoU dataset adapter uses unchanged upstream overlap arithmetic, preprocessing and metrics. Every preprocessed array/dtype and every metric field equals the eager implementation on all 837 MOT17-05 frames; original nano/tiny MOT20 scores also reproduce exactly. External source remains unchanged. The adapter avoids simultaneously retaining raw and preprocessed dense IoU matrices without raising the six-GiB container limit.\n'
    text+='\nFull predictions/seeds and evaluator intermediates: ignored `data/phase-5-meanshift/`; [raw metadata/timings](phase-5-meanshift/). No downloads, new dependencies, GUI access, MOT20 parameter search, baseline replacement, commit, merge or push. These uncommitted additions have not undergone a fresh-clone full reproduction or independent bonus review. The established full-reproduction profile remains historical scope and does not execute this new bonus.\n'
    (ROOT/'results/phase-5-meanshift.md').write_text(text)
    print(json.dumps({'status':result['status'],'mean_shift_TrackEval':result['quality']['meanshift']['TrackEval']['OVERALL'],'median_fps':fps}),flush=True)


if __name__=='__main__':main()
