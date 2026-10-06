"""Draw C++ detections (score > 0.6) on one Phase 2 frame for a visual sanity check.

  python draw_sample.py results/phase-2/cpp-nano.json 1 results/phase-2/sample-nano.jpg
"""
import json
import sys
from pathlib import Path

import cv2

SHOW_SCORE = 0.6  # ByteTrack's high-confidence track threshold


def visible_gt_count(frame_path):
    """Pedestrians (class 1, considered) at least 25% visible in this frame."""
    seq_dir = Path(frame_path).parent.parent
    n = int(Path(frame_path).stem)
    count = 0
    for line in (seq_dir / "gt/gt.txt").read_text().splitlines():
        f = line.split(",")
        if int(f[0]) == n and f[6] == "1" and f[7] == "1" and float(f[8]) > 0.25:
            count += 1
    return count


def main():
    run_path, index, out_path = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    frame = json.loads(Path(run_path).read_text())["frames"][index]
    img = cv2.imread(frame["frame"])
    shown = [d for d in frame["detections"] if d[4] > SHOW_SCORE]
    for x1, y1, x2, y2, _ in shown:
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 200, 255), 2)

    h, w = img.shape[:2]
    seq = Path(frame["frame"]).parent.parent.name.replace("-FRCNN", "")
    top = f"C++ detector, score > {SHOW_SCORE}: {len(shown)} boxes | ground truth (>25% visible): " \
          f"{visible_gt_count(frame['frame'])} people"
    bottom = f"{seq} frame {int(Path(frame['frame']).stem)} - MOTChallenge, CC BY-NC-SA 3.0"
    for y0, text in ((0, top), (h - 60, bottom)):
        cv2.rectangle(img, (0, y0), (w, y0 + 60), (0, 0, 0), -1)
        cv2.putText(img, text, (20, y0 + 42), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
    cv2.imwrite(out_path, cv2.resize(img, (w // 2, h // 2)), [cv2.IMWRITE_JPEG_QUALITY, 85])


if __name__ == "__main__":
    main()
