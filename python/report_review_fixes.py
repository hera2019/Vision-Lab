"""Record Opus review follow-up checks without re-scoring unchanged tracks."""
import hashlib
import json
from pathlib import Path
import numpy as np
from phase3_common import ROOT
from compare_tracking import compare

base = ROOT/'data/phase-3'
hash_file = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
outputs = []
for model in ('nano', 'tiny'):
    for path in sorted((base/'review-fixes'/model).glob('*.txt')):
        baseline = base/'tracks/cpp'/model/path.name
        equal = path.read_bytes() == baseline.read_bytes()
        assert equal, f'Reformatted tracker changed {model}/{path.name}'
        outputs.append({'model': model, 'sequence': path.stem, 'byte_identical': equal,
            'sha256': hash_file(path), 'baseline_sha256': hash_file(baseline)})
assert len(outputs) == 22, f'Expected 22 complete outputs, got {len(outputs)}'
edge = compare(base/'edge-cases/python.txt', base/'review-fixes/edge-cases.txt')
edge['pass'] = edge['same_frame_and_id'] and edge['max_box_difference'] <= .100001 and edge['max_score_difference'] < 1e-6
assert edge['pass']

score_examples = []
for model, name in (('nano', 'MOT20-02'), ('tiny', 'MOT20-05')):
    left = np.loadtxt(base/'tracks/python'/model/f'{name}.txt', delimiter=',')
    right = np.loadtxt(base/'tracks/cpp'/model/f'{name}.txt', delimiter=',')
    assert np.array_equal(left[:, :6], right[:, :6])
    for index in np.flatnonzero(np.abs(left[:, 6]-right[:, 6]) > 1e-6):
        score_examples.append({'model': model, 'sequence': name, 'frame': int(left[index, 0]),
            'id': int(left[index, 1]), 'python_score': float(left[index, 6]),
            'cpp_score': float(right[index, 6]), 'difference': float(abs(left[index, 6]-right[index, 6]))})
assert len(score_examples) == 3, score_examples

walkthrough = ROOT/'docs/walkthrough/phase-3.md'
text = walkthrough.read_text()
terms = ('motmetrics', 'TrackEval', 'ID switch', 'Behavioral fixture', 'Determinism', 'Domain shift')
assert all(term in text for term in terms)
assert '| MOT20 / held-out | TrackEval |' in text
result = {'date': '2026-10-06', 'author': 'Codex / GPT-6 (exact runtime model ID not exposed)',
    'review_source': 'docs/reviews/phase-3.md', 'status': 'follow-ups-addressed',
    'F1': {'walkthrough_words_whitespace_count': len(text.split()), 'sha256': hash_file(walkthrough),
           'english_then_chinese': True, 'result_table_and_new_terms_present': True},
    'F2': {'outputs': outputs, 'all_22_byte_identical': True, 'behavioral_fixture': edge,
           'tracker_source_sha256': hash_file(ROOT/'cpp/src/tracker/tracker.cpp'),
           'image_tag': 'vision-lab:review-fixes',
           'image_versions': (ROOT/'results/phase-3/review-fixes-image-versions.txt').read_text().splitlines(),
           'build_log': 'results/phase-3/review-fixes-offline-rebuild.log',
           'initial_build_failure': {'log': 'results/phase-3/review-fixes-build.log',
               'reason': 'Changing build network mode missed dependency-layer cache; apt could not run offline.',
               'resolution': 'Reuse accepted local vision-lab:dev toolchain via Dockerfile.review-fixes; no packages downloaded.'}},
    'F3': {'score_boundary_rows': score_examples,
           'documentation_corrected': ['docs/ISSUES.md', 'results/phase-3-tracking.md', 'python/report_phase3.py']},
    'limitations': 'Follow-up verification by executor; reviewer has not re-reviewed these changes. No detector rerun needed because tracker outputs are byte-identical.'}
(ROOT/'results/phase-3-review-fixes.json').write_text(json.dumps(result, indent=2)+'\n')
(ROOT/'results/phase-3-review-fixes.md').write_text('''# Phase 3 review follow-ups

Date: 2026-10-06. Author: Codex / GPT-6 (exact runtime model ID not exposed).

All three non-blocking follow-ups in `docs/reviews/phase-3.md` are addressed
and checked by the executor. This is not a new independent review verdict.

- **F1:** expanded the walkthrough to English/Chinese paragraph pairs, covering
  tracker mechanics, both evaluators, fixtures, determinism, domain shift,
  labelled result tables, and the two owner-reported failures. New terms have
  a glossary. Earlier-phase explanations are not redefined.
- **F2:** expanded compressed statements and loops, replaced opaque type/local
  aliases with readable names, and added comments aligning stages with Python.
  Built a separate offline `vision-lab:review-fixes` image. All 22 nano/tiny
  complete-sequence cache-track outputs are byte-identical to the accepted
  C++ baseline. The behavioral fixture, including exact float32 boundaries,
  still passes against Python. No settings or arithmetic order changed.
- **F3:** clarified that the tiny representation-difference bound applied to
  the initial MOT17-02 sequence. Verified all three decimal-half boundary rows
  across nano MOT20-02 and tiny MOT20-05: score difference about 0.01, identical
  frames/IDs/boxes. Both configured evaluators ignore emitted prediction scores.
  Corrected I-5 and the report generator; original numeric result tables remain.

Verification uses existing detector caches; no model inference, asset download,
threshold tuning, or replacement of accepted track files was necessary.
Image/source/output provenance and the three score examples are in the paired JSON.

The first attempt to rebuild the full Dockerfile with network disabled missed
the dependency-layer cache and failed during package installation. Its log
is retained. `Dockerfile.review-fixes` instead reuses the accepted local
runtime image and installs nothing; this offline build succeeded.

Reproduce after building the separate image:

```sh
docker build --network=none -f Dockerfile.review-fixes -t vision-lab:review-fixes .
bash scripts/phase3_review_verify.sh
```

The baseline runtime image and original tracking outputs remain available.
''')
print(json.dumps({'all_22_byte_identical': True, 'fixture_pass': edge['pass'],
                  'score_boundary_rows': len(score_examples), 'status': result['status']}), flush=True)
