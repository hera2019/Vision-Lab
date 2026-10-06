"""Phase 2: C++ detector vs Python ONNX Runtime reference on the Phase 1 frames.

  python check_cpp_detector.py frames    # write the frame list for the C++ run
  python check_cpp_detector.py compare   # run the reference, compare, write results

Reference path = ByteTrack's own code: yolox preproc, ONNX Runtime, the same
decode arithmetic as YOLOXHead.decode_outputs, yolox.utils.postprocess (NMS).

Pass criterion (docs/01-phase-0-plan.md): on each frame the same number of
detections after NMS; every box matched with IoU >= 0.99 and |score diff| <= 1e-3.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
import torch

from check_export_parity import pick_frames
from vl_common import preproc

CONF_THRESHOLD = 0.01  # ByteTrack tools/track.py --conf default
NMS_THRESHOLD = 0.7    # ByteTrack tools/track.py --nms default
TEST_SIZE = (608, 1088)
STRIDES = (8, 16, 32)
MIN_IOU = 0.99
MAX_SCORE_DIFF = 1e-3

WORK = Path("/work")
OUT_DIR = WORK / "results/phase-2"
FRAME_LIST = OUT_DIR / "frames.txt"


def decode(raw):
    """YOLOXHead.decode_outputs, on a [1, N, 6] tensor."""
    grids, strides = [], []
    for s in STRIDES:
        hs, ws = TEST_SIZE[0] // s, TEST_SIZE[1] // s
        yv, xv = torch.meshgrid([torch.arange(hs), torch.arange(ws)], indexing="ij")
        grids.append(torch.stack((xv, yv), 2).view(1, -1, 2))
        strides.append(torch.full((1, hs * ws, 1), s))
    grids = torch.cat(grids, 1).float()
    strides = torch.cat(strides, 1).float()
    out = raw.clone()
    out[..., :2] = (out[..., :2] + grids) * strides
    out[..., 2:4] = torch.exp(out[..., 2:4]) * strides
    return out


def reference_detections(sess, path):
    from yolox.utils import postprocess

    x, ratio = preproc(cv2.imread(str(path)), TEST_SIZE)
    raw = torch.from_numpy(sess.run(None, {"images": x[None]})[0])
    dets = postprocess(decode(raw), 1, CONF_THRESHOLD, NMS_THRESHOLD)[0]
    if dets is None:
        return np.zeros((0, 5))
    boxes = dets[:, :4].numpy() / ratio
    scores = (dets[:, 4] * dets[:, 5]).numpy()
    return np.column_stack([boxes, scores])


def iou(a, b):
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union


def match(ref, cpp):
    """Greedy: each reference box (by descending score) takes its best unmatched C++ box."""
    used, pairs = set(), []
    for r in ref[np.argsort(-ref[:, 4])]:
        best_j, best_iou = None, -1.0
        for j, c in enumerate(cpp):
            if j not in used and (v := iou(r, c)) > best_iou:
                best_j, best_iou = j, v
        if best_j is None:
            break
        used.add(best_j)
        pairs.append((best_iou, abs(r[4] - cpp[best_j][4])))
    return pairs


def compare_variant(variant, frames):
    sess = ort.InferenceSession(str(WORK / f"models/bytetrack_{variant}_mot17.onnx"),
                                providers=["CPUExecutionProvider"])
    cpp_run = json.loads((OUT_DIR / f"cpp-{variant}.json").read_text())
    cpp_by_frame = {Path(f["frame"]): np.array(f["detections"]).reshape(-1, 5)
                    for f in cpp_run["frames"]}

    per_frame = []
    for path in frames:
        ref = reference_detections(sess, path)
        cpp = cpp_by_frame[path]
        pairs = match(ref, cpp)
        min_iou = min((p[0] for p in pairs), default=1.0)
        max_sd = max((p[1] for p in pairs), default=0.0)
        per_frame.append({
            "frame": str(path.relative_to(WORK / "data/MOT17/train")),
            "count": {"python": len(ref), "cpp": len(cpp)},
            "min_iou": float(min_iou),
            "max_score_diff": float(max_sd),
            "pass": bool(len(ref) == len(cpp) and min_iou >= MIN_IOU and max_sd <= MAX_SCORE_DIFF),
        })
    return {
        "pass": all(f["pass"] for f in per_frame),
        "total_detections": {"python": sum(f["count"]["python"] for f in per_frame),
                             "cpp": sum(f["count"]["cpp"] for f in per_frame)},
        "min_iou": min(f["min_iou"] for f in per_frame),
        "max_score_diff": max(f["max_score_diff"] for f in per_frame),
        "frames": per_frame,
    }


def main():
    frames = pick_frames()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if sys.argv[1] == "frames":
        FRAME_LIST.write_text("".join(f"{p}\n" for p in frames))
        return
    result = {
        "phase": 2,
        "check": "cpp_detector_vs_python_reference_after_nms",
        "conf_threshold": CONF_THRESHOLD,
        "nms_threshold": NMS_THRESHOLD,
        "criteria": {"same_count": True, "min_iou": MIN_IOU, "max_score_diff": MAX_SCORE_DIFF},
        "versions": {"onnxruntime": ort.__version__, "opencv_python": cv2.__version__,
                     "torch": torch.__version__},
        "variants": {v: compare_variant(v, frames) for v in ("nano", "tiny")},
    }
    (WORK / "results/phase-2-detector-parity.json").write_text(json.dumps(result, indent=2) + "\n")
    for v, r in result["variants"].items():
        print(f"{v}: pass={r['pass']} dets={r['total_detections']} "
              f"min_iou={r['min_iou']:.6f} max_score_diff={r['max_score_diff']:.2e}")


if __name__ == "__main__":
    main()
