"""Shared helpers for the Python reference path (export, parity, evaluation)."""
from pathlib import Path

import torch
from torch import nn

BYTETRACK_ROOT = Path("/work/external/ByteTrack")
EXP_FILES = {
    "nano": BYTETRACK_ROOT / "exps/example/mot/yolox_nano_mix_det.py",
    "tiny": BYTETRACK_ROOT / "exps/example/mot/yolox_tiny_mix_det.py",
}
CHECKPOINTS = {
    "nano": Path("/work/models/bytetrack_nano_mot17.pth.tar"),
    "tiny": Path("/work/models/bytetrack_tiny_mot17.pth.tar"),
}
# Normalisation used by ByteTrack's tracking tools (tools/track.py, demo_track.py).
RGB_MEAN = (0.485, 0.456, 0.406)
RGB_STD = (0.229, 0.224, 0.225)


def load_model(variant):
    """Build the ByteTrack YOLOX model with raw (undecoded) head outputs."""
    from yolox.exp import get_exp
    from yolox.models.network_blocks import SiLU
    from yolox.utils import replace_module

    exp = get_exp(str(EXP_FILES[variant]), None)
    model = exp.get_model()
    ckpt = torch.load(CHECKPOINTS[variant], map_location="cpu", weights_only=False)
    model.load_state_dict(ckpt.get("model", ckpt))
    model.eval()
    # Same export-time substitutions as ByteTrack's tools/export_onnx.py.
    model = replace_module(model, nn.SiLU, SiLU)
    model.head.decode_in_inference = False
    return exp, model


def preproc(image_bgr, input_size):
    """Letterbox + normalise with ByteTrack's own function.

    Returns a CHW float32 array and the resize ratio.
    """
    from yolox.data.data_augment import preproc as bytetrack_preproc

    return bytetrack_preproc(image_bgr, input_size, RGB_MEAN, RGB_STD)
