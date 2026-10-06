"""Phase 3 compatibility and sequence configuration; never edits external code."""
import configparser
from pathlib import Path
from types import SimpleNamespace
import numpy as np

# ByteTrack / TrackEval use aliases removed in NumPy 1.24; motmetrics 1.4
# additionally uses np.asfarray removed in NumPy 2.
for name, value in {"float": float, "int": int, "bool": bool}.items():
    if name not in np.__dict__:
        setattr(np, name, value)
if not hasattr(np, "asfarray"):
    np.asfarray = lambda a, dtype=float: np.asarray(a, dtype=dtype if np.issubdtype(dtype, np.inexact) else float)

ROOT = Path("/work")

def sequence_info(path):
    c = configparser.ConfigParser()
    c.read(Path(path) / "seqinfo.ini")
    return dict(c["Sequence"])

def config(name):
    # Same sequence overrides as mot_evaluator.evaluate(), with A1 MOT20 defaults.
    threshold = {"MOT17-01-FRCNN": .65, "MOT17-06-FRCNN": .65,
                 "MOT17-12-FRCNN": .7, "MOT17-14-FRCNN": .67}.get(name, .6)
    buffer = {"MOT17-05-FRCNN": 14, "MOT17-06-FRCNN": 14,
              "MOT17-13-FRCNN": 25, "MOT17-14-FRCNN": 25}.get(name, 30)
    return SimpleNamespace(track_thresh=threshold, track_buffer=buffer,
                           match_thresh=.9, mot20=False)

def read_cache(path, frames):
    detections = [[] for _ in range(frames + 1)]
    with open(path) as source:
        for line in source:
            fields = line.strip().split(",")
            detections[int(fields[0])].append([float(x) for x in fields[2:7]])
    # Restore original detector float32 values from the 9-significant-digit cache.
    return [np.asarray(x, dtype=np.float32).reshape(-1, 5) for x in detections]
