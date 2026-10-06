"""Run all predeclared continuity variants; never changes the Phase 3 baseline."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import time
import cv2
import numpy as np
from phase3_common import ROOT, config, read_cache, sequence_info
from yolox.tracker.basetrack import BaseTrack
from yolox.tracker.byte_tracker import BYTETracker, STrack
from continuity_motion import estimate_translation, sanity_checks, translate_pool
import motmetrics as mm

NAME = 'MOT17-05-FRCNN'
LIMIT = 168
directory = ROOT/'data/continuity-pilot'
directory.mkdir(parents=True, exist_ok=True)
sequence = ROOT/'data/MOT17/train'/NAME
cache = ROOT/'data/phase-3/dets/nano'/f'{NAME}.txt'
baseline_path = ROOT/'data/phase-3/tracks/end-to-end/nano'/f'{NAME}.txt'
gt_path = sequence/'gt/gt.txt'
plan_path = ROOT/'docs/CONTINUITY_PILOT.md'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
protected = {str(p.relative_to(ROOT)): sha(p) for p in (cache, baseline_path, gt_path, plan_path)}
cv2.setNumThreads(1)
cv2.setRNGSeed(0)
checks = sanity_checks()
info = sequence_info(sequence)
size = (int(info['imheight']), int(info['imwidth']))
detections = read_cache(cache, int(info['seqlength']))
baseline = np.loadtxt(baseline_path, delimiter=',')
raw_gt = np.loadtxt(gt_path, delimiter=',')


def track(cache_rows, buffer, shifts=None):
    args = config(NAME)
    args.track_buffer = buffer
    BaseTrack._count = 0  # Fresh-sequence IDs, as in separate reference processes.
    tracker = BYTETracker(args, frame_rate=30)
    original_predict = STrack.multi_predict
    frame = 0
    def compensated(pool):
        original_predict(pool)
        translate_pool(pool, shifts[frame])
    if shifts is not None:
        STrack.multi_predict = staticmethod(compensated)
    rows = []
    try:
        for frame in range(1, len(cache_rows)):
            if not len(cache_rows[frame]):
                continue
            for t in tracker.update(cache_rows[frame].copy(), size, size):
                x, y, w, h = t.tlwh
                if w*h <= 100 or w/h > 1.6:
                    continue
                rows.append([frame, t.track_id, *[round(v, 1) for v in (x, y, w, h)],
                             round(t.score, 2), -1, -1, -1])
    finally:
        STrack.multi_predict = staticmethod(original_predict)
    return np.asarray(rows)


synthetic = []
for name, identity, return_x in (('same-person-same-position', 2, 100),
                               ('different-person-same-position', 3, 100),
                               ('same-person-displaced', 2, 250)):
    inputs = [np.empty((0, 5), dtype=np.float32)]
    for frame in range(1, 41):
        ds = [[400, 80, 440, 180, .9]]
        if frame <= 3 or frame >= 25:
            x = 100 if frame <= 3 else return_x
            ds.append([x, 100, x+40, 200, .9])
        inputs.append(np.asarray(ds, dtype=np.float32))
    outcomes = {}
    for buffer in (14, 42):
        output = track(inputs, buffer)
        initial = output[(output[:, 0] == 3) & (output[:, 2] < 350)][0]
        returning = output[(output[:, 0] >= 25) & (output[:, 2] < 350)][0]
        same_id = initial[1] == returning[1]
        outcomes[str(buffer)] = {'initial_id': int(initial[1]), 'return_id': int(returning[1]),
            'first_return_output_frame': int(returning[0]), 'same_tracker_id': bool(same_id),
            'correct_identity_relation': bool(same_id == (identity == 2))}
    input_hash = hashlib.sha256(b''.join(ds.tobytes() for ds in inputs)).hexdigest()
    synthetic.append({'case': name, 'true_return_identity': identity,
        'absent_frames': [4, 24], 'input_sha256': input_hash, 'outcomes': outcomes})
assert synthetic[0]['input_sha256'] == synthetic[1]['input_sha256']

prefix = detections[:LIMIT+1]
first = track(prefix, 14)
equal = bool(np.array_equal(first[:, :6], baseline[baseline[:, 0] <= LIMIT, :6]))
assert equal, 'Baseline replay differs; do not run experimental variants.'
print('Baseline: all 168 frame/ID/box rows equal stored C++.', flush=True)

shifts = [np.zeros(2) for _ in range(LIMIT+1)]
motion_log, image_hashes = [], {}
previous = None
for frame in range(1, LIMIT+1):
    path = sequence/'img1'/f'{frame:06d}.jpg'
    image_hashes[str(path.relative_to(ROOT))] = sha(path)
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise RuntimeError(f'Cannot read {path}')
    current = cv2.resize(image, (image.shape[1]//2, image.shape[0]//2))
    if previous is not None:
        shifts[frame], row = estimate_translation(previous, current, prefix[frame-1], prefix[frame])
        motion_log.append({'source_frame': frame, **row})
    previous = current
(directory/'camera-motion.json').write_text(json.dumps(motion_log, indent=2)+'\n')

mm.lap.default_solver = 'lap'
ground_truth = mm.io.loadtxt(gt_path, fmt='mot15-2D', min_confidence=1)
ground_truth = ground_truth[ground_truth.index.get_level_values('FrameId') <= LIMIT]


def visible_person_history(rows):
    history = []
    for g in raw_gt[(raw_gt[:, 0] <= LIMIT) & (raw_gt[:, 1] == 14) & (raw_gt[:, 8] > 0)]:
        boxes = rows[rows[:, 0] == g[0]]
        best, best_iou = None, 0.
        for r in boxes:
            a, b = r[2:6], g[2:6]
            inter = np.maximum(0, np.minimum(a[:2]+a[2:], b[:2]+b[2:])-np.maximum(a[:2], b[:2])).prod()
            overlap = float(inter/(a[2]*a[3]+b[2]*b[3]-inter))
            if overlap > best_iou:
                best, best_iou = int(r[1]), overlap
        history.append({'frame': int(g[0]), 'visibility': float(g[8]),
            'id': best if best_iou >= .5 else None, 'best_iou': best_iou})
    recognized = [r['id'] for r in history if r['id'] is not None]
    chain = []
    for tid in recognized:
        if not chain or chain[-1] != tid:
            chain.append(tid)
    return {'visible_annotated_frames': len(history),
        'frames_with_matching_box': len(recognized), 'ordered_id_chain': chain,
        'identity_changes_across_recognized_frames': max(0, len(chain)-1),
        'per_frame': history}


variants = {}
for label, buffer, motion in (('baseline', 14, False), ('retention-42', 42, False),
                              ('motion-14', 14, True), ('motion-retention-42', 42, True)):
    begin = time.perf_counter()
    output = first if label == 'baseline' else track(prefix, buffer, shifts if motion else None)
    path = directory/f'{label}.txt'
    path.write_text(''.join(','.join(str(v) for v in row)+'\n' for row in output))
    predictions = mm.io.loadtxt(path, fmt='mot15-2D', min_confidence=-1)
    accumulator = mm.utils.compare_to_groundtruth(ground_truth, predictions, 'iou', distth=.5)
    scored = mm.metrics.create().compute(accumulator,
        metrics=['mota', 'idf1', 'num_switches', 'num_false_positives', 'num_misses', 'num_objects']).iloc[0]
    metrics = {k: float(v)*100 if k in ('mota', 'idf1') else int(v) for k, v in scored.items()}
    variants[label] = {'buffer_updates': buffer, 'motion_compensation': motion,
        'development_prefix_motmetrics': metrics, 'target_gt14': visible_person_history(output),
        'output': str(path.relative_to(ROOT)), 'output_sha256': sha(path),
        'seconds_tracking_and_scoring_observational': time.perf_counter()-begin}
    print(json.dumps({'variant': label, 'metrics': metrics,
        'gt14_id_chain': variants[label]['target_gt14']['ordered_id_chain']}), flush=True)

assert all(sha(ROOT/p) == digest for p, digest in protected.items()), 'Protected inputs changed.'
result = {'date': '2026-10-06', 'author': 'Codex / GPT-6 (exact runtime model ID not exposed)',
    'scope': 'Exposed, training-seen MOT17 development diagnostics only; not acceptance or held-out accuracy.',
    'sequence': NAME, 'frame_range': [1, LIMIT], 'source_fps': 14, 'model': 'nano',
    'baseline_replay_equal_cpp': equal, 'baseline_inputs_unchanged': True,
    'synthetic_retention_cases': synthetic, 'motion_sanity_checks': checks,
    'camera_motion': {'pairs': len(motion_log), 'accepted': sum(r['accepted'] for r in motion_log),
        'log': 'data/continuity-pilot/camera-motion.json', 'sha256': sha(directory/'camera-motion.json')},
    'variants': variants, 'input_sha256': protected, 'source_image_sha256': image_hashes,
    'versions': {'opencv': cv2.__version__, 'numpy': np.__version__,
        'motmetrics': importlib.metadata.version('motmetrics')},
    'limitations': ['One exposed 168-frame case; no generalization claim.',
        'Translation only; no appearance matching or motion-estimate uncertainty model.',
        'No modified MOT20 run; no C++ improvement port or performance benchmark.',
        'All four predeclared variants reported; no post-result tuning.']}
(ROOT/'results/continuity-pilot.json').write_text(json.dumps(result, indent=2)+'\n')
print('Saved results/continuity-pilot.json', flush=True)
