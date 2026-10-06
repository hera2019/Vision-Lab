"""Collect full-run checks with separately recorded host Git-clone provenance."""
import hashlib
import json
from pathlib import Path
from phase3_common import ROOT

base = ROOT/'results/phase-6'
checks = json.loads((base/'full-check.json').read_text())
proof = json.loads((base/'clone-proof.json').read_text())
commit = (base/'source-commit.txt').read_text().strip()
origin = (base/'source-origin.txt').read_text().strip()
context_pass = (proof['source_commit'] == proof['clone_commit'] == commit
                and proof['source_tree'] == proof['clone_tree']
                and proof['clone_clean_before_assets']
                and proof['clone_clean_after_assets']
                and proof['clone_origin'] == origin
                and not (base/'source-status-before.txt').read_text().strip())
self_test = json.loads((ROOT/'results/phase-3/evaluation-self.json').read_text())
self_pass = all(row['pass'] for row in self_test['results'].values())
evaluation = json.loads((ROOT/'results/phase-3/evaluation-final.json').read_text())
assert evaluation['fresh'], 'Historical evaluator reuse cannot establish reproduction.'
fresh_procedure = all('reused_from' not in row
    for implementations in evaluation['results'].values()
    for impl, models in implementations.items() if impl != 'end-to-end'
    for row in models.values())
gate = context_pass and self_pass and fresh_procedure and checks['numerical_reproduction_checks_passed']
result = {'status': 'full-clean-clone-experiment-complete',
    'author': 'Codex / GPT-6 (exact runtime model ID not exposed)',
    'date': '2026-10-07', 'tested_source_commit': commit,
    'fresh_clone_context_passed': context_pass, 'clone_proof': proof,
    'fresh_evaluator_procedure_passed': fresh_procedure, 'ground_truth_self_test_passed': self_pass,
    'full_checks': checks, 'fresh_clone_gate_passed': gate,
    'limitations': ['Cached Docker build layers are allowed; a cold dependency install is not established.',
        'Mac Docker Linux VM speed; no edge hardware or real-camera acceptance.',
        'Independent review remains pending; original INT8 failures remain failed.'],
    'evidence_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (base/'full-check.json', base/'preflight.json', base/'clone-proof.json',
                  base/'python-environment.txt', ROOT/'results/phase-3/evaluation-final.json',
                  ROOT/'results/phase-3/evaluation-self.json', ROOT/'results/phase-4-performance.json',
                  ROOT/'results/phase-5-failures.json')}}
(ROOT/'results/phase-6-full-reproduction.json').write_text(json.dumps(result, indent=2)+'\n')
lines = ['# Phase 6 — full clean-clone reproduction', '',
    f'**Experiment complete. Fresh-clone acceptance: {"PASS" if gate else "FAIL"}.**', '',
    'Author: '+result['author']+'. Date: '+result['date']+'.', '',
    f'Tested source commit: `{commit}`. Clone context: {context_pass}. Fresh evaluator procedure: {fresh_procedure}. Ground-truth self-test: {self_pass}.', '',
    f'All FP32 canonical evaluator scores and track hashes equal the frozen reference: {checks["exact_evaluation_equal"]}. INT8 scores and track hashes equal the frozen reference: {checks["int8_evaluation_equal"]}.', '',
    'The full driver rebuilt the documented images, regenerated all detection caches, Python/C++ tracking and end-to-end outputs, recomputed reference metrics, recalibrated both fixed INT8 models, ran all 36 paired benchmarks and held-out INT8 evaluations, and regenerated the three failure-case crops. Runs use the original hardened container boundary. All failed criteria remain failed.', '',
    '| Model | Precision | Threads / CPU quota | Original FPS interval | New median FPS | Within interval |',
    '|---|---|---:|---|---:|---|']
for row in checks['benchmark_settings']:
    low, high = row['reference_interval']
    lines.append(f'| {row["model"]} | {row["precision"]} | {row["threads"]} | {low:.3f}–{high:.3f} | {row["median_fps"]:.3f} | {row["inside_interval"]} |')
lines += ['', 'Speed acceptance retains the predeclared original three-repeat min/max interval. A faster result outside the interval also fails; the interval is not widened after measurement. Quality equality and valid Git-clone provenance do not override failed speed checks.', '',
    'Original Phase 3–5 evidence in the main checkout is unchanged. Full-run outputs live in the disposable clone; canonical reference JSON files were archived before overwrite. The historical snapshot smoke report remains separate.', '',
    'Limitations: '+ ' '.join(result['limitations']), '',
    'See the paired JSON for clone tree/commit evidence, per-setting checks and hashes; raw logs and metadata are under `results/phase-6/`.']
(ROOT/'results/phase-6-full-reproduction.md').write_text('\n'.join(lines)+'\n')
print(json.dumps({k: result[k] for k in ('status','tested_source_commit','fresh_clone_context_passed','fresh_clone_gate_passed')}), flush=True)
