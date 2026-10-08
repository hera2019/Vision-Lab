"""Additive post-hoc experiment; frozen protocol in docs/PHASE4_REPAIR.md."""
import argparse
import copy
import csv
import gc
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
import cv2
import numpy as np
import onnx
import onnxruntime as ort
from onnx import numpy_helper
from phase3_common import ROOT, sequence_info
from vl_common import preproc

BASE = ROOT / 'data/phase-4-repair'
RAW = ROOT / 'results/phase-4-repair'
PREPARED = ROOT / 'data/phase-4/models/bytetrack_nano_mot17.preprocessed.onnx'
ORIGINAL = ROOT / 'data/phase-4/models/bytetrack_nano_mot17.int8.onnx'
FP32 = ROOT / 'models/bytetrack_nano_mot17.onnx'
CANDIDATES = ('head-fp32', 'neck-head-fp32')
AUTHOR = 'Codex / GPT-6 (exact runtime model ID not exposed)'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def context():
    return {'author': AUTHOR, 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
            'protocol': 'docs/PHASE4_REPAIR.md',
            'protocol_sha256': sha(ROOT / 'docs/PHASE4_REPAIR.md'),
            'script_sha256': sha(Path(__file__)),
            'original_hashes': {str(p.relative_to(ROOT)): sha(p)
                                for p in (FP32, PREPARED, ORIGINAL)},
            'onnxruntime': ort.__version__,
            'cpp_source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in
                (ROOT/'cpp/src/detector.h', ROOT/'cpp/src/track_sequence.cpp',
                 ROOT/'cpp/src/benchmark_pipeline.cpp', ROOT/'cpp/src/tracker/tracker.cpp')}}


def session(path, debug=False):
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    if debug:
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
    return ort.InferenceSession(str(path), options, providers=['CPUExecutionProvider'])


def diagnose():
    from check_cpp_detector import reference_detections
    graph = onnx.load(ORIGINAL)
    initials = {t.name: numpy_helper.to_array(t) for t in graph.graph.initializer}
    tensors = {}
    for node in graph.graph.node:
        if node.op_type != 'QuantizeLinear' or node.input[0] in initials:
            continue
        scale, zero = initials[node.input[1]], initials[node.input[2]]
        assert scale.size == zero.size == 1, 'Activation scale must be scalar.'
        info = np.iinfo(zero.dtype)
        lo = float(scale.item() * (info.min - int(zero.item())))
        hi = float(scale.item() * (info.max - int(zero.item())))
        tensors[node.input[0]] = {'low': lo, 'high': hi, 'scale': float(scale.item()),
                                'zero_point': int(zero.item()), 'qmin': info.min, 'qmax': info.max,
                                'stage': 'head' if node.input[0].startswith('/head/') else 'backbone'}
    assert len(tensors) > 100
    for label, path in (('fp32', PREPARED), ('int8', ORIGINAL)):
        model = onnx.load(path)
        names = {x.name for x in model.graph.output}
        for name in tensors:
            if name not in names:
                model.graph.output.append(onnx.helper.make_tensor_value_info(name, onnx.TensorProto.FLOAT, None))
        onnx.save(model, BASE / f'debug-{label}.onnx')
    debug = {k: session(BASE / f'debug-{k}.onnx', True) for k in ('fp32', 'int8')}
    ordinary = {'fp32': session(PREPARED), 'int8': session(ORIGINAL)}
    disabled = {'fp32': session(PREPARED, True), 'int8': session(ORIGINAL, True)}
    frames = []
    for benchmark in ('MOT17', 'MOT20'):
        pattern = '*-FRCNN' if benchmark == 'MOT17' else 'MOT20-*'
        for seq in sorted((ROOT / 'data' / benchmark / 'train').glob(pattern)):
            count = int(sequence_info(seq)['seqlength'])
            indices = (2, count // 2) if benchmark == 'MOT17' else (1, 150)
            frames.extend((benchmark, seq / 'img1' / f'{i:06d}.jpg') for i in indices)
    rows = []
    aggregate = {b: {n: {'elements': 0, 'fp32_outside': 0, 'int8_prequant_outside': 0,
                         'fp32_round_clamps': 0, 'int8_prequant_round_clamps': 0,
                         'fp32_negative': 0, 'fp32_negative_to_zero': 0,
                         'abs_error_sum': 0.0, 'abs_fp32_sum': 0.0}
                     for n in tensors} for b in ('MOT17', 'MOT20')}
    for benchmark, path in frames:
        array, _ = preproc(cv2.imread(str(path)), (608, 1088))
        inputs = {'images': array[None]}
        finals = {k: s.run(None, inputs)[0] for k, s in ordinary.items()}
        row = {'benchmark': benchmark, 'image': str(path.relative_to(ROOT)),
               'sha256': sha(path), 'outputs': {}, 'instrumentation_check': {}}
        acts = {k: dict(zip([x.name for x in s.get_outputs()], s.run(None, inputs)))
                for k, s in debug.items()}
        for label in ordinary:
            raw = finals[label]
            assert raw.shape == (1, 13566, 6) and np.isfinite(raw).all()
            scores = (raw[..., 4] * raw[..., 5]).ravel()
            det = reference_detections(ordinary[label], path)
            row['outputs'][label] = {
                'score_quantiles_50_90_99_100': np.quantile(scores, [.5, .9, .99, 1]).tolist(),
                'objectness_max': float(raw[..., 4].max()),
                'class_probability_max': float(raw[..., 5].max()),
                'pre_nms_ge_001': int((scores >= .01).sum()),
                'pre_nms_ge_06': int((scores >= .6).sum()),
                'nms_ge_001': len(det), 'nms_ge_06': int((det[:, 4] >= .6).sum())}
            name = debug[label].get_outputs()[0].name
            control = disabled[label].run(None, inputs)[0]
            difference = float(np.max(np.abs(acts[label][name] - control)))
            assert difference == 0, 'Adding outputs changed unoptimized final output.'
            row['instrumentation_check'][label] = {
                'same_optimization_final_max_abs': difference,
                'optimized_vs_unoptimized_max_abs': float(np.max(np.abs(finals[label] - control)))}
        for name, limits in tensors.items():
            a, b = acts['fp32'][name], acts['int8'][name]
            assert a.shape == b.shape and np.isfinite(a).all() and np.isfinite(b).all()
            stat = aggregate[benchmark][name]
            stat['elements'] += a.size
            stat['fp32_outside'] += int(((a < limits['low']) | (a > limits['high'])).sum())
            stat['int8_prequant_outside'] += int(((b < limits['low']) | (b > limits['high'])).sum())
            for values, key in ((a, 'fp32'), (b, 'int8_prequant')):
                codes = np.rint(values / limits['scale']) + limits['zero_point']
                stat[key + '_round_clamps'] += int(((codes < limits['qmin']) | (codes > limits['qmax'])).sum())
                if key == 'fp32':
                    stat['fp32_negative'] += int((values < 0).sum())
                    stat['fp32_negative_to_zero'] += int(((values < 0) & (codes == limits['zero_point'])).sum())
            stat['abs_error_sum'] += float(np.abs(a - b).sum(dtype=np.float64))
            stat['abs_fp32_sum'] += float(np.abs(a).sum(dtype=np.float64))
        rows.append(row)
        print(f'diagnosed {path.parent.parent.name}/{path.name}: '
              f'NMS high FP32={row["outputs"]["fp32"]["nms_ge_06"]} '
              f'INT8={row["outputs"]["int8"]["nms_ge_06"]}', flush=True)
        del acts
        gc.collect()
    for benchmark, stats in aggregate.items():
        for name, stat in stats.items():
            stat.update(tensors[name])
            stat['fp32_outside_fraction'] = stat['fp32_outside'] / stat['elements']
            stat['int8_prequant_outside_fraction'] = stat['int8_prequant_outside'] / stat['elements']
            stat['relative_l1_error'] = stat['abs_error_sum'] / max(stat['abs_fp32_sum'], 1e-30)
            stat['fp32_round_clamp_fraction'] = stat['fp32_round_clamps'] / stat['elements']
            stat['int8_prequant_round_clamp_fraction'] = stat['int8_prequant_round_clamps'] / stat['elements']
            stat['fp32_negative_to_zero_fraction_of_negative'] = stat['fp32_negative_to_zero'] / max(stat['fp32_negative'], 1)
    result = {**context(), 'status': 'selected-frame-read-only-diagnosis-complete',
              'activation_tensor_count': len(tensors), 'frames': rows, 'activation_summary': aggregate,
              'scope': 'MOT20 read-only failure analysis, not calibration or remedy selection; selected frames only.'}
    save(ROOT / 'results/phase-4-nano-diagnosis.json', result)
    text = '# Post-hoc nano INT8 diagnosis\n\n' + result['generated_at_utc'] + '\n\n'
    text += 'Original model unchanged. Selected frames; counts are not dataset-wide estimates.\n\n'
    text += '| Frame | FP32 boxes >=0.6 | Original INT8 boxes >=0.6 |\n|---|---:|---:|\n'
    for r in rows:
        text += f'| {r["image"]} | {r["outputs"]["fp32"]["nms_ge_06"]} | {r["outputs"]["int8"]["nms_ge_06"]} |\n'
    text += '\n## Quantization diagnostics\n\nOutside-range counts describe values beyond the model\'s fixed INT8 representable window. '
    text += 'They are not clamp counts: rounding near an endpoint can land on it without integer overflow. '
    text += 'Actual saturation counts apply round-to-nearest then test integer bounds, and are recorded separately. '
    text += 'FP32 values are counterfactual; INT8 prequant values are observed in the instrumented QDQ graph. '
    text += 'Relative L1 error compares corresponding prequantization tensors after accumulated upstream quantization errors. '
    text += 'Clipping/error alone does not establish a single causal operator.\n\n'
    for b in aggregate:
        text += f'### {b}: ten largest head relative errors\n\n| Tensor | FP32 outside | INT8 prequant outside | Relative L1 |\n|---|---:|---:|---:|\n'
        top = sorted(((n, s) for n, s in aggregate[b].items() if s['stage'] == 'head'),
                     key=lambda x: x[1]['relative_l1_error'], reverse=True)[:10]
        for n, s in top:
            text += f'| `{n}` | {s["fp32_outside_fraction"]:.4%} | {s["int8_prequant_outside_fraction"]:.4%} | {s["relative_l1_error"]:.4f} |\n'
        text += '\nTen largest observed prequant integer-clamp fractions:\n\n| Tensor | FP32 clamps | INT8 prequant clamps |\n|---|---:|---:|\n'
        top = sorted(aggregate[b].items(), key=lambda x: x[1]['int8_prequant_round_clamp_fraction'], reverse=True)[:10]
        for n, s in top:
            text += f'| `{n}` | {s["fp32_round_clamp_fraction"]:.4%} | {s["int8_prequant_round_clamp_fraction"]:.4%} |\n'
    text += '\nAll instrumented final outputs equal noninstrumented outputs with optimization disabled. '
    text += 'Optimized/unoptimized differences and all tensor ranges are recorded in the [JSON](phase-4-nano-diagnosis.json). '
    text += 'This instrumented graph can suppress deployment fusions; only ordinary optimized inference supplies the detection counts.\n'
    (ROOT / 'results/phase-4-nano-diagnosis.md').write_text(text)


def quantize():
    from onnxruntime.quantization import (CalibrationDataReader, CalibrationMethod,
                                          QuantFormat, QuantType, quantize_static)
    manifest = json.loads((ROOT / 'results/phase-4/calibration-frames.json').read_text())
    assert len(manifest) == 112
    for row in manifest:
        assert row['path'].startswith('data/MOT17/train/') and sha(ROOT / row['path']) == row['sha256']
    class Reader(CalibrationDataReader):
        def __init__(self):
            self.rows = iter(manifest)
            self.used = 0
        def get_next(self):
            row = next(self.rows, None)
            if row is None:
                return None
            self.used += 1
            array, _ = preproc(cv2.imread(str(ROOT / row['path'])), (608, 1088))
            return {'images': array[None]}
    # ORT writes its inferred helper next to its input. Keep the original read-only.
    prepared_copy = BASE / 'prepared-copy.onnx'
    shutil.copyfile(PREPARED, prepared_copy)
    assert sha(prepared_copy) == sha(PREPARED)
    graph = onnx.load(prepared_copy)
    conv = [n.name for n in graph.graph.node if n.op_type == 'Conv']
    result = {**context(), 'calibration_manifest_sha256': sha(ROOT / 'results/phase-4/calibration-frames.json'),
              'candidates': {}}
    for candidate in CANDIDATES:
        excluded = [n for n in conv if (n.startswith('/head/') if candidate == 'head-fp32'
                                       else not n.startswith('/backbone/backbone/'))]
        assert len(excluded) == (36 if candidate == 'head-fp32' else 66)
        target = BASE / f'{candidate}.onnx'
        assert not target.exists(), 'Refuse to overwrite a candidate model.'
        reader = Reader()
        quantize_static(prepared_copy, target, reader, quant_format=QuantFormat.QDQ,
                        op_types_to_quantize=['Conv'], per_channel=True, reduce_range=False,
                        activation_type=QuantType.QInt8, weight_type=QuantType.QInt8,
                        calibrate_method=CalibrationMethod.MinMax,
                        calibration_providers=['CPUExecutionProvider'], nodes_to_exclude=excluded,
                        extra_options={'CalibMaxIntermediateOutputs': 128})
        assert reader.used == 112
        onnx.checker.check_model(str(target))
        x, _ = preproc(cv2.imread(str(ROOT / manifest[0]['path'])), (608, 1088))
        out = session(target).run(None, {'images': x[None]})[0]
        assert out.shape == (1, 13566, 6) and np.isfinite(out).all()
        result['candidates'][candidate] = {'model_sha256': sha(target), 'bytes': target.stat().st_size,
            'excluded_conv_nodes': excluded, 'quantized_conv_count': len(conv) - len(excluded),
            'calibration_samples': reader.used, 'smoke_finite': True}
        print(f'{candidate}: quantized {len(conv)-len(excluded)} Conv nodes', flush=True)
        save(RAW / 'candidate-models.json', result)


def score(benchmark):
    from evaluate_tracking import motmetrics_score, sequences
    models = json.loads((RAW / 'candidate-models.json').read_text())
    baseline = json.loads((ROOT / 'results/phase-3/evaluation-final.json').read_text())['results'][benchmark]['end-to-end']['nano']
    if benchmark == 'MOT17':
        candidates = CANDIDATES
    else:
        selection = json.loads((RAW / 'selection.json').read_text())
        assert selection['selected'] is not None
        candidates = (selection['selected'],)
    scored = {}
    for candidate in candidates:
        assert sha(BASE / f'{candidate}.onnx') == models['candidates'][candidate]['model_sha256']
        folder = BASE / 'tracks' / benchmark / candidate
        hashes, coverage = {}, {}
        for seq in sequences(benchmark):
            file = folder / (seq.name + '.txt')
            times = list(csv.DictReader(file.with_suffix('.txt.timing.csv').open()))
            expected = int(sequence_info(seq)['seqlength'])
            assert len(times) == expected and [int(t['frame']) for t in times] == list(range(1, expected+1))
            assert all(int(t['threads']) == 4 for t in times)
            frozen = ROOT / 'data/phase-3/tracks/end-to-end/nano' / file.name
            assert sha(frozen) == baseline['sha256'][seq.name]
            values = np.loadtxt(file, delimiter=',', ndmin=2)
            assert values.size and np.isfinite(values).all()
            assert (values[:, 0] >= 1).all() and (values[:, 0] <= expected).all()
            hashes[seq.name] = sha(file)
            coverage[seq.name] = {'frames': expected, 'rows': len(values)}
        measured = motmetrics_score(benchmark, folder)
        old = baseline['scores']['motmetrics']['OVERALL']
        loss = {k: old[k] - measured['OVERALL'][k] for k in ('mota', 'idf1')}
        scored[candidate] = {'motmetrics': measured, 'loss_pp_vs_fp32': loss,
                             'sha256': hashes, 'coverage': coverage}
        print(f'{benchmark}/{candidate}: {measured["OVERALL"]}, loss={loss}', flush=True)
    result = {**context(), 'benchmark': benchmark, 'candidates': scored,
              'baseline_motmetrics': baseline['scores']['motmetrics']}
    save(RAW / f'evaluation-{benchmark}.json', result)
    if benchmark == 'MOT17':
        selected = next((c for c in CANDIDATES if all(v <= 1 for v in scored[c]['loss_pp_vs_fp32'].values())), None)
        save(RAW / 'selection.json', {**context(), 'selected': selected,
            'selected_model_sha256': sha(BASE / f'{selected}.onnx') if selected else None,
            'selection_data': 'MOT17 only; both complete 5316-frame evaluations',
            'rule': 'first predefined candidate with MOTA and IDF1 losses <=1.0 pp',
            'development_scores': scored})
        print(f'pre-held-out selection: {selected}', flush=True)


def weight_control():
    decision = json.loads((RAW / 'selection.json').read_text())
    assert decision['selected'] is None, 'Control allowed only after both candidates fail.'
    target = BASE / 'weight-control.onnx'
    assert not target.exists(), 'Refuse model overwrite.'
    model, original = onnx.load(PREPARED), onnx.load(ORIGINAL)
    original_nodes = {n.name: n for n in original.graph.node}
    dq = {n.output[0]: n for n in original.graph.node if n.op_type == 'DequantizeLinear'}
    initials = {t.name: t for t in original.graph.initializer}
    nodes, added, removed = [], {}, set()
    for node in model.graph.node:
        if node.op_type == 'Conv':
            weight = node.input[1]
            source_dq = dq[original_nodes[node.name].input[1]]
            assert numpy_helper.to_array(initials[source_dq.input[0]]).dtype == np.int8
            for name in source_dq.input:
                added[name] = copy.deepcopy(initials[name])
            new_dq = copy.deepcopy(source_dq)
            new_dq.output[0] = weight
            nodes.append(new_dq)
            removed.add(weight)
        nodes.append(node)
    del model.graph.node[:]
    model.graph.node.extend(nodes)
    keep = [t for t in model.graph.initializer if t.name not in removed]
    del model.graph.initializer[:]
    model.graph.initializer.extend(keep + list(added.values()))
    assert len(removed) == 113 and not any(n.op_type == 'QuantizeLinear' for n in nodes)
    onnx.checker.check_model(model)
    onnx.save(model, target)
    models = json.loads((RAW / 'candidate-models.json').read_text())
    models['candidates']['weight-control'] = {**context(), 'model_sha256': sha(target),
        'bytes': target.stat().st_size, 'quantized_weight_conv_count': len(removed),
        'activation_quantization_nodes': 0, 'compute': 'FP32',
        'weight_quantization': 'Original S8S8 artifact exact INT8 weights/scales; biases remain original FP32.'}
    save(RAW / 'candidate-models.json', models)
    print('weight-control: exact original INT8 weights; all activations/biases FP32', flush=True)


def score_control():
    # Reuse the unchanged scorer, changing only the explicitly declared candidate set.
    global CANDIDATES
    prior = json.loads((RAW / 'selection.json').read_text())
    assert prior['selected'] is None
    shutil.copyfile(RAW / 'selection.json', RAW / 'selection-original-candidates.json')
    shutil.copyfile(RAW / 'evaluation-MOT17.json', RAW / 'evaluation-MOT17-original-candidates.json')
    CANDIDATES = ('weight-control',)
    score('MOT17')
    selection = json.loads((RAW / 'selection.json').read_text())
    selection['compute'] = 'FP32; INT8 weight storage only'
    selection['prior_failed_selection'] = 'results/phase-4-repair/selection-original-candidates.json'
    save(RAW / 'selection.json', selection)


def report():
    declaration = json.loads((RAW / 'selection.json').read_text())
    selected = declaration['selected']
    development = json.loads((RAW / 'evaluation-MOT17.json').read_text())['candidates']
    prior_path = RAW / 'evaluation-MOT17-original-candidates.json'
    if prior_path.exists():
        development = {**json.loads(prior_path.read_text())['candidates'], **development}
    result = {**context(), 'status': 'post-hoc-development-complete-no-qualifying-remedy',
        'original_static_int8_failure_preserved': True, 'accepted_baseline_replaced': False,
        'diagnosis': {'report': 'results/phase-4-nano-diagnosis.json',
                      'sha256': sha(ROOT/'results/phase-4-nano-diagnosis.json')},
        'candidate_models': json.loads((RAW/'candidate-models.json').read_text()),
        'MOT17_development': development, 'pre_held_out_selection': declaration,
        'original_MOT20_int8_mota': -0.07949840209975356,
        'original_MOT20_fp32_mota': 56.02072599139443,
        'MOT20_evaluation_runs': 0, 'usefulness_gates': [], 'benchmark_runs': []}
    if (RAW/'control-invariants.json').exists():
        result['control_invariants'] = json.loads((RAW/'control-invariants.json').read_text())
        result['bias_quantization_error'] = json.loads((RAW/'bias-quantization-error.json').read_text())
    for file, digest in declaration['original_hashes'].items():
        assert sha(ROOT/file) == digest, 'Original model changed.'
    if selected:
        evaluation = json.loads((RAW/'evaluation-MOT20.json').read_text())
        assert sha(BASE/f'{selected}.onnx') == declaration['selected_model_sha256']
        assert evaluation['generated_at_utc'] > declaration['generated_at_utc']
        candidate = evaluation['candidates'][selected]
        assert sum(row['frames'] for row in candidate['coverage'].values()) == 8931
        result['MOT20'] = evaluation
        result['MOT20_evaluation_runs'] = 1
        result['status'] = 'post-hoc-variant-full-measurement-complete'
        for threads in (1, 2, 4):
            speeds = {}
            for precision in ('fp32', selected):
                fps = []
                for repeat in (1, 2, 3):
                    stem = RAW/'benchmark'/f'{precision}-t{threads}-r{repeat}'
                    meta = json.loads(stem.with_suffix('.json').read_text())
                    rows = list(csv.DictReader(stem.with_suffix('.csv').open()))
                    assert len(rows) == 100 and [int(r['frame']) for r in rows] == list(range(51,151))
                    assert meta['threads'] == threads and meta['cpu_max'] == f'{threads*100000} 100000'
                    assert meta['warmup'] == 50 and meta['measured'] == 100
                    times = np.asarray([float(r['end_to_end_ms']) for r in rows])
                    assert np.isfinite(times).all() and (times > 0).all()
                    rate = float(1000/np.mean(times))
                    fps.append(rate)
                    result['benchmark_runs'].append({'precision': precision, 'threads': threads,
                        'repeat': repeat, 'fps': rate, 'p50_ms': float(np.quantile(times,.5)),
                        'p95_ms': float(np.quantile(times,.95)), 'metadata': meta,
                        'csv_sha256': sha(stem.with_suffix('.csv'))})
                speeds[precision] = float(np.median(fps))
            ratio = speeds[selected]/speeds['fp32']
            loss = candidate['loss_pp_vs_fp32']['mota']
            result['usefulness_gates'].append({'threads': threads, 'fp32_fps': speeds['fp32'],
                'variant_fps': speeds[selected], 'speed_ratio': ratio, 'MOTA_loss_pp': loss,
                'speed_ge_1_3': ratio >= 1.3, 'quality_loss_le_1_pp': loss <= 1,
                'pass': ratio >= 1.3 and loss <= 1})
    save(ROOT/'results/phase-4-nano-repair.json', result)
    text = '# Post-hoc nano remedy and diagnostic control\n\n' + result['generated_at_utc'] + '\n\n'
    text += 'Author: ' + AUTHOR + '. [Protocol](../docs/PHASE4_REPAIR.md). '
    text += 'Original static INT8 failure and accepted FP32 baseline remain unchanged.\n\n'
    text += '## MOT17 development: fixed candidates\n\n| Candidate | MOTA | IDF1 | MOTA loss pp | IDF1 loss pp |\n|---|---:|---:|---:|---:|\n'
    for name, row in development.items():
        m, loss = row['motmetrics']['OVERALL'], row['loss_pp_vs_fp32']
        text += f'| {name} | {m["mota"]:.4f} | {m["idf1"]:.4f} | {loss["mota"]:.4f} | {loss["idf1"]:.4f} |\n'
    text += '\nEach candidate processes all 5,316 MOT17 frames with the original C++ tracker. '
    text += 'These are fidelity/development scores, not held-out accuracy. '
    text += 'The first two candidates keep 77/47 convolutions activation-quantized. '
    if 'weight-control' in development:
        text += 'After both fail the development rule, the conditional control preserves exact original INT8 weight arrays/scales, '
        text += 'with every activation and bias floating. **Weight-control uses FP32 convolution computation; it is not INT8 acceleration.** '
    text += f'Pre-held-out selection: **{selected or "none"}**. The declaration and model hash are saved before any new MOT20 evaluation.\n'
    if selected:
        m = result['MOT20']['candidates'][selected]['motmetrics']['OVERALL']
        text += '\n## Single MOT20 evaluation\n\n'
        text += f'All 8,931 frames evaluated once. Original FP32 MOTA 56.0207; original INT8 MOTA -0.0795. '
        text += f'Selected variant MOTA **{m["mota"]:.4f}**, IDF1 **{m["idf1"]:.4f}** (motmetrics).\n\n'
        text += '| Threads / CPU quota | Paired FP32 FPS | Variant FPS | Speed ratio | MOTA loss pp | Original usefulness rule |\n|---|---:|---:|---:|---:|---|\n'
        for r in result['usefulness_gates']:
            text += f'| {r["threads"]} | {r["fp32_fps"]:.3f} | {r["variant_fps"]:.3f} | {r["speed_ratio"]:.3f}x | {r["MOTA_loss_pp"]:.4f} | {"PASS" if r["pass"] else "FAIL"} |\n'
        text += '\nThree fresh paired repeats per budget; original 50-frame warm-up/100-frame measured slice. '
        text += 'Raw timing, p50/p95 and memory metadata are retained. Drawing/writing excluded. '
        text += 'No selection or recalibration on MOT20, and no further candidate after this evaluation.\n'
    else:
        text += '\nNo candidate meets both development loss limits. No new MOT20 quality run or benchmark was executed. '
        text += 'A useful nano INT8 repair remains unresolved within this bounded experiment.\n'
    text += '\n## Interpretation and limits\n\n'
    text += 'The [diagnosis](phase-4-nano-diagnosis.md) observes low high-confidence detection counts on MOT20. '
    text += 'MOT17 already shows a stem step of 0.7163 and all observed negative floating activations rounding to zero; '
    text += 'the corresponding integer saturation rate is negligible. Large downstream head errors coexist with this loss of resolution. '
    text += 'This is evidence of destructive numerical resolution loss, not evidence that MOT20 alone exceeded calibration ranges. '
    text += 'The control retains weight quantization but removes activation quantization and restores FP32 biases across the whole network; '
    if 'bias_quantization_error' in result:
        text += f'original bias dequantization differs from FP32 by up to {result["bias_quantization_error"]["max_abs_error"]:.6f}. '
        text += 'The two changes are not separately isolated, so restored quality supports the activation/bias path over weight quantization, '
        text += 'not an exclusive causal attribution to activation quantization. '
    text += 'It does not isolate one causal convolution or prove that negative rounding alone explains every error. '
    text += 'Post-hoc measurements are clearly separated from the original predeclared experiment. No baseline replacement, '
    text += 'fresh-clone acceptance of these uncommitted additions, cold-install or edge-device claim.\n'
    text += '\nFirst candidate-build attempt failed because ORT tried to create an inferred helper beside a read-only input. '
    text += 'The failure log is retained; the remedy uses a byte-identical input copy in the new writable directory. '
    text += 'Outside-window diagnostic v1 is archived; v2 distinguishes rounding from true clamp saturation. '
    text += 'Neither correction changes the original artifacts or container protections.\n'
    text += 'The original development driver also exits 127 after saving both scores/null selection because the executor edited '
    text += 'the still-running shell file; its full log is retained. Subsequent stages use the completed saved driver.\n'
    (ROOT/'results/phase-4-nano-repair.md').write_text(text)
    print(f'report complete: {result["status"]}; selected={selected}', flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('stage', choices=['diagnose', 'quantize', 'score-mot17', 'score-mot20',
                                    'weight-control', 'score-control', 'report'])
    a = p.parse_args()
    BASE.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    cv2.setNumThreads(1)
    if a.stage == 'diagnose':
        diagnose()
    elif a.stage == 'quantize':
        quantize()
    elif a.stage == 'weight-control':
        weight_control()
    elif a.stage == 'score-control':
        score_control()
    elif a.stage == 'report':
        report()
    else:
        score('MOT17' if a.stage == 'score-mot17' else 'MOT20')


if __name__ == '__main__':
    main()
