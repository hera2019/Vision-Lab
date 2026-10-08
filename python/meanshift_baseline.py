"""Oracle-born OpenCV mean-shift; fixed protocol docs/MEANSHIFT_EXECUTION.md."""
import argparse
import csv
import hashlib
import json
import inspect
import math
import time
from datetime import datetime, timezone
from pathlib import Path
import cv2
import numpy as np
from phase3_common import ROOT, sequence_info

BASE = ROOT / 'data/phase-5-meanshift'
RAW = ROOT / 'results/phase-5-meanshift'
SIZE = (608, 1088)
CRITERIA = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
AUTHOR = 'Codex / GPT-6 (exact runtime model ID not exposed)'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def context():
    return {'author': AUTHOR, 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
            'protocol': 'docs/MEANSHIFT_EXECUTION.md',
            'protocol_sha256': sha(ROOT/'docs/MEANSHIFT_EXECUTION.md'),
            'script_sha256': sha(Path(__file__)), 'opencv': cv2.__version__,
            'opencv_threads': cv2.getNumThreads(), 'cpu_max': Path('/sys/fs/cgroup/cpu.max').read_text().strip()}


def prepare(image):
    h, w = image.shape[:2]
    ratio = min(SIZE[0]/h, SIZE[1]/w)
    resized = cv2.resize(image, (int(w*ratio), int(h*ratio)), interpolation=cv2.INTER_LINEAR)
    padded = np.full((*SIZE, 3), 114, dtype=np.uint8)
    padded[:resized.shape[0], :resized.shape[1]] = resized
    return padded, ratio, (resized.shape[1], resized.shape[0])


def seed_rows(gt):
    valid = gt[(gt[:, 6] == 1) & (gt[:, 7] == 1)]
    valid = valid[np.lexsort((valid[:, 1], valid[:, 0]))]
    seen, rows = set(), []
    for row in valid:
        gid = int(row[1])
        if gid not in seen:
            seen.add(gid)
            rows.append(row)
    return rows


def clip_seed(row, ratio, content_size):
    width, height = content_size
    x, y, w, h = row[2:6]*ratio
    x1, y1 = max(0, int(math.floor(x))), max(0, int(math.floor(y)))
    x2, y2 = min(width, int(math.ceil(x+w))), min(height, int(math.ceil(y+h)))
    if x2 <= x1 or y2 <= y1:
        return None
    return (x1, y1, x2-x1, y2-y1)


def histogram(hsv, window):
    x, y, w, h = window
    roi = hsv[y:y+h, x:x+w]
    mask = cv2.inRange(roi, (0,60,32), (180,255,255))
    hist = cv2.calcHist([roi], [0], mask, [180], [0,180])
    cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
    return hist


def core_sha():
    functions=(prepare,seed_rows,clip_seed,histogram,local_mean_shift)
    return hashlib.sha256((''.join(inspect.getsource(f) for f in functions)+str(SIZE)+str(CRITERIA)).encode()).hexdigest()


def local_mean_shift(hsv, hist, window, scratch):
    """Exact lazy backprojection: outside pixels do not affect one iteration."""
    for _ in range(10):
        x, y, w, h = window
        scratch[y:y+h, x:x+w] = cv2.calcBackProject([hsv[y:y+h, x:x+w]], [0], hist, [0,180], 1)
        iterations, updated = cv2.meanShift(scratch, window, (cv2.TERM_CRITERIA_COUNT,1,1))
        scratch[y:y+h, x:x+w] = 0
        if updated == window or iterations == 0:
            return updated
        window = updated
    return window


def preflight():
    from vl_common import preproc, RGB_MEAN, RGB_STD
    rng = np.random.default_rng(20261008)
    checks = []
    for i in range(30):
        hsv = rng.integers(0,256,(64,96,3),dtype=np.uint8)
        hsv[:,:,0] %= 180
        windows = [(0,0,15,20),(81,44,15,20),(20,10,24,30),(1,1,1,1)]
        for window in windows:
            hist = histogram(hsv,window) if i else np.zeros((180,1),np.float32)
            projection = cv2.calcBackProject([hsv],[0],hist,[0,180],1)
            expected = cv2.meanShift(projection,window,CRITERIA)[1]
            actual = local_mean_shift(hsv,hist,window,np.zeros(hsv.shape[:2],np.uint8))
            assert actual == expected, (actual,expected)
            checks.append('synthetic')
    images, max_preproc_error = [], 0.0
    for name in ('MOT17-02-FRCNN','MOT17-05-FRCNN'):
        seq = ROOT/'data/MOT17/train'/name
        gt = np.loadtxt(seq/'gt/gt.txt', delimiter=',', ndmin=2)
        first = seed_rows(gt)
        # Keeping only birth annotations cannot change the seed schedule.
        assert [r.tolist() for r in seed_rows(np.asarray(first))] == [r.tolist() for r in first]
        for frame in (1,2,51,100):
            path = seq/'img1'/f'{frame:06d}.jpg'
            image = cv2.imread(str(path))
            padded, ratio, content = prepare(image)
            tensor, old_ratio = preproc(image,SIZE)
            rgb = padded[:,:,::-1].astype(np.float64)/255
            calculated = ((rgb-np.asarray(RGB_MEAN))/np.asarray(RGB_STD)).transpose(2,0,1).astype(np.float32)
            error = float(np.max(np.abs(calculated-tensor)))
            assert ratio == old_ratio and error <= 1e-6
            max_preproc_error = max(max_preproc_error,error)
            hsv = cv2.cvtColor(padded,cv2.COLOR_BGR2HSV)
            boxes = gt[(gt[:,0] == frame) & (gt[:,6] == 1) & (gt[:,7] == 1)][:5]
            for row in boxes:
                window = clip_seed(row,ratio,content)
                if window is None:
                    continue
                hist = histogram(hsv,window)
                projection = cv2.calcBackProject([hsv],[0],hist,[0,180],1)
                expected = cv2.meanShift(projection,window,CRITERIA)[1]
                actual = local_mean_shift(hsv,hist,window,np.zeros(SIZE,np.uint8))
                assert actual == expected, (path,actual,expected)
                checks.append('MOT17')
            images.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path)})
    result = {**context(),'status':'pass','synthetic_windows':checks.count('synthetic'),
              'tracking_core_sha256':core_sha(),
              'MOT17_windows':checks.count('MOT17'),'images':images,
              'preprocess_max_abs_error':max_preproc_error,
              'births_unchanged_without_later_annotations':True,
              'full_backprojection_final_windows_identical':True}
    write_json(RAW/'preflight.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('images','script_sha256')}),flush=True)


def track(sequence, repeat=None):
    check=json.loads((RAW/'preflight.json').read_text())
    assert check['status']=='pass' and check['tracking_core_sha256']==core_sha()
    assert check['protocol_sha256']==sha(ROOT/'docs/MEANSHIFT_EXECUTION.md')
    info = sequence_info(sequence)
    expected = int(info['seqlength'])
    benchmark = repeat is not None
    limit = min(expected,150) if benchmark else expected
    name = sequence.name
    stem = RAW/'benchmark'/f'r{repeat}' if benchmark else BASE/'tracks'/name
    destination = None if benchmark else stem.with_suffix('.txt')
    timing = stem.with_suffix('.csv') if benchmark else stem.with_suffix('.timing.csv')
    assert not timing.exists() and (destination is None or not destination.exists()), 'Refuse overwrite.'
    timing.parent.mkdir(parents=True,exist_ok=True)
    gt_path = sequence/'gt/gt.txt'
    gt = np.loadtxt(gt_path,delimiter=',',ndmin=2)
    births = {}
    for row in seed_rows(gt):
        births.setdefault(int(row[0]),[]).append(row)
    # Never consult later annotation boxes, visibility or disappearance in tracking.
    del gt
    active, seeds, invalid, zero_hist = [], [], [], 0
    frame_manifest = hashlib.sha256()
    rows_emitted = 0
    scratch = np.zeros(SIZE,np.uint8)
    track_file = destination.open('w') if destination else None
    started = time.perf_counter()
    with timing.open('w') as stream:
        writer = csv.DictWriter(stream,fieldnames=['frame','decode_ms','preprocess_ms','tracking_ms','end_to_end_ms','active_tracks','kept_tracks'])
        writer.writeheader()
        for frame in range(1,limit+1):
            path = sequence/info['imdir']/f'{frame:06d}{info["imext"]}'
            # Hash outside measured stages; the manifest covers every consumed image.
            image_digest = sha(path)
            frame_manifest.update(f'{frame}:{image_digest}\n'.encode())
            begin = time.perf_counter()
            image = cv2.imread(str(path))
            decoded = time.perf_counter()
            assert image is not None and image.shape[:2] == (int(info['imheight']),int(info['imwidth']))
            padded, ratio, content = prepare(image)
            hsv = cv2.cvtColor(padded,cv2.COLOR_BGR2HSV)
            prepared = time.perf_counter()
            for item in active:
                item['window'] = local_mean_shift(hsv,item['hist'],item['window'],scratch)
            for row in births.get(frame,[]):
                window = clip_seed(row,ratio,content)
                if window is None:
                    invalid.append({'frame':frame,'gt_id':int(row[1])})
                    continue
                hist = histogram(hsv,window)
                tracker_id = len(active)+1
                active.append({'id':tracker_id,'window':window,'hist':hist})
                is_zero = bool(not np.any(hist))
                zero_hist += int(is_zero)
                seeds.append({'frame':frame,'gt_id':int(row[1]),'tracker_id':tracker_id,
                    'gt_xywh':row[2:6].tolist(),'input_xywh':list(window),'empty_histogram':is_zero,
                    'image_sha256':image_digest})
            outputs=[]
            for item in active:
                x,y,w,h = np.asarray(item['window'],dtype=float)/ratio
                if w*h > 100 and w/h <= 1.6:
                    outputs.append(f'{frame},{item["id"]},{x:.1f},{y:.1f},{w:.1f},{h:.1f},1.00,-1,-1,-1\n')
            ended = time.perf_counter()
            rows_emitted += len(outputs)
            if track_file:
                track_file.writelines(outputs)
            if not benchmark or frame > 50:
                writer.writerow({'frame':frame,'decode_ms':(decoded-begin)*1000,
                    'preprocess_ms':(prepared-decoded)*1000,'tracking_ms':(ended-prepared)*1000,
                    'end_to_end_ms':(ended-begin)*1000,'active_tracks':len(active),'kept_tracks':len(outputs)})
            if frame % 500 == 0:
                print(f'{name}: frame {frame}/{limit}, active={len(active)}',flush=True)
    if track_file:
        track_file.close()
    memory = next(line.split()[1] for line in Path('/proc/self/status').read_text().splitlines() if line.startswith('VmHWM:'))
    result = {**context(),'sequence':name,'processed_frames':limit,'measured_frames':100 if benchmark else limit,
        'warmup_frames':50 if benchmark else 0,'benchmark_repeat':repeat,
        'gt_sha256':sha(gt_path),'seqinfo_sha256':sha(sequence/'seqinfo.ini'),
        'ordered_image_manifest_sha256':frame_manifest.hexdigest(),
        'initialized_tracks':len(active),'empty_histograms':zero_hist,'invalid_seeds':invalid,
        'emitted_rows_including_warmup':rows_emitted,'peak_rss_kib':int(memory),
        'seconds_driver':time.perf_counter()-started,'timing_sha256':sha(timing),
        'tracks_sha256':sha(destination) if destination else None,
        'seed_source':'first valid pedestrian GT appearance only; no subsequent GT updates or retirement'}
    write_json(stem.with_suffix('.json'),result)
    if not benchmark:
        write_json(stem.with_suffix('.seeds.json'),seeds)
    print(f'{name}: complete, tracks={len(active)}, emitted={rows_emitted}',flush=True)


def evaluate():
    import shutil
    import sys
    from evaluate_tracking import sequences,motmetrics_score
    sys.path.insert(0,str(ROOT/'external/TrackEval'))
    import trackeval
    original = json.loads((ROOT/'results/phase-3/evaluation-final.json').read_text())['results']['MOT20']['end-to-end']
    labels = {'meanshift':BASE/'tracks',
              'nano':ROOT/'data/phase-3/tracks/end-to-end/nano',
              'tiny':ROOT/'data/phase-3/tracks/end-to-end/tiny'}
    hashes = {}
    for label,folder in labels.items():
        target = BASE/'eval-input'/label/'data'
        target.mkdir(parents=True,exist_ok=True)
        hashes[label] = {}
        for seq in sequences('MOT20'):
            source = folder/(seq.name+'.txt')
            digest = sha(source)
            if label != 'meanshift':
                assert digest == original[label]['sha256'][seq.name], 'Baseline changed.'
            else:
                meta=json.loads((BASE/'tracks'/f'{seq.name}.json').read_text())
                rows=list(csv.DictReader((BASE/'tracks'/f'{seq.name}.timing.csv').open()))
                count=int(sequence_info(seq)['seqlength'])
                assert meta['processed_frames']==count and meta['tracks_sha256']==digest
                assert [int(row['frame']) for row in rows]==list(range(1,count+1))
            hashes[label][seq.name]=digest
            shutil.copyfile(source,target/source.name)
    seqmap=BASE/'MOT20-seqmap.txt'
    seqmap.write_text('name\n'+'\n'.join(s.name for s in sequences('MOT20'))+'\n')
    config={'GT_FOLDER':str(ROOT/'data/MOT20/train'),'TRACKERS_FOLDER':str(BASE/'eval-input'),
            'OUTPUT_FOLDER':str(BASE/'eval-output'),'TRACKERS_TO_EVAL':list(labels),
            'BENCHMARK':'MOT20','SPLIT_TO_EVAL':'train','SKIP_SPLIT_FOL':True,
            'SEQMAP_FILE':str(seqmap),'PRINT_CONFIG':False}
    evaluator=trackeval.Evaluator({'USE_PARALLEL':False,'PRINT_CONFIG':False,'PRINT_RESULTS':False,
        'DISPLAY_LESS_PROGRESS':True,'TIME_PROGRESS':False,'OUTPUT_SUMMARY':False,
        'OUTPUT_DETAILED':False,'PLOT_CURVES':False,'LOG_ON_ERROR':None,'BREAK_ON_ERROR':True})
    from meanshift_trackeval import LazyMotChallenge2DBox
    assert json.loads((RAW/'evaluator-equivalence.json').read_text())['status']=='pass'
    dataset=LazyMotChallenge2DBox(config)
    result,status=evaluator.evaluate([dataset],[trackeval.metrics.HOTA(),trackeval.metrics.CLEAR(),trackeval.metrics.Identity()])
    scored={}
    for label,folder in labels.items():
        assert status[dataset.get_name()][label]=='Success'
        scores={('OVERALL' if seq=='COMBINED_SEQ' else seq):{
            'HOTA':float(np.mean(row['pedestrian']['HOTA']['HOTA']))*100,
            'MOTA':float(row['pedestrian']['CLEAR']['MOTA'])*100,
            'IDF1':float(row['pedestrian']['Identity']['IDF1'])*100,
            'IDSW':int(row['pedestrian']['CLEAR']['IDSW'])}
            for seq,row in result[dataset.get_name()][label].items()}
        mm=motmetrics_score('MOT20',folder)
        if label!='meanshift':
            assert scores==original[label]['scores']['TrackEval']
            assert mm==original[label]['scores']['motmetrics']
        scored[label]={'TrackEval':scores,'motmetrics':mm,'sha256':hashes[label]}
        print(f'{label}: TrackEval {scores["OVERALL"]}',flush=True)
    write_json(RAW/'evaluation.json',{**context(),'results':scored,'original_baselines_exact':True,
        'raw_similarities':'computed on demand in own dataset adapter; identical float64 IoU/preprocessing/metric APIs',
        'trackeval_revision':'12c8791b303e0a0b50f753af204249e622d0281a'})


def verify_evaluator():
    import shutil
    from meanshift_trackeval import LazyMotChallenge2DBox,trackeval
    seq='MOT17-05-FRCNN'
    folder=BASE/'equivalence-input'/'nano'/'data'
    folder.mkdir(parents=True,exist_ok=True)
    source=ROOT/'data/phase-3/tracks/end-to-end/nano'/f'{seq}.txt'
    shutil.copyfile(source,folder/source.name)
    seqmap=BASE/'equivalence-seqmap.txt'
    seqmap.write_text('name\n'+seq+'\n')
    cfg={'GT_FOLDER':str(ROOT/'data/MOT17/train'),'TRACKERS_FOLDER':str(BASE/'equivalence-input'),
         'TRACKERS_TO_EVAL':['nano'],'BENCHMARK':'MOT17','SPLIT_TO_EVAL':'train',
         'SKIP_SPLIT_FOL':True,'SEQMAP_FILE':str(seqmap),'PRINT_CONFIG':False}
    ordinary=trackeval.datasets.MotChallenge2DBox(cfg)
    lazy=LazyMotChallenge2DBox(cfg)
    direct=ordinary.get_preprocessed_seq_data(ordinary.get_raw_seq_data('nano',seq),'pedestrian')
    optimized=lazy.get_preprocessed_seq_data(lazy.get_raw_seq_data('nano',seq),'pedestrian')
    assert direct.keys()==optimized.keys()
    arrays=0
    for key,values in direct.items():
        other=optimized[key]
        if isinstance(values,list):
            assert len(values)==len(other)
            for a,b in zip(values,other):
                assert np.array_equal(a,b),key
                if isinstance(a,np.ndarray):assert a.dtype==b.dtype
                arrays+=1
        else:assert values==other,key
    for metric in (trackeval.metrics.HOTA(),trackeval.metrics.CLEAR(),trackeval.metrics.Identity()):
        a,b=metric.eval_sequence(direct),metric.eval_sequence(optimized)
        assert a.keys()==b.keys()
        for key in a:assert np.array_equal(a[key],b[key]),(metric.get_name(),key)
    write_json(RAW/'evaluator-equivalence.json',{**context(),'status':'pass','sequence':seq,
        'source_tracks_sha256':sha(source),'frames':direct['num_timesteps'],
        'arrays_equal':arrays,'float_dtype_unchanged':True,'all_metric_fields_equal':True,
        'adapter_sha256':sha(ROOT/'python/meanshift_trackeval.py')})
    print(f'TrackEval lazy/eager equivalence pass: {direct["num_timesteps"]} frames, {arrays} arrays',flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('stage',choices=['preflight','verify-evaluator','track','benchmark','evaluate'])
    p.add_argument('--sequence',type=Path)
    p.add_argument('--repeat',type=int,choices=[1,2,3])
    a=p.parse_args()
    cv2.setNumThreads(1)
    cv2.ocl.setUseOpenCL(False)
    BASE.mkdir(parents=True,exist_ok=True);RAW.mkdir(parents=True,exist_ok=True)
    if a.stage=='preflight':preflight()
    elif a.stage=='verify-evaluator':verify_evaluator()
    elif a.stage=='evaluate':evaluate()
    else:
        assert a.sequence is not None
        if a.stage=='track':assert a.sequence.parent==ROOT/'data/MOT20/train'
        else:assert a.sequence==ROOT/'data/MOT17/train/MOT17-02-FRCNN' and a.repeat is not None
        track(a.sequence,a.repeat if a.stage=='benchmark' else None)


if __name__=='__main__':main()
