"""Read-only required-input checks before reproduction; no downloading."""
import hashlib
import json
import sys
from pathlib import Path
from phase3_common import ROOT, sequence_info

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assets = json.loads((ROOT/'assets.json').read_text())
checks = {'models': {}, 'external_revisions': {}, 'sequences': {}}
revisions = dict(line.split() for line in (ROOT/'results/phase-6/external-revisions.txt').read_text().splitlines())
for model in ('nano', 'tiny'):
    path = ROOT/'models'/f'bytetrack_{model}_mot17.onnx'
    digest = sha(path)
    assert digest == assets['exported'][path.name]['sha256'], f'Model hash differs: {path}'
    checks['models'][model] = digest
for label in ('ByteTrack', 'TrackEval'):
    entry = assets['code'][label]
    revision = revisions[label]
    assert revision == entry['commit'], f'External revision differs: {label}'
    checks['external_revisions'][label] = revision
for dataset in ('MOT17', 'MOT20'):
    paths = sorted((ROOT/'data'/dataset/'train').glob('*-FRCNN' if dataset == 'MOT17' else 'MOT20-*'))
    assert len(paths) == (7 if dataset == 'MOT17' else 4)
    for path in paths:
        info = sequence_info(path); count = int(info['seqlength'])
        assert len(list((path/'img1').glob('*.jpg'))) == count
        assert (path/'gt/gt.txt').is_file()
        checks['sequences'][path.name] = {'frames': count, 'gt_sha256': sha(path/'gt/gt.txt')}
reference = json.loads((ROOT/'results/phase-4-performance.json').read_text())
image = ROOT/'data/MOT17/train/MOT17-02-FRCNN/img1/000001.jpg'
assert sha(image) == reference['input_frame_sha256']['MOT17-02-FRCNN/img1/000001.jpg']
if sys.argv[1] == 'smoke':
    assert (ROOT/'data/phase-3/edge-cases/dets.txt').is_file(), 'Smoke needs the frozen synthetic cache; full mode regenerates it.'
checks.update(status='pass', representative_image_sha256=sha(image),
              limitations='Hashes cover original models, GT and one representative image; all image counts checked. This is not a full image-byte integrity scan.')
(ROOT/'results/phase-6/preflight.json').write_text(json.dumps(checks, indent=2)+'\n')
print(json.dumps({'preflight': 'pass', 'models': 2, 'sequences': 11}), flush=True)
