"""Phase 1: PyTorch vs ONNX Runtime parity on fixed MOT17 frames.

Pass criterion (docs/01-phase-0-plan.md): on 20 fixed frames, raw head outputs
max abs diff <= 1e-3. Writes results/phase-1-export-parity.json.
"""
import json
import random
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import torch

from vl_common import load_model, preproc

MOT17_TRAIN = Path("/work/data/MOT17/train")
N_FRAMES = 20
SEED = 0
TOLERANCE = 1e-3
# Output columns: 0-3 box regression (raw grid offsets / log sizes), 4 objectness, 5 class score.
GROUPS = {"box": slice(0, 4), "objectness": slice(4, 5), "class": slice(5, 6)}


def pick_frames():
    """20 frames sampled with a fixed seed from the FRCNN copy of MOT17 train."""
    pool = sorted(MOT17_TRAIN.glob("MOT17-*-FRCNN/img1/*.jpg"))
    assert pool, f"no frames under {MOT17_TRAIN}"
    return sorted(random.Random(SEED).sample(pool, N_FRAMES))


def check_variant(variant, frames):
    exp, model = load_model(variant)
    onnx_path = Path(f"/work/models/bytetrack_{variant}_mot17.onnx")
    sess = ort.InferenceSession(str(onnx_path), providers=["CPUExecutionProvider"])

    per_frame = []
    for path in frames:
        x, _ = preproc(cv2.imread(str(path)), exp.test_size)
        with torch.no_grad():
            ref = model(torch.from_numpy(x)[None]).numpy()
        got = sess.run(None, {"images": x[None]})[0]
        assert ref.shape == got.shape, (ref.shape, got.shape)
        diff = np.abs(ref - got)
        # Candidate detections as the tracker would see them: obj * cls > 0.1.
        ref_cand = int(((ref[0, :, 4] * ref[0, :, 5]) > 0.1).sum())
        got_cand = int(((got[0, :, 4] * got[0, :, 5]) > 0.1).sum())
        per_frame.append({
            "frame": str(path.relative_to(MOT17_TRAIN)),
            "max_abs_diff": float(diff.max()),
            "max_abs_diff_by_group": {k: float(diff[0, :, s].max()) for k, s in GROUPS.items()},
            "max_abs_ref_box": float(np.abs(ref[0, :, 0:4]).max()),
            "candidates_score_gt_0.1": {"torch": ref_cand, "onnxruntime": got_cand},
        })

    worst = max(f["max_abs_diff"] for f in per_frame)
    return {
        "onnx": onnx_path.name,
        "output_shape": list(got.shape),
        "test_size": list(exp.test_size),
        "max_abs_diff": worst,
        "pass": worst <= TOLERANCE,
        "frames": per_frame,
    }


def main():
    frames = pick_frames()
    result = {
        "phase": 1,
        "check": "pytorch_vs_onnxruntime_raw_outputs",
        "tolerance": TOLERANCE,
        "seed": SEED,
        "versions": {"torch": torch.__version__, "onnxruntime": ort.__version__,
                     "opencv": cv2.__version__, "numpy": np.__version__},
        "variants": {v: check_variant(v, frames) for v in ("nano", "tiny")},
    }
    out = Path("/work/results/phase-1-export-parity.json")
    out.write_text(json.dumps(result, indent=2) + "\n")
    for v, r in result["variants"].items():
        print(f"{v}: max_abs_diff={r['max_abs_diff']:.3e} pass={r['pass']}")


if __name__ == "__main__":
    main()
