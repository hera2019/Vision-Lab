"""Report all controlled outcomes; keep initial FP32-only files separately."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from phase3_common import ROOT

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
base = ROOT/'results/phase-4'
paired = base/'benchmark-paired'
folder = paired if len(list(paired.glob('*.json'))) == 36 else base/'benchmark-fp32'
expected = 36 if folder == paired else 18
records = []
for path in sorted(folder.glob('*.json')):
    model, precision, threads, repeat = path.stem.split('-')
    metadata = json.loads(path.read_text())
    rows = list(csv.DictReader(path.with_suffix('.csv').open()))
    assert len(rows) == 100 and [int(r['frame']) for r in rows] == list(range(51, 151))
    assert metadata['warmup'] == 50 and metadata['measured'] == 100
    assert metadata['peak_rss_kib'] > 0 and metadata['opencv_threads'] == 1
    quota, period = (int(x) for x in metadata['cpu_max'].split())
    count = int(threads[1:])
    assert quota/period == count == metadata['threads']
    fields = [k for k in rows[0] if k.endswith('_ms')]
    arrays = {field: np.array([float(r[field]) for r in rows]) for field in fields}
    assert all(np.isfinite(v).all() and (v >= 0).all() for v in arrays.values())
    records.append({'model': model, 'precision': precision, 'threads': count,
        'repeat': int(repeat[1:]), 'fps': 100000/arrays['end_to_end_ms'].sum(),
        'metadata': metadata, 'timing_csv': str(path.with_suffix('.csv').relative_to(ROOT)),
        'timing_sha256': sha(path.with_suffix('.csv')), 'arrays': arrays})
assert len(records) == expected, f'Expected {expected} benchmark runs, got {len(records)}'

settings = []
for model in ('nano', 'tiny'):
    for precision in ('fp32', 'int8'):
        for threads in (1, 2, 4):
            runs = [r for r in records if (r['model'], r['precision'], r['threads']) == (model, precision, threads)]
            if not runs:
                continue
            assert sorted(r['repeat'] for r in runs) == [1, 2, 3]
            stages = {}
            for field in runs[0]['arrays']:
                values = np.concatenate([r['arrays'][field] for r in runs])
                stages[field] = {'mean_ms': float(values.mean()),
                    'p50_ms': float(np.percentile(values, 50)), 'p95_ms': float(np.percentile(values, 95))}
            model_path = ROOT/'models'/f'bytetrack_{model}_mot17.onnx' if precision == 'fp32' else ROOT/'data/phase-4/models'/f'bytetrack_{model}_mot17.int8.onnx'
            median_fps = float(np.median([r['fps'] for r in runs]))
            settings.append({'model': model, 'precision': precision, 'threads': threads,
                'median_repeat_fps': median_fps, 'repeat_fps': [r['fps'] for r in runs],
                'realtime_25_fps_gate': median_fps >= 25, 'stages': stages,
                'peak_rss_mib_max': max(r['metadata']['peak_rss_kib'] for r in runs)/1024,
                'model_bytes': model_path.stat().st_size, 'model_sha256': sha(model_path)})
for r in records:
    del r['arrays']
dependency = json.loads((ROOT/'results/phase-4-dependency.json').read_text())
evaluation_path = base/'evaluation-int8.json'
evaluation = json.loads(evaluation_path.read_text()) if evaluation_path.exists() else None
quantization = {model: json.loads((base/f'quantization-{model}.json').read_text())
                for model in ('nano', 'tiny') if (base/f'quantization-{model}.json').exists()}
thread_check = json.loads((base/'int8-thread-check.json').read_text()) if (base/'int8-thread-check.json').exists() else None
gates = []
if folder == paired and evaluation:
    assert evaluation['threads'] == 4 and set(evaluation['models']) == {'nano', 'tiny'}
    for model in ('nano', 'tiny'):
        measured = evaluation['models'][model]
        assert set(measured['coverage']) == {'MOT20-01', 'MOT20-02', 'MOT20-03', 'MOT20-05'}
        assert sum(v['processed_frames'] for v in measured['coverage'].values()) == 8931
        assert quantization[model]['calibration_reader_samples'] == 112
        assert quantization[model]['smoke_all_finite']
        baseline_mota = measured['baseline']['motmetrics']['OVERALL']['mota']
        int8_mota = measured['scores']['motmetrics']['OVERALL']['mota']
        loss = baseline_mota-int8_mota
        for threads in (1, 2, 4):
            original = next(s for s in settings if (s['model'], s['precision'], s['threads']) == (model, 'fp32', threads))
            quantized = next(s for s in settings if (s['model'], s['precision'], s['threads']) == (model, 'int8', threads))
            ratio = quantized['median_repeat_fps']/original['median_repeat_fps']
            gates.append({'model': model, 'threads': threads, 'speed_up': ratio,
                'speed_up_at_least_1_3': ratio >= 1.3, 'motmetrics_mota_loss_pp': loss,
                'loss_at_most_1_pp': loss <= 1, 'worth_it_per_fixed_gate': ratio >= 1.3 and loss <= 1,
                'quality_measured_at_threads': 4,
                'quality_transfer_to_this_budget_fully_measured': threads == 4})
complete = folder == paired and evaluation is not None and len(quantization) == 2
generated_at = datetime.now(timezone.utc).isoformat()
result = {'date': generated_at[:10], 'date_semantics': 'report generation date in UTC',
    'report_generated_at_utc': generated_at, 'protocol_date': '2026-10-06',
    'measurement_time_range_utc': None,
    'measurement_time_note': 'Absolute measurement timestamps are not recorded in the source timing files. Report generation and protocol dates do not establish when measurements were collected.',
    'author': 'Codex / GPT-6 (exact runtime model ID not exposed)',
    'status': 'phase-4-measurements-complete' if complete else 'partial-phase-4',
    'protocol': 'docs/PHASE4_EXECUTION.md', 'input_size': [608, 1088],
    'sequence': 'MOT17-02-FRCNN', 'warmup_frames': 50, 'measured_frames_per_repeat': 100,
    'repeats': 3, 'runs': records, 'settings': settings,
    'image_versions': (folder/'image-version.txt').read_text().splitlines(),
    'all_image_versions': (base/'all-image-versions.txt').read_text().splitlines() if (base/'all-image-versions.txt').exists() else [],
    'implementation_checks': json.loads((base/'implementation-checks.json').read_text()) if (base/'implementation-checks.json').exists() else None,
    'cpp_environment': json.loads((base/'environment.json').read_text()),
    'vm_hardware': (base/'hardware.txt').read_text().splitlines(),
    'benchmark_source_sha256': sha(ROOT/'cpp/src/benchmark_pipeline.cpp'),
    'input_frame_sha256': {f'MOT17-02-FRCNN/img1/{frame:06d}.jpg':
        sha(ROOT/'data/MOT17/train/MOT17-02-FRCNN/img1'/f'{frame:06d}.jpg')
        for frame in range(1, 151)},
    'int8_dependency': dependency, 'int8_worth_it_gate_evaluated': complete,
    'int8_quantization': quantization, 'int8_evaluation': evaluation,
    'int8_thread_check': thread_check, 'int8_usefulness_gates': gates,
    'int8_diagnostic': json.loads((ROOT/'results/phase-4-int8-diagnostic.json').read_text()) if (ROOT/'results/phase-4-int8-diagnostic.json').exists() else None,
    'accepted_baseline_replaced': False,
    'container_safety': json.loads((base/'container-safety.json').read_text()) if (base/'container-safety.json').exists() else None,
    'negative_records': {'calibration_initial_failure': 'phase-4/quantization-first-attempt.json',
                         'safety_probe_initial_failure': 'phase-4/container-safety-first-attempt.json'},
    'limitations': ['Mac M2 Max Linux VM, not edge-device FPS.',
        'CPU quota controls average budget, not physical-core affinity.',
        'Image read/decode through filtering included; output serialization/rendering excluded.',
        'Benchmark repeats use warm filesystem cache; disk cold-start is not measured.',
        'Concurrent user/host workloads are not excluded; repeat distributions retained.',
        'MOT20 quality measured at four threads; 1/4-thread byte consistency checked only on a fixed 50-frame slice, not every held-out frame.',
        'Static QDQ quantizes Conv operators only; other operations/input/output remain float.',
        'Numeric throughput gates do not establish robust identity tracking or product readiness.']}
(ROOT/'results/phase-4-performance.json').write_text(json.dumps(result, indent=2)+'\n')
conclusion = 'Final usefulness conclusions require the complete paired speed and held-out quality results.'
if complete:
    losses = '; '.join(f'{model} MOTA loss {next(g for g in gates if g["model"] == model)["motmetrics_mota_loss_pp"]:.4f} pp' for model in ('nano', 'tiny'))
    verdict = 'Neither INT8 model meets the fixed usefulness gate at any tested budget.' if not any(g['worth_it_per_fixed_gate'] for g in gates) else 'See the per-budget usefulness verdicts below.'
    conclusion = f'**Conclusion: {verdict} {losses}. The FP32 baseline is retained.**'
lines = ['# Phase 4 — controlled speed and memory', '',
    f'Report generated (UTC): {generated_at}. Author: Codex / GPT-6 (exact runtime model ID not exposed).', '',
    f'Protocol date: {result["protocol_date"]}. Measurement UTC range: not recorded in the source timing files. Generation and protocol dates do not establish when measurements were collected.', '',
    f'Status: **{result["status"]}**. '+('All predeclared measurements finished; failed gates remain failed. Independent review is pending.' if complete else 'This is a partial result, not phase completion.'), '',
    conclusion, '',
    'Existing baseline tracker/settings; native 608×1088 detector input. One fresh process at a time, OpenCV one thread, ORT/container CPU budgets 1/2/4. Each setting has three repeats; frames 1–50 warm up and only 51–150 are measured. FPS includes JPEG read/decode, detector and track update/box filtering, excluding output serialization and video drawing. Each median FPS is the median of three repeat throughputs, not reciprocal median latency.', '',
    '| Model | Precision | Threads / CPU quota | Median repeat FPS | End-to-end p50 ms | End-to-end p95 ms | Peak RSS MiB (max repeat) | Model MiB | >=25 FPS |',
    '|---|---|---:|---:|---:|---:|---:|---:|---|']
for s in settings:
    stage = s['stages']['end_to_end_ms']
    lines.append(f'| {s["model"]} | {s["precision"]} | {s["threads"]} | {s["median_repeat_fps"]:.2f} | {stage["p50_ms"]:.2f} | {stage["p95_ms"]:.2f} | {s["peak_rss_mib_max"]:.1f} | {s["model_bytes"]/1048576:.2f} | {s["realtime_25_fps_gate"]} |')
lines += ['', '## Mean stage latency — milliseconds', '',
    '| Model | Precision | Threads | Decode | Preprocess | Inference | Postprocess | Tracking/filtering | End-to-end |',
    '|---|---|---:|---:|---:|---:|---:|---:|---:|']
for s in settings:
    values = ' | '.join(f'{s["stages"][field]["mean_ms"]:.2f}' for field in
        ('decode_ms', 'preprocess_ms', 'inference_ms', 'postprocess_ms', 'tracking_ms', 'end_to_end_ms'))
    lines.append(f'| {s["model"]} | {s["precision"]} | {s["threads"]} | {values} |')
if evaluation:
    lines += ['', '## Held-out MOT20 — unchanged procedures and A1 settings', '',
        'Four complete sequences, 8,931 frames per model. Calibration uses MOT17 only. FP32 baseline hashes checked against the accepted Phase 3 result. Every number keeps its evaluator label; no MOT20 tuning or post-result recalibration.', '',
        '| Evaluator | Model | Sequence | FP32 MOTA | INT8 MOTA | ΔMOTA pp | FP32 IDF1 | INT8 IDF1 | ΔIDF1 pp |',
        '|---|---|---|---:|---:|---:|---:|---:|---:|']
    for model, measurement in evaluation['models'].items():
        for evaluator, names in measurement['scores'].items():
            mk, ik = ('mota', 'idf1') if evaluator == 'motmetrics' else ('MOTA', 'IDF1')
            for name, new in names.items():
                old = measurement['baseline'][evaluator][name]
                lines.append(f'| {evaluator} | {model} | {name} | {old[mk]:.4f} | {new[mk]:.4f} | {new[mk]-old[mk]:+.4f} | {old[ik]:.4f} | {new[ik]:.4f} | {new[ik]-old[ik]:+.4f} |')
    lines += ['', 'TrackEval HOTA and identity switches, motmetrics identity switches/FP/FN, coverage and track hashes are retained in the JSON.', '',
        '## Fixed INT8 usefulness gate', '',
        'Worth it requires paired end-to-end speed-up ≥1.3× AND overall motmetrics MOT20 MOTA loss ≤1.0 pp. Quality is measured at four threads; the separate 50-frame 1/4-thread consistency check is limited evidence for transfer to other budgets.', '',
        '| Model | Threads | End-to-end speed-up | MOT20 MOTA loss pp | Speed pass | Accuracy pass | Worth it |',
        '|---|---:|---:|---:|---|---|---|']
    for g in gates:
        lines.append(f'| {g["model"]} | {g["threads"]} | {g["speed_up"]:.3f}× | {g["motmetrics_mota_loss_pp"]:.4f} | {g["speed_up_at_least_1_3"]} | {g["loss_at_most_1_pp"]} | {g["worth_it_per_fixed_gate"]} |')
lines += ['', '## Quantization, safety and retained failures', '',
    'The owner approved ml_dtypes 0.6.0; its hash-checked binary wheel was installed into a separate image with no other package upgrades. Static QDQ uses Conv-only S8S8, per-channel weights and MinMax over the same 112 MOT17 images. Native-shaped outputs are finite and original FP32 model hashes remain unchanged. Model/node counts, hashes, calibration sample counts and dependency versions are in the JSON.', '',
    'An initial calibration failed: ORT 1.30 cleared each capped intermediate batch without computing/merging its ranges. Raising the storage cap from 1 to 128 retains all 112 fixed observations; reader count is asserted. No input, quantization scheme, score threshold or memory limit changed. Initial log/JSON remain. The initial safety probe also failed an overly narrow interface-name assumption; down kernel tunnel devices were inspected, and actual routing/connectivity checks confirm isolation. Runtime protections were unchanged.', '',
    'Runtime protections are documented in `phase-4/container-safety.md` / `.json`: offline, non-root, zero capabilities, no privilege escalation, read-only root/project except selected outputs, 1 GiB nosuid/nodev/noexec tmpfs, 6 GiB RAM, 512-process cap, no Docker socket. Only approved image builds use network.', '',
    'The read-only [INT8 diagnostic](phase-4-int8-diagnostic.md) uses MOT17-02 frames 1/51/150. Official preprocessing matches the reconstructed C++ formula within 4.77e-7; preprocessed FP32 and original FP32 raw outputs are identical on all three frames for both models. Nano INT8 produces far more post-NMS boxes, including when runtime optimization is disabled. This localizes the observed issue to the INT8 path on this slice, without identifying a specific operator or establishing its general root cause. No model/settings changes or replacement quality score were made.', '',
    '## Limits and remaining work', '',
    'These are Mac M2 Max cores in Docker’s Linux VM, not measurements on an edge board. Peak memory is process VmHWM, including initialization and warm-up; it is not host/VM total RAM. CPU quota is verified from cgroup cpu.max and does not pin physical cores. Repeated images benefit from filesystem cache. Individual repeat FPS, raw frame timings, per-stage mean/p50/p95, model/image hashes and all failed real-time settings remain in the JSON.', '',
    'Original FP32-only runs/report are retained as `phase-4-performance-fp32.*`. Paired runs are used for speed ratios to reduce ordering bias. This phase does not repair the owner-reported identity failures. '+('Executor package inventory, model-ledger and syntax checks are in implementation_checks.' if result['implementation_checks'] else 'Original executor-only implementation checks are not presented as newly executed; see the archived Phase 6 reference if running full reproduction.')+' Fresh-clone context requires separate verification; individual pipeline stages alone do not establish it.', '',
    'Reproduce using the existing baseline models/data, pinned external evaluators and local base images:', '',
    '```sh', 'docker build --network=none -f Dockerfile.phase4 -t vision-lab:phase4 .',
    'docker build -f Dockerfile.phase4-pytools -t vision-lab:phase4-pytools .',
    'bash scripts/phase4_experiment.sh', '```']
(ROOT/'results/phase-4-performance.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status': result['status'], 'settings': [{k: s[k] for k in
    ('model', 'precision', 'threads', 'median_repeat_fps', 'peak_rss_mib_max', 'realtime_25_fps_gate')} for s in settings]}), flush=True)
