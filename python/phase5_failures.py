"""Read-only CLEAR audit and illustrative failure crops from accepted FP32 output."""
import gc
import hashlib
import json
import sys
from pathlib import Path
import cv2
import numpy as np
from scipy.optimize import linear_sum_assignment
from phase3_common import ROOT, read_cache, sequence_info

sys.path.insert(0, str(ROOT/'external/TrackEval'))
import trackeval

OUT = ROOT/'data/phase-5/crops'
OUT.mkdir(parents=True, exist_ok=True)
cv2.setNumThreads(1)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
names = sorted(p.name for p in (ROOT/'data/MOT20/train').glob('MOT20-*'))
dataset = trackeval.datasets.MotChallenge2DBox({
    'GT_FOLDER': str(ROOT/'data/MOT20/train'),
    'TRACKERS_FOLDER': str(ROOT/'data/phase-3/eval-input/MOT20'),
    'TRACKERS_TO_EVAL': ['cpp-nano'], 'BENCHMARK': 'MOT20',
    'SPLIT_TO_EVAL': 'train', 'SKIP_SPLIT_FOL': True,
    'SEQMAP_FILE': str(ROOT/'data/phase-3/MOT20-seqmap.txt'), 'PRINT_CONFIG': False})
baseline = json.loads((ROOT/'results/phase-3/evaluation-final.json').read_text())['results']['MOT20']['end-to-end']['nano']
audits, cases = {}, {}


def ious(box, others):
    if not len(others):
        return np.empty(0)
    a, b = np.asarray(box), np.asarray(others)
    inter = np.maximum(0, np.minimum(a[:2]+a[2:], b[:, :2]+b[:, 2:])-
                       np.maximum(a[:2], b[:, :2])).prod(axis=1)
    return inter/(a[2]*a[3]+b[:, 2]*b[:, 3]-inter)


def audit(name):
    seq = ROOT/'data/MOT20/train'/name
    track_path = ROOT/'data/phase-3/tracks/end-to-end/nano'/f'{name}.txt'
    eval_path = ROOT/'data/phase-3/eval-input/MOT20/cpp-nano/data'/f'{name}.txt'
    assert sha(track_path) == baseline['sha256'][name] == sha(eval_path)
    raw = dataset.get_raw_seq_data('cpp-nano', name)
    data = dataset.get_preprocessed_seq_data(raw, 'pedestrian')
    del raw
    gt = np.loadtxt(seq/'gt/gt.txt', delimiter=',', ndmin=2)
    gt = gt[(gt[:, 6] != 0) & (gt[:, 7] == 1)]
    original_gt_ids = np.unique(gt[:, 1]).astype(int)
    assert len(original_gt_ids) == data['num_gt_ids']
    predicted = np.loadtxt(track_path, delimiter=',', ndmin=2)
    # TrackEval remaps predicted IDs after removing ignored predictions.
    # Recover original IDs by each retained box, not by assuming all IDs survive.
    pred_by_frame = {f: predicted[predicted[:, 0] == f] for f in range(1, data['num_timesteps']+1)}
    id_map = {}
    for t, ids in enumerate(data['tracker_ids']):
        rows = pred_by_frame[t+1]
        for remapped, box in zip(ids, data['tracker_dets'][t]):
            found = rows[np.all(rows[:, 2:6] == box, axis=1)]
            assert len(found) == 1, 'Original prediction ID mapping is ambiguous.'
            original = int(found[0, 1])
            assert id_map.get(int(remapped), original) == original
            id_map[int(remapped)] = original
    last_id = np.full(data['num_gt_ids'], np.nan)
    previous = last_id.copy()
    matches = []
    totals = {'CLR_TP': 0, 'CLR_FN': 0, 'CLR_FP': 0, 'IDSW': 0}
    epsilon = np.finfo(float).eps
    for t, (gids, tids) in enumerate(zip(data['gt_ids'], data['tracker_ids'])):
        associated = {}
        if not len(gids):
            totals['CLR_FP'] += len(tids)
        elif not len(tids):
            totals['CLR_FN'] += len(gids)
        else:
            sim = data['similarity_scores'][t]
            score = 1000*(tids[None, :] == previous[gids[:, None]])+sim
            score[sim < 0.5-epsilon] = 0
            rows, cols = linear_sum_assignment(-score)
            keep = score[rows, cols] > epsilon
            rows, cols = rows[keep], cols[keep]
            mg, mt = gids[rows], tids[cols]
            totals['IDSW'] += int(np.sum(~np.isnan(last_id[mg]) & (last_id[mg] != mt)))
            totals['CLR_TP'] += len(rows)
            totals['CLR_FN'] += len(gids)-len(rows)
            totals['CLR_FP'] += len(tids)-len(rows)
            last_id[mg] = mt
            previous[:] = np.nan
            previous[mg] = mt
            associated = {int(original_gt_ids[g]): {'track_id': id_map[int(tr)],
                'iou': float(sim[r, c]), 'track_box': data['tracker_dets'][t][c].tolist()}
                for r, c, g, tr in zip(rows, cols, mg, mt)}
        matches.append(associated)
    official = trackeval.metrics.CLEAR({'PRINT_CONFIG': False}).eval_sequence(data)
    assert all(totals[k] == int(official[k]) for k in totals), (name, totals, official)
    assert totals['IDSW'] == baseline['scores']['TrackEval'][name]['IDSW']
    audits[name] = {'counts': totals, 'matches_upstream_CLEAR': True,
        'source_sha256': {str(p.relative_to(ROOT)): sha(p) for p in
            (track_path, seq/'gt/gt.txt', ROOT/'data/phase-3/dets/nano'/f'{name}.txt')},
        'processed_frames': len(matches)}
    del data
    gt_by_frame = {f: {int(r[1]): r for r in gt[gt[:, 0] == f]}
                   for f in range(1, len(matches)+1)}
    detections = read_cache(ROOT/'data/phase-3/dets/nano'/f'{name}.txt', len(matches))
    return seq, sequence_info(seq), gt_by_frame, matches, detections


def best_detection(row, detections):
    if not len(detections):
        return {'iou': 0.0, 'score': None, 'box': None}
    boxes = detections[:, :4].astype(float).copy()
    boxes[:, 2:] -= boxes[:, :2]
    values = ious(row[2:6], boxes)
    best = int(np.argmax(values))
    return {'iou': float(values[best]), 'score': float(detections[best, 4]),
            'box': boxes[best].tolist()}


def record(category, name, gid, frames, pictures, gt, matches, detections, info):
    scale = min(608/int(info['imheight']), 1088/int(info['imwidth']))
    observations = []
    for f in frames:
        row = gt[f][gid]
        neighbors = [int(other) for other, r in gt[f].items() if other != gid and ious(row[2:6], r[None, 2:6])[0] > 0]
        observations.append({'frame': f, 'gt_box': row[2:6].tolist(), 'visibility': float(row[8]),
            'native_input_height_px': float(row[5]*scale),
            'touches_image_border': bool(row[2] <= 1 or row[3] <= 1 or
                row[2]+row[4] >= int(info['imwidth'])-1 or row[3]+row[5] >= int(info['imheight'])-1),
            'association': matches[f-1].get(gid), 'best_detection': best_detection(row, detections[f]),
            'overlapping_gt_ids': neighbors})
    return {'category': category, 'sequence': name, 'gt_id': gid, 'model': 'nano FP32',
        'frame_range': [frames[0], frames[-1]], 'crop_frames': pictures,
        'source_fps': int(info['framerate']), 'observations': observations}


for name in names:
    seq, info, gt, matches, detections = audit(name)
    if 'identity-switch' not in cases:
        for f in range(6, len(matches)-3):
            for gid in sorted(gt[f]):
                rows = [gt[t].get(gid) for t in range(f-5, f+5)]
                assoc = [matches[t-1].get(gid) for t in range(f-5, f+5)]
                if any(r is None or r[8] < 0.6 for r in rows) or any(a is None for a in assoc):
                    continue
                ids = [a['track_id'] for a in assoc]
                if len(set(ids[:5])) != 1 or len(set(ids[5:])) != 1 or ids[4] == ids[5]:
                    continue
                neighbors = [r for other, r in gt[f].items() if other != gid]
                if not neighbors or not (ious(gt[f][gid][2:6], np.array(neighbors)[:, 2:6]) > 0).any():
                    continue
                cases['identity-switch'] = record('identity-switch', name, gid,
                    list(range(f-5, f+5)), [f-1, f, f+4], gt, matches, detections, info)
                break
            if 'identity-switch' in cases:
                break
    if 'small-target-miss' not in cases:
        scale = min(608/int(info['imheight']), 1088/int(info['imwidth']))
        for f in range(1, len(matches)-6):
            for gid in sorted(gt[f]):
                rows = [gt[t].get(gid) for t in range(f, f+8)]
                if any(r is None or r[8] < 0.75 or r[5]*scale > 40 for r in rows):
                    continue
                if any(gid in matches[t-1] for t in range(f, f+8)):
                    continue
                if sum(best_detection(gt[t][gid], detections[t])['iou'] < 0.5 for t in range(f, f+8)) < 5:
                    continue
                cases['small-target-miss'] = record('small-target-miss', name, gid,
                    list(range(f, f+8)), [f, f+3, f+7], gt, matches, detections, info)
                break
            if 'small-target-miss' in cases:
                break
    if name == 'MOT20-03':
        gid = 169
        assert matches[140][gid]['track_id'] == 75 and matches[179][gid]['track_id'] == 107
        cases['occlusion-fragmentation'] = record('occlusion-fragmentation', name, gid,
            list(range(130, 186)), [130, 155, 180], gt, matches, detections, info)
        cases['occlusion-fragmentation']['prior_state_diagnosis'] = 'results/phase-3-occlusion-case-75-107.json'
    print(json.dumps({'sequence': name, 'audit': audits[name]['counts'],
                      'categories_found': list(cases)}), flush=True)
    del gt, matches, detections
    gc.collect()
    if len(cases) == 3:
        break

assert len(cases) == 3, f'Predeclared selectors found only {list(cases)}; report before changing selectors.'


def render(case):
    selected = [r for r in case['observations'] if r['frame'] in case['crop_frames']]
    boxes = np.array([r['gt_box'] for r in case['observations']])
    left, top = np.floor(boxes[:, :2].min(axis=0)-[70, 40]).astype(int)
    right, bottom = np.ceil((boxes[:, :2]+boxes[:, 2:]).max(axis=0)+[70, 40]).astype(int)
    seq = ROOT/'data/MOT20/train'/case['sequence']
    info = sequence_info(seq)
    left, top = max(0, left), max(0, top)
    right, bottom = min(int(info['imwidth']), right), min(int(info['imheight']), bottom)
    factor = min(2.0, 480/(right-left), 560/(bottom-top))
    width, height = round((right-left)*factor), round((bottom-top)*factor)
    panels, source_hashes = [], {}
    for observation in selected:
        path = seq/'img1'/f'{observation["frame"]:06d}.jpg'
        source_hashes[str(path.relative_to(ROOT))] = sha(path)
        image = cv2.imread(str(path))
        assert image is not None
        crop = cv2.resize(image[top:bottom, left:right], (width, height))
        panel = np.full((height+90, max(width, 320), 3), 24, dtype=np.uint8)
        panel[85:85+height, :width] = crop
        association = observation['association']
        label = f'ID {association["track_id"]}' if association else 'no matched track'
        for y, text in [(20, case['sequence']+' / frame '+str(observation['frame'])),
                        (42, f'GT {case["gt_id"]}, visibility {observation["visibility"]:.2f}'),
                        (64, label+' | yellow GT / cyan prediction')]:
            cv2.putText(panel, text, (5, y), cv2.FONT_HERSHEY_SIMPLEX, .43, (240,240,240), 1, cv2.LINE_AA)
        for box, color in [(observation['gt_box'], (0,255,255))]+([(association['track_box'], (255,255,0))] if association else []):
            x, y, w, h = box
            a = (round((x-left)*factor), round((y-top)*factor)+85)
            b = (round((x+w-left)*factor), round((y+h-top)*factor)+85)
            cv2.rectangle(panel, a, b, color, 2)
        panels.append(panel)
    image = np.hstack(panels)
    destination = OUT/(case['category']+'.png')
    assert cv2.imwrite(str(destination), image)
    decoded = cv2.imread(str(destination))
    assert decoded.shape == image.shape and np.array_equal(decoded, image)
    case['crop'] = {'path': str(destination.relative_to(ROOT)), 'sha256': sha(destination),
        'source_sha256': source_hashes, 'source_crop_xyxy': [int(v) for v in (left, top, right, bottom)],
        'display_scale': factor, 'output_size': [image.shape[1], image.shape[0]],
        'license': 'CC BY-NC-SA 3.0', 'attribution': 'MOTChallenge authors, https://motchallenge.net/'}


for case in cases.values():
    render(case)
result = {'status': 'three-failure-categories-documented', 'author': 'Codex / GPT-6 (exact runtime model ID not exposed)',
    'protocol': 'docs/PHASE5_EXECUTION.md', 'baseline': 'accepted nano FP32, unchanged A1 settings',
    'matching': 'TrackEval pedestrian preprocessing and CLEAR IoU 0.5 continuity-aware correspondence; counts cross-checked with upstream.',
    'selection': 'Deterministic illustrative examples, not prevalence or new overall accuracy estimates.',
    'cases': cases, 'audited_sequences': audits,
    'clear_source_sha256': sha(ROOT/'external/TrackEval/trackeval/metrics/clear.py'),
    'limitations': ['Only selected nano FP32 examples; no random sample or exhaustive taxonomy.',
        'GT visibility is annotation evidence, not direct measurement of the exact occluding object.',
        'Small input height does not prove distance or the cause of every miss.',
        'Correspondence switches show failure against annotation, not a proven unique association cause.',
        'Mean-shift optional bonus and Phase 6 fresh-clone reproduction not performed here.']}
(ROOT/'results/phase-5-failures.json').write_text(json.dumps(result, indent=2)+'\n')
lines = ['# Phase 5 — failure cases from held-out MOT20', '', 'Author: '+result['author']+'.', '',
    '**Status: three categories documented; existing FP32 baseline unchanged.** Independent review pending.', '',
    result['matching'], '', result['selection'], '',
    'Each image uses yellow for target GT and cyan for its associated prediction. A missing cyan box means no CLEAR match, not necessarily no prediction anywhere nearby. The images are original source crops with overlays, not generated scene content.']
explanations = {
    'occlusion-fragmentation': 'Owner-reported pillar case: GT 169 is emitted as ID 75 through frame 141 and ID 107 from frame 180. Prior reference replay confirms the old ID expires after the 30-update retention limit. Long occlusion and a new ID are established in this case; increasing retention alone can introduce wrong-person recovery.',
    'identity-switch': 'The same annotated person corresponds to one predicted ID for five consecutive frames, then a different ID for five. Another annotated person overlaps at the switch. This proves an identity correspondence change in a crowded neighborhood; overlap alone does not identify the precise internal association cause.',
    'small-target-miss': 'The annotated pedestrian has visibility >=0.75, <=40-pixel annotated height at native detector resize, and no emitted-track match for all eight frames. At least five frames also lack an overlapping cached detection at IoU >=0.5. File inspection shows only a head entering at the bottom image border: small annotated extent and boundary truncation co-occur. The high visibility annotation does not mean the whole body is in the image. Nearby low-confidence detector boxes exist, but they do not overlap the GT sufficiently. This places part of the failure before association; it is not evidence of distant-person failure or a unique small-size cause.'}
for key in ('occlusion-fragmentation', 'identity-switch', 'small-target-miss'):
    case = cases[key]
    lines += ['', '## '+key, '', f'{case["sequence"]}, GT {case["gt_id"]}, frames {case["frame_range"][0]}–{case["frame_range"][1]}; crop frames '+', '.join(map(str, case['crop_frames']))+'.', '',
              explanations[key], '', f'![{key}](../{case["crop"]["path"]})', '',
              '| Frame | Visibility | Native input height px | Matched ID | Match IoU | Best cached detection IoU | Detection score |',
              '|---|---:|---:|---|---:|---:|---:|']
    for row in case['observations']:
        if row['frame'] not in case['crop_frames']:
            continue
        match, det = row['association'], row['best_detection']
        tid = match['track_id'] if match else 'none'
        overlap = f'{match["iou"]:.3f}' if match else '—'
        confidence = f'{det["score"]:.3f}' if det['score'] is not None else '—'
        lines.append(f'| {row["frame"]} | {row["visibility"]:.2f} | {row["native_input_height_px"]:.1f} | {tid} | {overlap} | {det["iou"]:.3f} | {confidence} |')
lines += ['', '## Evidence boundaries', '', 'Full selected intervals, GT/prediction/detection boxes, source hashes, exact crop rectangles and output hashes are in the JSON. CLEAR count audits agree with upstream on every scanned sequence. Earlier MOTA/IDF1/HOTA results are not recalculated or replaced. These examples do not estimate the relative frequency of the three categories.', '',
          'No new models, downloads, parameter changes or detector inference. Crops retain MOTChallenge attribution and CC BY-NC-SA 3.0 research-use terms. The mean-shift bonus is deferred. Phase 6 reproduction remains next.', '',
          'Reproduce with existing baseline data/evaluators/image: `bash scripts/phase5_failures.sh`.']
(ROOT/'results/phase-5-failures.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({'status': result['status'], 'cases': {k: {n: v[n] for n in ('sequence','gt_id','frame_range','crop_frames')} for k,v in cases.items()}}), flush=True)
