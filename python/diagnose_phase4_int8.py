"""Read-only failure diagnosis on three fixed development frames, no retuning."""
import hashlib
import json
import cv2
import numpy as np
import onnxruntime as ort
import torch
from check_cpp_detector import decode
from phase3_common import ROOT
from vl_common import preproc, RGB_MEAN, RGB_STD
from yolox.utils import postprocess

cv2.setNumThreads(1)
torch.set_num_threads(1)
frames = [1, 51, 150]  # Existing calibration/benchmark sequence; no MOT20 input.
paths = [ROOT/'data/MOT17/train/MOT17-02-FRCNN/img1'/f'{n:06d}.jpg' for n in frames]
inputs, preprocessing = [], []
for path in paths:
    bgr = cv2.imread(str(path))
    x, ratio = preproc(bgr, (608, 1088))
    resized = cv2.resize(bgr, (int(bgr.shape[1]*ratio), int(bgr.shape[0]*ratio)))
    padded = np.full((608, 1088, 3), 114, dtype=np.float32)
    padded[:resized.shape[0], :resized.shape[1]] = resized
    mean, std = np.array(RGB_MEAN, dtype=np.float32), np.array(RGB_STD, dtype=np.float32)
    cpp_formula = ((padded[:, :, ::-1]/np.float32(255)-mean)/std).transpose(2, 0, 1)
    difference = float(np.abs(x-cpp_formula).max())
    assert difference <= 1e-6
    inputs.append(x[None])
    preprocessing.append({'frame': int(path.stem), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'python_vs_cpp_formula_max_abs': difference})

models = {}
for model in ('nano', 'tiny'):
    variants = [('fp32-original', ROOT/'models'/f'bytetrack_{model}_mot17.onnx', True),
                ('fp32-preprocessed', ROOT/'data/phase-4/models'/f'bytetrack_{model}_mot17.preprocessed.onnx', True),
                ('int8-optimized', ROOT/'data/phase-4/models'/f'bytetrack_{model}_mot17.int8.onnx', True),
                ('int8-optimization-disabled', ROOT/'data/phase-4/models'/f'bytetrack_{model}_mot17.int8.onnx', False)]
    reference, measurements = {}, {}
    for label, path, optimized in variants:
        options = ort.SessionOptions()
        options.intra_op_num_threads = options.inter_op_num_threads = 1
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL if optimized else ort.GraphOptimizationLevel.ORT_DISABLE_ALL
        session = ort.InferenceSession(str(path), sess_options=options, providers=['CPUExecutionProvider'])
        rows = []
        for frame, x in zip(frames, inputs):
            raw = session.run(None, {'images': x})[0]
            assert np.isfinite(raw).all()
            if label == 'fp32-original':
                reference[frame] = raw
            scores = raw[0, :, 4]*raw[0, :, 5]
            detections = postprocess(decode(torch.from_numpy(raw.copy())), 1, 0.01, 0.7)[0]
            high = int(((detections[:, 4]*detections[:, 5]) >= 0.6).sum()) if detections is not None else 0
            rows.append({'frame': frame, 'raw_max_abs_diff_from_fp32': float(np.abs(raw-reference[frame]).max()),
                'confidence_max': float(scores.max()), 'candidates_at_0_01': int((scores >= 0.01).sum()),
                'post_nms_boxes_at_0_01': 0 if detections is None else len(detections),
                'post_nms_boxes_at_0_6': high})
        measurements[label] = rows
        del session
    models[model] = measurements

result = {'scope': 'Read-only diagnosis on MOT17-02 frames 1/51/150; no held-out input, modified model or alternative quality score.',
          'preprocessing': preprocessing, 'models': models,
          'note': 'Optimization-disabled INT8 is diagnostic only. It is not benchmarked or proposed as a replacement. No setting, model, threshold or calibration changes.'}
(ROOT/'results/phase-4-int8-diagnostic.json').write_text(json.dumps(result, indent=2)+'\n')
lines = ['# Phase 4 INT8 failure diagnosis', '', result['scope'], '',
         'The calibration helper uses the same official RGB normalization as the existing Python reference. Independent reconstruction of the C++ formula agrees within 1e-6 on all three fixed images. This is a limited input check, not a full new parity claim.', '',
         '| Model | Graph/runtime | Frame | Raw max difference from original FP32 | Maximum confidence | Post-NMS boxes >=0.01 | Post-NMS boxes >=0.6 |',
         '|---|---|---:|---:|---:|---:|---:|']
for model, variants in models.items():
    for label, rows in variants.items():
        for row in rows:
            lines.append(f'| {model} | {label} | {row["frame"]} | {row["raw_max_abs_diff_from_fp32"]:.6g} | {row["confidence_max"]:.6g} | {row["post_nms_boxes_at_0_01"]} | {row["post_nms_boxes_at_0_6"]} |')
lines += ['', result['note'], '', 'These observations distinguish input preparation, FP32 graph preprocessing and INT8/runtime behavior on a development slice. They do not isolate a specific operator or establish a general root cause. The complete MOT20 failure remains the acceptance result.']
(ROOT/'results/phase-4-int8-diagnostic.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(result), flush=True)
