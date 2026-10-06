"""Read-only replay of the owner-reported MOT20-03 IDs 75 -> 107 case.

Uses the frozen nano cache and official tracker, with no parameter changes.
Run inside the existing pytools image through scripts/drun.sh.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from phase3_common import config, read_cache, sequence_info
from yolox.tracker.byte_tracker import BYTETracker

ROOT = Path('/work')
sequence = ROOT / 'data/MOT20/train/MOT20-03'
cache = ROOT / 'data/phase-3/dets/nano/MOT20-03.txt'
tracks = ROOT / 'data/phase-3/tracks/end-to-end/nano/MOT20-03.txt'
reference = ROOT / 'data/phase-3/tracks/python/nano/MOT20-03.txt'
gt_path = sequence / 'gt/gt.txt'
info = sequence_info(sequence)
size = (int(info['imheight']), int(info['imwidth']))
fps = int(info['framerate'])
rows = np.loadtxt(tracks, delimiter=',')
py_rows = np.loadtxt(reference, delimiter=',')
gt = np.loadtxt(gt_path, delimiter=',')


def iou(a, b):
    """Continuous-box geometry, used only for inspecting GT correspondence."""
    a, b = np.asarray(a), np.asarray(b)
    intersection = np.maximum(0, np.minimum(a[:2]+a[2:4], b[:2]+b[2:4])
                              - np.maximum(a[:2], b[:2])).prod()
    return float(intersection / (a[2]*a[3]+b[2]*b[3]-intersection))


endpoints = {}
for tid in (75, 107):
    chosen = rows[(rows[:, 1] == tid) & (rows[:, 0] <= 300)]
    py_chosen = py_rows[(py_rows[:, 1] == tid) & (py_rows[:, 0] <= 300)]
    endpoints[str(tid)] = {'first_row': chosen[0].tolist(),
                           'last_row': chosen[-1].tolist(),
                           'emitted_frames': int(len(chosen)),
                           'python_same_frames_ids_boxes': bool(
                               np.array_equal(chosen[:, :6], py_chosen[:, :6]))}

gt_matches = []
for frame, tid in ((130, 75), (141, 75), (180, 107)):
    tracked = rows[(rows[:, 0] == frame) & (rows[:, 1] == tid)][0]
    candidates = gt[(gt[:, 0] == frame) & (gt[:, 6] == 1) & (gt[:, 7] == 1)]
    ranked = sorted(((iou(tracked[2:6], g[2:6]), g) for g in candidates),
                    key=lambda x: x[0], reverse=True)[:3]
    gt_matches.append({'frame': frame, 'track_id': tid, 'top_matches': [
        {'gt_id': int(g[1]), 'iou': overlap, 'visibility': float(g[8]),
         'box': g[2:6].tolist()} for overlap, g in ranked]})

detections = read_cache(cache, int(info['seqlength']))
tracker = BYTETracker(config(info['name']), frame_rate=30)
transitions = []
previous = {}
for frame in range(1, 186):
    if len(detections[frame]) == 0:
        continue
    emitted = tracker.update(detections[frame], size, size)
    for tid in (75, 107):
        locations = {}
        for collection in ('tracked_stracks', 'lost_stracks', 'removed_stracks'):
            for track in getattr(tracker, collection):
                if track.track_id == tid:
                    locations[collection] = {'state': int(track.state),
                        'activated': bool(track.is_activated),
                        'start_update': int(track.start_frame),
                        'last_matched_update': int(track.end_frame)}
        signature = [(name, value['state'], value['activated'])
                     for name, value in locations.items()]
        if signature != previous.get(tid, []):
            transitions.append({'source_frame': frame,
                'tracker_update': int(tracker.frame_id), 'id': tid,
                'collections': locations,
                'in_tracker_output': any(t.track_id == tid for t in emitted)})
        previous[tid] = signature

result = {'sequence': info['name'], 'model': 'nano', 'source_fps': fps,
    'frozen_config': vars(config(info['name'])),
    'tracker_frame_rate_argument': 30, 'max_time_lost_updates': tracker.max_time_lost,
    'endpoints_in_demo': endpoints,
    'missing_output_frames_between_ids': int(endpoints['107']['first_row'][0]
                                             - endpoints['75']['last_row'][0] - 1),
    'gt_correspondence': gt_matches,
    'reference_state_transitions': transitions,
    'state_enum': {'new': 0, 'tracked': 1, 'lost': 2, 'removed': 3},
    'input_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (cache, tracks, reference, gt_path)},
    'scope': 'Owner-reported failure inspection; no detector/tracker setting changed.'}
destination = ROOT / 'results/phase-3-occlusion-case-75-107.json'
destination.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if k != 'input_sha256'}, indent=2))
