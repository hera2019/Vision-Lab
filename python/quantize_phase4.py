"""Predeclared static QDQ experiment; requires the separately approved dependency."""
import hashlib
import json
import time
from collections import Counter
from pathlib import Path
import cv2
import numpy as np
import onnx
import onnxruntime as ort
from phase3_common import ROOT, sequence_info
from vl_common import preproc


def main():
    # Import intentionally fails in the original image: do not fake ml_dtypes.
    from onnxruntime.quantization import (CalibrationDataReader, CalibrationMethod,
        QuantFormat, QuantType, quantize_static)
    from onnxruntime.quantization.shape_inference import quant_pre_process
    import ml_dtypes
    cv2.setNumThreads(1)
    base = ROOT/'data/phase-4/models'
    base.mkdir(parents=True, exist_ok=True)
    frames = []
    for sequence in sorted((ROOT/'data/MOT17/train').glob('*-FRCNN')):
        count = int(sequence_info(sequence)['seqlength'])
        frames.extend(sequence/'img1'/f'{index:06d}.jpg'
                      for index in np.linspace(1, count, 16, dtype=int))
    assert len(frames) == 112 and all('MOT17/train/' in str(p) for p in frames)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p)} for p in frames]
    (ROOT/'results/phase-4/calibration-frames.json').write_text(json.dumps(manifest, indent=2)+'\n')

    class Reader(CalibrationDataReader):
        def __init__(self):
            self.iterator = iter(frames)
            self.used = 0
        def get_next(self):
            path = next(self.iterator, None)
            if path is None:
                return None
            image = cv2.imread(str(path))
            if image is None:
                raise RuntimeError(f'Cannot decode calibration image {path}')
            array, _ = preproc(image, (608, 1088))
            self.used += 1
            return {'images': array[None]}

    for model in ('nano', 'tiny'):
        source = ROOT/'models'/f'bytetrack_{model}_mot17.onnx'
        prepared = base/f'bytetrack_{model}_mot17.preprocessed.onnx'
        output = base/f'bytetrack_{model}_mot17.int8.onnx'
        digest = sha(source)
        started = time.perf_counter()
        print(f'{model}: preprocessing and 112-frame MOT17-only calibration', flush=True)
        quant_pre_process(source, prepared)
        reader = Reader()
        quantize_static(prepared, output, reader, quant_format=QuantFormat.QDQ,
            op_types_to_quantize=['Conv'], per_channel=True, reduce_range=False,
            activation_type=QuantType.QInt8, weight_type=QuantType.QInt8,
            calibrate_method=CalibrationMethod.MinMax,
            calibration_providers=['CPUExecutionProvider'],
            # ORT 1.30 clears, rather than merges, when this limit is reached.
            # Keep every one of the fixed 112 observations below the limit.
            extra_options={'CalibMaxIntermediateOutputs': 128})
        assert reader.used == 112
        onnx.checker.check_model(str(output))
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        session = ort.InferenceSession(str(output), sess_options=options,
                                       providers=['CPUExecutionProvider'])
        image, _ = preproc(cv2.imread(str(frames[0])), (608, 1088))
        raw = session.run(None, {'images': image[None]})[0]
        assert raw.shape == (1, 13566, 6) and np.isfinite(raw).all()
        assert sha(source) == digest
        graph = onnx.load(output)
        result = {'model': model, 'status': 'quantized-smoke-pass',
            'scheme': 'Static QDQ; Conv only; S8S8; per-channel weights; MinMax; no reduced range',
            'calibration_frames': manifest, 'source_sha256': digest,
            'calibration_reader_samples': reader.used, 'calib_intermediate_cap': 128,
            'preprocessed_sha256': sha(prepared), 'int8_sha256': sha(output),
            'source_bytes': source.stat().st_size, 'int8_bytes': output.stat().st_size,
            'node_types': dict(Counter(n.op_type for n in graph.graph.node)),
            'initializer_types': dict(Counter(int(t.data_type) for t in graph.graph.initializer)),
            'smoke_shape': list(raw.shape), 'smoke_all_finite': True,
            'seconds': time.perf_counter()-started,
            'versions': {'onnxruntime': ort.__version__, 'onnx': onnx.__version__,
                         'ml_dtypes': ml_dtypes.__version__}}
        (ROOT/'results/phase-4'/f'quantization-{model}.json').write_text(json.dumps(result, indent=2)+'\n')
        print(f'{model}: static INT8 smoke pass, {result["int8_bytes"]} bytes', flush=True)


if __name__ == '__main__':
    main()
