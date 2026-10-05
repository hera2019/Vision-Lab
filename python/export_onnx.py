"""Export a ByteTrack YOLOX checkpoint to ONNX with raw head outputs.

Output: models/bytetrack_<variant>_mot17.onnx, input `images` [1,3,H,W],
output `output` [1,N,6] = (x, y, w, h) grid offsets, objectness, class score.
Box decoding, NMS and tracking happen downstream (C++).
"""
import argparse
import hashlib
from pathlib import Path

import onnx
import torch

from vl_common import load_model

OPSET = 13  # >= 13 needed later for per-channel INT8 QDQ quantization.


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("variant", choices=["nano", "tiny"])
    args = parser.parse_args()

    exp, model = load_model(args.variant)
    out = Path(f"/work/models/bytetrack_{args.variant}_mot17.onnx")
    dummy = torch.zeros(1, 3, *exp.test_size)
    torch.onnx.export(
        model, dummy, str(out),
        input_names=["images"], output_names=["output"],
        opset_version=OPSET, dynamo=False,
    )
    onnx.checker.check_model(onnx.load(str(out)))
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"{out.name} test_size={exp.test_size} opset={OPSET} sha256={digest}")


if __name__ == "__main__":
    main()
