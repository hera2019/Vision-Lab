"""Phase 1 follow-up: where does the nano export diff come from, and does it matter?

Run after check_export_parity.py failed for nano (max abs diff 1.18e-3 > 1e-3).
The pass criterion is NOT changed by this script; it only explains the failure.

For each of the same 20 frames it reports, per ORT graph-optimization level:
  - max abs diff on raw outputs (all anchors, and anchors with score > 0.1)
  - max relative diff on the box-regression channels
  - max diff after decoding to letterboxed-pixel boxes (score > 0.1 anchors)
Writes results/phase-1-parity-investigation.json.
"""
import json
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import torch

from check_export_parity import pick_frames
from vl_common import load_model, preproc

SCORE_THRESHOLD = 0.1
STRIDES = (8, 16, 32)
LEVELS = {
    "ORT_DISABLE_ALL": ort.GraphOptimizationLevel.ORT_DISABLE_ALL,
    "ORT_ENABLE_BASIC": ort.GraphOptimizationLevel.ORT_ENABLE_BASIC,
    "ORT_ENABLE_ALL": ort.GraphOptimizationLevel.ORT_ENABLE_ALL,
}


def grids_and_strides(h, w):
    grids, strides = [], []
    for s in STRIDES:
        hs, ws = h // s, w // s
        yv, xv = np.meshgrid(np.arange(hs), np.arange(ws), indexing="ij")
        grids.append(np.stack((xv, yv), 2).reshape(-1, 2))
        strides.append(np.full((hs * ws, 1), s))
    return np.concatenate(grids).astype(np.float64), np.concatenate(strides).astype(np.float64)


def decode(raw, grids, strides):
    """Same arithmetic as YOLOXHead.decode_outputs, in float64."""
    out = raw.astype(np.float64).copy()
    out[:, :2] = (out[:, :2] + grids) * strides
    out[:, 2:4] = np.exp(out[:, 2:4]) * strides
    return out


def main():
    frames = pick_frames()
    report = {"variants": {}}
    for variant in ("nano", "tiny"):
        exp, model = load_model(variant)
        grids, strides = grids_and_strides(*exp.test_size)
        inputs, refs = [], []
        for path in frames:
            x, _ = preproc(cv2.imread(str(path)), exp.test_size)
            with torch.no_grad():
                refs.append(model(torch.from_numpy(x)[None]).numpy()[0])
            inputs.append(x)

        per_level = {}
        for name, level in LEVELS.items():
            opts = ort.SessionOptions()
            opts.graph_optimization_level = level
            sess = ort.InferenceSession(f"/work/models/bytetrack_{variant}_mot17.onnx", opts,
                                        providers=["CPUExecutionProvider"])
            stats = {"raw_all": 0.0, "raw_scored": 0.0, "box_rel": 0.0,
                     "decoded_px_scored": 0.0, "score_scored": 0.0, "worst_anchor": None}
            for x, ref in zip(inputs, refs):
                got = sess.run(None, {"images": x[None]})[0][0]
                diff = np.abs(ref - got)
                scored = (ref[:, 4] * ref[:, 5]) > SCORE_THRESHOLD
                rel = diff[:, :4] / np.maximum(np.abs(ref[:, :4]), 1e-6)
                dec = np.abs(decode(ref, grids, strides) - decode(got, grids, strides))
                i = int(diff.max(axis=1).argmax())
                if diff[i].max() > stats["raw_all"]:
                    stats["worst_anchor"] = {
                        "anchor": i, "stride": int(strides[i, 0]),
                        "ref_value": float(ref[i, int(diff[i].argmax())]),
                        "score": float(ref[i, 4] * ref[i, 5]),
                    }
                stats["raw_all"] = max(stats["raw_all"], float(diff.max()))
                stats["box_rel"] = max(stats["box_rel"], float(rel.max()))
                if scored.any():
                    stats["raw_scored"] = max(stats["raw_scored"], float(diff[scored].max()))
                    stats["decoded_px_scored"] = max(stats["decoded_px_scored"],
                                                     float(dec[scored, :4].max()))
                    stats["score_scored"] = max(stats["score_scored"],
                                                float(dec[scored, 4:6].max()))
            per_level[name] = stats
        report["variants"][variant] = per_level

    out = Path("/work/results/phase-1-parity-investigation.json")
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
