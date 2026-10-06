"""Report INT8 1/4-thread detection determinism on the existing fixed slice."""
import csv
import hashlib
import json
from phase3_common import ROOT

base = ROOT/'data/phase-4/determinism'
result = {}
for model in ('nano', 'tiny'):
    paths = [base/f'{model}-t{threads}.txt' for threads in (1, 4)]
    for path in paths:
        rows = list(csv.DictReader(path.with_suffix('.txt.timing.csv').open()))
        assert len(rows) == 50 and [int(r['frame']) for r in rows] == list(range(1, 51))
    result[model] = {'byte_identical_1_4': paths[0].read_bytes() == paths[1].read_bytes(),
        'sha256': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}}
output = {'scope': 'MOT17-02 frames 1–50; consistency check only, not full held-out per-thread accuracy.',
          'models': result, 'accuracy_threads': 4}
(ROOT/'results/phase-4/int8-thread-check.json').write_text(json.dumps(output, indent=2)+'\n')
print(json.dumps(output), flush=True)
