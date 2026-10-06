"""Build the final human/machine phase report from measured evaluator outputs."""
import csv
import hashlib
import json
from pathlib import Path
from phase3_common import ROOT, sequence_info
from compare_tracking import compare

directory=ROOT/'results/phase-3'
evaluation=json.loads((directory/'evaluation-final.json').read_text())
data=evaluation['results']
determinism=json.loads((directory/'thread-determinism.json').read_text())
self_test=json.loads((directory/'evaluation-self.json').read_text())
edge_cases=json.loads((directory/'edge-cases.json').read_text())
boundary_before=json.loads((directory/'edge-cases-threshold-before-fix.json').read_text())
score_boundaries=json.loads((directory/'score-boundaries.json').read_text())
threads=determinism['accuracy_threads']
criteria={'3a':{},'3b':{}}
comparison={}
timings={}
cache_hashes={}
for benchmark in ('MOT17','MOT20'):
    comparison[benchmark]={};timings[benchmark]={};cache_hashes[benchmark]={}
    for model in ('nano','tiny'):
        scores=data[benchmark]
        cpp=scores['cpp'][model]['scores']['motmetrics']
        python=scores['python'][model]['scores']['motmetrics']
        end=scores['end-to-end'][model]['scores']['motmetrics']
        comparison[benchmark][model]={};timings[benchmark][model]={};cache_hashes[benchmark][model]={}
        for name in cpp:
            if name=='OVERALL':continue
            base=ROOT/'data/phase-3/tracks'
            paths={impl:base/impl/model/(name+'.txt') for impl in ('python','cpp','end-to-end')}
            comparison[benchmark][model][name]={
                'cpp_vs_python':compare(paths['python'],paths['cpp']),
                'end_to_end_vs_cached_cpp':compare(paths['cpp'],paths['end-to-end'])}
            delta={m:abs(cpp[name][m]-python[name][m]) for m in ('mota','idf1')}
            if benchmark=='MOT17':
                criteria['3a'].setdefault(model,{})[name]={'delta_pp':delta,'pass':all(x<=.1 for x in delta.values())}
            cache=ROOT/'data/phase-3/dets'/model/(name+'.txt')
            cache_hashes[benchmark][model][name]=hashlib.sha256(cache.read_bytes()).hexdigest()
            rows=list(csv.DictReader(paths['end-to-end'].with_suffix('.txt.timing.csv').open()))
            fields=['preprocess_ms','inference_ms','postprocess_ms','tracking_ms']
            timings[benchmark][model][name]={'frames':len(rows),'threads':sorted(set(int(r['threads']) for r in rows)),
                    'stage_total_seconds':{field:sum(float(r[field]) for r in rows)/1000 for field in fields},
                    'python_reference_tracker_loop_seconds':json.loads(paths['python'].with_suffix('.run.json').read_text())['seconds']}
            seq=ROOT/'data'/benchmark/'train'/name
            if len(rows)!=int(sequence_info(seq)['seqlength']):raise RuntimeError(f'incomplete run: {name}')
        if benchmark=='MOT17':
            published={'nano':{'mota':69.0,'idf1':66.3},'tiny':{'mota':77.1,'idf1':71.5}}[model]
            delta={m:end['OVERALL'][m]-published[m] for m in ('mota','idf1')}
            criteria['3b'][model]={'measured':end['OVERALL'],'published':published,
                'delta_pp':delta,'pass':all(abs(x)<=1 for x in delta.values())}

passed=all(row['pass'] for model in criteria['3a'].values() for row in model.values()) and all(row['pass'] for row in criteria['3b'].values())
identical=all(row['end_to_end_vs_cached_cpp']['byte_identical'] for bench in comparison.values() for model in bench.values() for row in model.values())
demos={p.stem:json.loads(p.read_text()) for p in (ROOT/'data/phase-3/demos').glob('*.json')}
result={'date':'2026-10-06','status':'pass' if passed else 'failed-criterion-review-required',
        'author':'Codex / GPT-6 (exact runtime model ID not exposed)','accuracy_threads':threads,
        'criteria':criteria,'end_to_end_equals_cached_cpp':identical,'comparisons':comparison,
        'evaluation':evaluation,'determinism':determinism,'ground_truth_self_test':self_test,
        'edge_cases':edge_cases,'detection_cache_sha256':cache_hashes,
        'threshold_correction':{'issue':'I-7','before_fix_fixture':boundary_before,
                                'after_fix_fixture':edge_cases,'actual_cache_boundary_counts':score_boundaries},
        'stage_timings_observational':timings,'demos':demos,
        'timing_limitations':'Concurrent accuracy runs; no warm-up exclusion or repeat benchmark. Stage sums omit image decoding and are not end-to-end throughput. Phase 4 has not run.',
        'cpp_environment':json.loads((directory/'environment.txt').read_text()),
        'image_versions':(directory/'image-versions.txt').read_text().splitlines(),
        'python_environment':(directory/'python-environment.txt').read_text().splitlines(),
        'demo_image_version':(directory/'demo-image-version.txt').read_text().splitlines(),
        'cpp_binaries_unchanged_after_demo_target':(directory/'cpp-binaries-before-demo.txt').read_bytes()==(directory/'cpp-binaries-after-demo.txt').read_bytes(),
        'execution_notes':{
            'streaming_driver':{'initial_exit_code':2,'all_sequence_outputs_written':True,
                'log':'phase-3/tracking-run.log','resolution':'completed script passes syntax checks; final C++ outputs regenerated and all end-to-end files match'},
            'artifact_encoder':{'first_attempt':'tmpfs execution refused',
                'log':'phase-3/demo-encoding-first-attempt.log','resolution':'normal image-build target; unchanged container protections'}},
        'data_boundaries':'MOT17 train: fidelity only; MOT20 train: held-out, no tuning; existing research-only pedestrian weights.'}
(ROOT/'results/phase-3-tracking.json').write_text(json.dumps(result,indent=2)+'\n')

lines=['# Phase 3 — C++ ByteTrack tracking', '',
       f'Date: 2026-10-06 · Result: **{result["status"]}** · ONNX Runtime threads: **{threads}**', '',
       'The C++ tracker follows the upstream Python tracker, including score fusion, inclusive-pixel association IoU, empty-frame skipping and list-update order. No thresholds were tuned. External source trees and prior-phase source/results remain unchanged.', '',
       'This is Phase 3 acceptance only. The earlier nano Phase 1 raw-output tolerance failure stays on record; speed/INT8 acceptance is deferred to Phase 4.', '',
       '## Fixed criteria — motmetrics 1.4.0', '',
       'MOT17 train was seen during training: these are fidelity checks, not held-out accuracy.', '',
       'Published reference scores are from ByteTrack README lines 157–158 at the source revision in `assets.json`.', '',
       '| Model | 3a: every sequence ΔMOTA / ΔIDF1 ≤ 0.1 pp | 3b: overall vs published ±1.0 pp |',
       '|---|---|---|']
for model in ('nano','tiny'):
    ok=all(r['pass'] for r in criteria['3a'][model].values())
    lines.append(f'| {model} | {"pass" if ok else "FAIL"} | {"pass" if criteria["3b"][model]["pass"] else "FAIL"} |')
lines += ['', '### Criterion 3a per sequence — motmetrics 1.4.0', '',
          '| Model | Sequence | Python MOTA | C++ MOTA | ΔMOTA pp | Python IDF1 | C++ IDF1 | ΔIDF1 pp | Pass |',
          '|---|---|---:|---:|---:|---:|---:|---:|---|']
for model in ('nano','tiny'):
    py=data['MOT17']['python'][model]['scores']['motmetrics'];cpp=data['MOT17']['cpp'][model]['scores']['motmetrics']
    for name,row in criteria['3a'][model].items():
        lines.append(f'| {model} | {name} | {py[name]["mota"]:.4f} | {cpp[name]["mota"]:.4f} | {row["delta_pp"]["mota"]:.4f} | {py[name]["idf1"]:.4f} | {cpp[name]["idf1"]:.4f} | {row["delta_pp"]["idf1"]:.4f} | {row["pass"]} |')
lines += ['', '### Criterion 3b — C++ end-to-end, motmetrics 1.4.0', '',
          '| Model | MOTA | Published MOTA | Δ pp | IDF1 | Published IDF1 | Δ pp | Pass |',
          '|---|---:|---:|---:|---:|---:|---:|---|']
for model,row in criteria['3b'].items():
    v,p,d=row['measured'],row['published'],row['delta_pp']
    lines.append(f'| {model} | {v["mota"]:.4f} | {p["mota"]:.1f} | {d["mota"]:+.4f} | {v["idf1"]:.4f} | {p["idf1"]:.1f} | {d["idf1"]:+.4f} | {row["pass"]} |')
lines += ['', '## MOT20 held-out accuracy — C++ end-to-end', '',
          'A1 configuration: 608×1088 input, track_thresh 0.6, track_buffer 30, match_thresh 0.9, score fusion on; no sequence-specific overrides. These are the Phase 4 INT8 baselines; no pass/fail threshold applies.', '',
          '| Model | Sequence | motmetrics MOTA | motmetrics IDF1 | TrackEval HOTA | TrackEval MOTA | TrackEval IDF1 | TrackEval ID switches |',
          '|---|---|---:|---:|---:|---:|---:|---:|']
for model in ('nano','tiny'):
    scores=data['MOT20']['end-to-end'][model]['scores']
    for name,m in scores['motmetrics'].items():
        t=scores['TrackEval'][name]
        lines.append(f'| {model} | {name} | {m["mota"]:.4f} | {m["idf1"]:.4f} | {t["HOTA"]:.4f} | {t["MOTA"]:.4f} | {t["IDF1"]:.4f} | {t["IDSW"]} |')
lines += ['', '## MOT17 TrackEval — C++ end-to-end (fidelity only)', '',
          '| Model | Sequence | HOTA | MOTA | IDF1 | ID switches |', '|---|---|---:|---:|---:|---:|']
for model in ('nano','tiny'):
    for name,t in data['MOT17']['end-to-end'][model]['scores']['TrackEval'].items():
        lines.append(f'| {model} | {name} | {t["HOTA"]:.4f} | {t["MOTA"]:.4f} | {t["IDF1"]:.4f} | {t["IDSW"]} |')
lines += ['', '## Output comparisons', '',
          f'End-to-end output equals cache-then-track output byte-for-byte for every sequence/model: **{identical}**.', '',
          'Literal matching is kept separate from numeric matching. The Python writer expands rounded float32 scores; C++ writes two decimal places (I-5). Most score differences are below 2.87e-8, but three rows in nano MOT20-02 and tiny MOT20-05 differ by 0.01 at decimal-half rounding boundaries (NumPy float32 rounding vs C++ decimal formatting). Frames, IDs and boxes agree; neither configured evaluator uses these emitted prediction scores. The percentages below compare literal lines, without normalization.', '',
          '| Dataset | Model | Sequence | Literal line share | Same frame/ID order | Max box difference px | Max score difference |',
          '|---|---|---|---:|---|---:|---:|']
for benchmark in comparison:
    for model,seqs in comparison[benchmark].items():
        for name,c in seqs.items():
            c=c['cpp_vs_python']
            lines.append(f'| {benchmark} | {model} | {name} | {c["identical_line_share"]*100:.3f}% | {c["same_frame_and_id"]} | {c.get("max_box_difference",float("nan")):.4f} | {c.get("max_score_difference",float("nan")):.3g} |')
lines += ['', '## Validation, timing and provenance', '',
          '- Both models have bit-identical 1-thread/4-thread detections on MOT17-02 frames 1–50.',
          '- TrackEval ground-truth self-tests score exactly 100 HOTA/MOTA/IDF1 on every MOT17 and MOT20 sequence.',
          f'- Behavioral fixtures for confidence tiers, empty frames, recovery, expiry, unconfirmed removal and exact float32 thresholds: pass={edge_cases["pass"]}.',
          '- An initial threshold-equality fixture failed (I-7). The score comparisons were corrected to match NumPy float32 semantics; the negative result and actual cached boundary counts are preserved in the JSON. All final C++ cache outputs were regenerated with the corrected tracker and checked against stored end-to-end outputs.',
          '- Two driver/artifact failures are retained (I-8/I-9): editing a running shell driver caused an EOF error after every output was written; executing an encoder from the protected tmpfs was refused. Final drivers pass syntax checks, regenerated tracking files agree, and the encoder uses the normal image build. Container protections were preserved.',
          '- Evaluators intentionally differ: motmetrics follows ByteTrack\'s procedure (gt min_confidence=1, IoU distance threshold 0.5, lap solver). TrackEval uses its standard pedestrian/distractor preprocessing. Their scores must not be mixed.',
          '- These are concurrent accuracy runs. Per-stage time totals and Python tracker run times are in the JSON/raw files; they are observations, not Phase 4 benchmarks. Image decoding is excluded from stage sums. No realtime or INT8 claim is made.',
          '- Scores from an earlier evaluator run are reused only when all its input file hashes still match. End-to-end scores can reuse cached-C++ evaluation only when every end-to-end output byte is identical; each reuse is recorded in the JSON.',
          '- Detection and tracker output SHA-256 values, dependency versions and per-sequence stage time totals are in the JSON. Models/data are excluded from git; sources and revisions are in `assets.json`.', '',
          '## Reproduction', '', 'Run from the repository root. The existing local models and MOT17/MOT20 sequences are required; TrackEval must exist at the revision in `assets.json`. Fresh-clone asset setup is Phase 6, not validated here.', '',
          '```bash', './scripts/phase3_build.sh', './scripts/phase3_determinism.sh',
          './scripts/phase3_edge_cases.sh', './scripts/phase3_evaluate.sh self',
          f'./scripts/phase3_detect.sh {threads}', './scripts/phase3_track.sh',
          f'./scripts/phase3_end_to_end.sh {threads}',
          './scripts/phase3_demo.sh', './scripts/phase3_finalize.sh', '```', '',
          'All runs go through the hardened container wrapper. Accuracy settings are fixed by amendment A1.', '',
          '## Demonstrations', '',
          'Three 12-second clips were selected before held-out scores were available: MOT17-02 (fixed street camera), MOT17-05 (moving street camera), MOT20-03 (crowded scene). Each uses measured C++ nano end-to-end output, fixed ID colors and 2-second image-space trails. All frames in each output video were decoded successfully; three preview frames per video were saved. Only pedestrian identities are drawn. Playback rate is the source rate, not measured inference throughput.', '',
          '| Sequence | Frames | Source FPS | Video |', '|---|---|---:|---|']
for name,d in sorted(demos.items()):
    lines.append(f'| {d["sequence"]} | {d["frame_range"][0]}–{d["frame_range"][1]} | {d["fps"]} | [`{name}.mp4`](../data/phase-3/demos/{name}.mp4) |')
lines += ['', 'Source: MOTChallenge. Clips retain CC BY-NC-SA 3.0 attribution and are research-only. No external video or additional model was downloaded.', '',
          '## Next step', '',
          'Phase 4 benchmarks and INT8 are not started. The next taskbook is written after review of this phase. Any failed criterion remains failed and requires review; thresholds are not adjusted to make it pass.', '']
(ROOT/'results/phase-3-tracking.md').write_text('\n'.join(lines))
print(json.dumps({'criteria':criteria,'status':result['status'],'end_to_end_identical':identical}),flush=True)
