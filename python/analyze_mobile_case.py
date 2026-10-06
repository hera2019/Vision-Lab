"""Frozen-cache inspection of owner-reported MOT17-05 IDs 3 -> 4 -> 18.

Run through scripts/drun.sh in pytools. Observation hooks return the original
matching results unchanged; no external source or configuration is modified.
"""
import hashlib
import json
from collections import Counter
from pathlib import Path
import numpy as np
from phase3_common import config, read_cache, sequence_info
from yolox.tracker.byte_tracker import BYTETracker
from yolox.tracker import matching

ROOT = Path('/work')
NAME = 'MOT17-05-FRCNN'
IDS = (3, 4, 18)
LIMIT = 168
sequence = ROOT / 'data/MOT17/train' / NAME
cache = ROOT / 'data/phase-3/dets/nano' / f'{NAME}.txt'
tracks = ROOT / 'data/phase-3/tracks/end-to-end/nano' / f'{NAME}.txt'
reference = ROOT / 'data/phase-3/tracks/python/nano' / f'{NAME}.txt'
gt_path = sequence / 'gt/gt.txt'
info = sequence_info(sequence)
rows = np.loadtxt(tracks, delimiter=',')
py_rows = np.loadtxt(reference, delimiter=',')
gt = np.loadtxt(gt_path, delimiter=',')


def gt_match(frame, box):
    candidates = gt[(gt[:, 0] == frame) & (gt[:, 6] == 1) & (gt[:, 7] == 1)]
    def overlap(g):
        b = g[2:6]
        area = np.maximum(0, np.minimum(box[:2]+box[2:], b[:2]+b[2:])
                          - np.maximum(box[:2], b[:2])).prod()
        return float(area / (box[2]*box[3]+b[2]*b[3]-area))
    if not len(candidates):
        return None
    best = max(candidates, key=overlap)
    return {'gt_id': int(best[1]), 'iou': overlap(best),
            'visibility': float(best[8]), 'gt_box': best[2:6].tolist()}


segments = {}
for tid in IDS:
    chosen = rows[(rows[:, 1] == tid) & (rows[:, 0] <= LIMIT)]
    py_chosen = py_rows[(py_rows[:, 1] == tid) & (py_rows[:, 0] <= LIMIT)]
    correspondence = [{'frame': int(r[0]), **gt_match(int(r[0]), r[2:6])}
                      for r in chosen]
    segments[str(tid)] = {'first_row': chosen[0].tolist(),
        'last_row': chosen[-1].tolist(), 'emitted_frames': len(chosen),
        'gt_best_matches': correspondence,
        'gt_best_match_counts_iou_at_least_0_5': dict(Counter(
            m['gt_id'] for m in correspondence if m['iou'] >= .5)),
        'python_same_frames_ids_boxes': bool(np.array_equal(chosen[:, :6], py_chosen[:, :6]))}

detections = read_cache(cache, int(info['seqlength']))
size = (int(info['imheight']), int(info['imwidth']))
tracker = BYTETracker(config(NAME), frame_rate=30)
transitions, assignments, replay_rows = [], [], []
previous = {}
frame = 0
context = {}
original_iou = matching.iou_distance
original_assignment = matching.linear_assignment


def observe_iou(a, b):
    matrix = original_iou(a, b)
    if frame in (31, 50):
        context.clear()
        context.update({'tracks': list(a), 'detections': list(b), 'raw': matrix.copy(),
            'predicted_boxes': [t.tlwh.copy() for t in a]})
    return matrix


def observe_assignment(cost, thresh):
    result = original_assignment(cost, thresh)
    if frame in (31, 50):
        selected = {int(i): int(j) for i, j in result[0]}
        for i, t in enumerate(context['tracks']):
            if t.track_id not in IDS:
                continue
            candidates = [{'index': j, 'score': float(d.score),
                'box': d.tlwh.tolist(), 'gt_match': gt_match(frame, d.tlwh),
                'inclusive_iou': float(1-context['raw'][i, j]),
                'assignment_cost': float(cost[i, j]), 'selected': selected.get(i) == j}
                for j, d in enumerate(context['detections'])]
            assignments.append({'source_frame': frame, 'track_id': t.track_id,
                'state_before_assignment': int(t.state), 'cost_limit': float(thresh),
                'predicted_box': context['predicted_boxes'][i].tolist(),
                'candidates': candidates})
    return result


matching.iou_distance = observe_iou
matching.linear_assignment = observe_assignment
try:
    for frame in range(1, LIMIT+1):
        if not len(detections[frame]):
            continue
        emitted = tracker.update(detections[frame], size, size)
        for t in emitted:
            x, y, w, h = t.tlwh
            if w*h > 100 and w/h <= 1.6:
                replay_rows.append([frame, t.track_id, *[round(v, 1) for v in (x, y, w, h)]])
        for tid in IDS:
            locations = {}
            for name in ('tracked_stracks', 'lost_stracks', 'removed_stracks'):
                for t in getattr(tracker, name):
                    if t.track_id == tid:
                        locations[name] = {'state': int(t.state), 'activated': bool(t.is_activated),
                            'start_update': int(t.start_frame), 'last_matched_update': int(t.end_frame)}
            signature = [(name, v['state'], v['activated']) for name, v in locations.items()]
            if signature != previous.get(tid, []):
                transitions.append({'source_frame': frame, 'tracker_update': tracker.frame_id,
                    'id': tid, 'collections': locations,
                    'in_tracker_output': any(t.track_id == tid for t in emitted)})
            previous[tid] = signature
finally:
    matching.iou_distance = original_iou
    matching.linear_assignment = original_assignment

replay_equal = bool(np.array_equal(np.asarray(replay_rows), rows[rows[:, 0] <= LIMIT, :6]))
assert replay_equal, 'Observation replay differs from the frozen C++ demo outputs.'
result = {'sequence': NAME, 'model': 'nano', 'source_fps': int(info['framerate']),
    'demo_frame_range': [1, LIMIT], 'frozen_config': vars(config(NAME)),
    'tracker_frame_rate_argument': 30, 'max_time_lost_updates': tracker.max_time_lost,
    'segments': segments, 'reference_state_transitions': transitions,
    'association_probes': assignments, 'replay_all_frames_ids_boxes_equal_cpp': replay_equal,
    'gt_correspondence_method': 'Highest continuous-box IoU to marked class-1 GT; no trajectory interpolation.',
    'state_enum': {'new': 0, 'tracked': 1, 'lost': 2, 'removed': 3},
    'input_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (cache, tracks, reference, gt_path)},
    'scope': 'Owner-reported failure inspection only; no tracking/detection settings changed.'}
(ROOT / 'results/phase-3-mobile-case-3-4-18.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'replay_equal': replay_equal,
    'probes': [{**a, 'candidates': [c for c in a['candidates'] if c['selected']
                                   or c['gt_match']['gt_id'] == 14]} for a in assignments],
    'gt14_frame_ranges': {tid: [m['frame'] for m in s['gt_best_matches']
                              if m['gt_id'] == 14 and m['iou'] >= .5]
                         for tid, s in segments.items()}}, indent=2))
