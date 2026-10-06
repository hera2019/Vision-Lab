"""Track a C++ detection cache with the unmodified official Python BYTETracker."""
import argparse
import json
import time
from pathlib import Path
from phase3_common import config, read_cache, sequence_info
from yolox.tracker.byte_tracker import BYTETracker

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sequence", required=True)
    p.add_argument("--cache", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--limit", type=int)
    a = p.parse_args()
    info = sequence_info(a.sequence)
    frames = int(info["seqlength"])
    detections = read_cache(a.cache, frames)
    size = (int(info["imheight"]), int(info["imwidth"]))
    tracker = BYTETracker(config(info["name"]), frame_rate=30)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    begin = time.perf_counter()
    with out.open("w") as target:
        for frame in range(1, min(frames, a.limit or frames) + 1):
            if len(detections[frame]) == 0:
                continue
            for t in tracker.update(detections[frame], size, size):
                x, y, w, h = t.tlwh
                if w*h <= 100 or w/h > 1.6:
                    continue
                target.write(f"{frame},{t.track_id},{round(x, 1)},{round(y, 1)},"
                             f"{round(w, 1)},{round(h, 1)},{round(t.score, 2)},-1,-1,-1\n")
    elapsed = time.perf_counter() - begin
    out.with_suffix(".run.json").write_text(json.dumps({"seconds": elapsed,
        "sequence": info["name"], "frames": min(frames, a.limit or frames),
        "config": vars(config(info["name"])), "frame_rate": 30}, indent=2) + "\n")
    print(f"{info['name']}: {elapsed:.2f}s -> {out}", flush=True)

if __name__ == "__main__":
    main()
