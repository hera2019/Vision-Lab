"""Bounded output/provenance audit; no tracking, timing or metric rerun."""
import ast
import csv
import hashlib
import json
import math
from datetime import datetime, timezone
from phase3_common import ROOT, sequence_info


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report = json.loads((ROOT/'results/phase-5-meanshift.json').read_text())
    assert report['original_baselines_exact'] and not report['baseline_replaced']
    assert report['protocol_sha256'] == sha(ROOT/report['protocol'])
    for source, digest in report['source_sha256'].items():
        assert sha(ROOT/source) == digest, source
    counts = {}
    for name, record in report['sequences'].items():
        sequence = ROOT/'data/MOT20/train'/name
        folder = ROOT/'data/phase-5-meanshift/tracks'
        meta = record['metadata']
        info = sequence_info(sequence)
        assert meta['processed_frames'] == int(info['seqlength'])
        assert meta['gt_sha256'] == sha(sequence/'gt/gt.txt')
        assert meta['script_sha256'] == sha(ROOT/'python/meanshift_baseline.py')
        assert meta['cpu_max'] == '100000 100000' and meta['opencv_threads'] == 1
        assert not meta['invalid_seeds']
        seeds_path = folder/f'{name}.seeds.json'
        assert record['seeds_sha256'] == sha(seeds_path)
        seeds = json.loads(seeds_path.read_text())
        first = {}
        with (sequence/'gt/gt.txt').open() as stream:
            for fields in csv.reader(stream):
                row = [float(x) for x in fields]
                if row[6] == 1 and row[7] == 1:
                    identity = int(row[1])
                    if identity not in first or row[0] < first[identity][0]:
                        first[identity] = row
        expected = sorted(first.values(), key=lambda row: (row[0], row[1]))
        assert len(expected) == len(seeds) == meta['initialized_tracks']
        ratio = min(608/int(info['imheight']), 1088/int(info['imwidth']))
        content_w, content_h = int(int(info['imwidth'])*ratio), int(int(info['imheight'])*ratio)
        for index, (row, seed) in enumerate(zip(expected, seeds), start=1):
            assert seed['tracker_id'] == index and seed['gt_id'] == int(row[1])
            assert seed['frame'] == int(row[0]) and seed['gt_xywh'] == row[2:6]
            x, y, w, h = [value*ratio for value in row[2:6]]
            left, top = max(0, math.floor(x)), max(0, math.floor(y))
            right, bottom = min(content_w, math.ceil(x+w)), min(content_h, math.ceil(y+h))
            assert seed['input_xywh'] == [left, top, right-left, bottom-top]
        assert sum(s['empty_histogram'] for s in seeds) == meta['empty_histograms']
        seed_by_id = {s['tracker_id']: s for s in seeds}
        previous, total = (0, 0), 0
        track_path = folder/f'{name}.txt'
        assert sha(track_path) == meta['tracks_sha256']
        assert report['quality']['meanshift']['sha256'][name] == meta['tracks_sha256']
        with track_path.open() as stream:
            for fields in csv.reader(stream):
                assert len(fields) == 10
                values = [float(x) for x in fields]
                assert all(math.isfinite(x) for x in values)
                frame, identity = int(values[0]), int(values[1])
                assert values[:2] == [frame, identity]
                assert (frame, identity) > previous and 1 <= frame <= meta['processed_frames']
                seed = seed_by_id[identity]
                assert frame >= seed['frame'] and values[4] > 0 and values[5] > 0
                assert values[4:6] == [float(f'{v/ratio:.1f}') for v in seed['input_xywh'][2:]]
                assert values[6:] == [1, -1, -1, -1]
                previous, total = (frame, identity), total+1
        assert total == meta['emitted_rows_including_warmup']
        timing_path = folder/f'{name}.timing.csv'
        assert sha(timing_path) == meta['timing_sha256']
        with timing_path.open() as stream:
            timings = list(csv.DictReader(stream))
        assert [int(r['frame']) for r in timings] == list(range(1, meta['processed_frames']+1))
        assert sum(int(r['kept_tracks']) for r in timings) == total
        for row in timings:
            assert int(row['active_tracks']) == sum(s['frame'] <= int(row['frame']) for s in seeds)
            assert math.isclose(float(row['end_to_end_ms']), sum(float(row[k]) for k in ('decode_ms','preprocess_ms','tracking_ms')), abs_tol=1e-8)
        counts[name] = {'frames': meta['processed_frames'], 'seeds': len(seeds), 'rows': total}
    for source in ('meanshift_baseline.py','meanshift_trackeval.py','report_meanshift.py','verify_meanshift.py'):
        ast.parse((ROOT/'python'/source).read_text(), filename=source)
    result = {'author': report['author'], 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
              'status': 'pass', 'scope': 'Executor output/provenance audit; no new inference, benchmark or metric computation; not independent review.',
              'counts': counts, 'frames': sum(c['frames'] for c in counts.values()),
              'rows': sum(c['rows'] for c in counts.values()), 'source_hashes_match': True,
              'GT_first_appearance_schedule_and_boxes_match': True,
              'track_numeric_shape_order_birth_size_and_hash_checks': True,
              'full_frame_timing_and_active_target_counts_match': True,
              'python_syntax': 'pass', 'audit_source_sha256': sha(ROOT/'python/verify_meanshift.py')}
    assert result['frames'] == 8931
    (ROOT/'results/phase-5-meanshift/verification.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': result['status'], 'frames': result['frames'], 'rows': result['rows']}))


if __name__ == '__main__':
    main()
