"""Finalize paired full-run reports; provenance and numerical gates are separate."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def build_report(root):
    base = root/'results/phase-6'
    load = lambda path: json.loads(path.read_text())
    checks = load(base/'full-check.json')
    commit = (base/'source-commit.txt').read_text().strip()
    origin = (base/'source-origin.txt').read_text().strip()
    if (base/'source-context.json').exists():
        proof = load(base/'source-context.json')
        if proof['run_id'] != checks.get('run_id') or proof['run_id'] != (base/'run-id.txt').read_text().strip():
            raise ValueError('Full check belongs to another run; refusing stale evidence.')
        context_pass = (proof['fresh_clone_context_passed'] is True
            and proof['source_commit'] == commit and proof['origin'] == origin
            and not (base/'source-status-before.txt').read_text().strip())
        provenance_path = base/'source-context.json'
        run_id = proof['run_id']
    else:
        # Historical dcdb81e run used separately recorded host clone proof.
        proof = load(base/'clone-proof.json')
        context_pass = (proof['source_commit'] == proof['clone_commit'] == commit
            and proof['source_tree'] == proof['clone_tree']
            and proof['clone_clean_before_assets'] and proof['clone_clean_after_assets']
            and proof['clone_origin'] == origin
            and not (base/'source-status-before.txt').read_text().strip())
        provenance_path = base/'clone-proof.json'
        run_id = None
    self_test = load(root/'results/phase-3/evaluation-self.json')
    if self_test.get('stage') != 'self' or set(self_test['results']) != {'MOT17', 'MOT20'}:
        raise ValueError('Both evaluator self-tests are required.')
    self_pass = all(row['pass'] is True for row in self_test['results'].values())
    evaluation = load(root/'results/phase-3/evaluation-final.json')
    if evaluation.get('fresh') is not True or set(evaluation['results']) != {'MOT17', 'MOT20'}:
        raise ValueError('Fresh complete evaluator results are required.')
    fresh_procedure = True
    for dataset, implementations in evaluation['results'].items():
        if set(implementations) != {'python', 'cpp', 'end-to-end'}:
            raise ValueError('All three tracking implementations are required.')
        for impl, models in implementations.items():
            if set(models) != {'nano', 'tiny'}:
                raise ValueError('Both models are required.')
            for row in models.values():
                if len(row['sha256']) != (7 if dataset == 'MOT17' else 4):
                    raise ValueError('Incomplete sequence output hashes.')
                if impl != 'end-to-end' and 'reused_from' in row:
                    fresh_procedure = False
    required = {(m, p, t) for m in ('nano','tiny') for p in ('fp32','int8') for t in (1,2,4)}
    budgets = checks['benchmark_settings']
    if len(budgets) != 12 or {(s['model'], s['precision'], s['threads']) for s in budgets} != required:
        raise ValueError('Exactly twelve unique benchmark settings are required.')
    numerical = (checks['exact_evaluation_equal'] is True and checks['int8_evaluation_equal'] is True
        and all(s['inside_interval'] is True for s in budgets))
    if checks['status'] != 'full-stages-executed' or checks['numerical_reproduction_checks_passed'] != numerical:
        raise ValueError('Inconsistent full numerical check.')
    gate = context_pass and self_pass and fresh_procedure and numerical
    now = datetime.now(timezone.utc).isoformat()
    return {'status': 'full-clean-clone-experiment-complete',
        'author': 'Codex / GPT-6 (exact runtime model ID not exposed)',
        'date': now[:10], 'report_generated_at_utc': now,
        'run_id': run_id, 'tested_source_commit': commit,
        'fresh_clone_context_passed': context_pass, 'clone_proof': proof,
        'fresh_evaluator_procedure_passed': fresh_procedure, 'ground_truth_self_test_passed': self_pass,
        'full_checks': checks, 'fresh_clone_gate_passed': gate,
        'speed_settings_passed': sum(s['inside_interval'] is True for s in budgets),
        'speed_settings_failed': sum(s['inside_interval'] is not True for s in budgets),
        'limitations': ['Cached Docker build layers are allowed; a cold dependency install is not established.',
            'Mac Docker Linux VM speed; no edge hardware or real-camera acceptance.',
            'Independent review remains separate; original INT8 failures remain failed.'],
        'evidence_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (base/'full-check.json', base/'preflight.json', provenance_path,
                      base/'python-environment.txt', root/'results/phase-3/evaluation-final.json',
                      root/'results/phase-3/evaluation-self.json', root/'results/phase-4-performance.json',
                      root/'results/phase-5-failures.json')}}


def write_report(root, result):
    (root/'results/phase-6-full-reproduction.json').write_text(json.dumps(result, indent=2)+'\n')
    checks = result['full_checks']
    lines = ['# Phase 6 — full clean-clone reproduction', '',
        f'**Experiment complete. Fresh-clone acceptance: {"PASS" if result["fresh_clone_gate_passed"] else "FAIL"}.**', '',
        'Author: '+result['author']+'. Report generated (UTC): '+result['report_generated_at_utc']+'.', '',
        f'Tested source commit: {result["tested_source_commit"]}. Run: {result["run_id"] or "historical-host-proof"}.', '',
        f'Clone context: {result["fresh_clone_context_passed"]}. Fresh evaluator procedure: {result["fresh_evaluator_procedure_passed"]}. Ground-truth self-test: {result["ground_truth_self_test_passed"]}.', '',
        f'All FP32 canonical evaluator scores and track hashes equal the frozen reference: {checks["exact_evaluation_equal"]}. INT8 scores and track hashes equal the frozen reference: {checks["int8_evaluation_equal"]}.', '',
        'All documented full-driver experiment stages completed. No benchmark retry, tuning, acceptance interval change or replacement baseline is implied by this report.', '',
        '| Model | Precision | Threads / CPU quota | Original FPS interval | New median FPS | Within interval |',
        '|---|---|---:|---|---:|---|']
    for row in checks['benchmark_settings']:
        low, high = row['reference_interval']
        lines.append(f'| {row["model"]} | {row["precision"]} | {row["threads"]} | {low:.3f}–{high:.3f} | {row["median_fps"]:.3f} | {row["inside_interval"]} |')
    lines += ['', 'The original three-repeat min/max rule remains fixed. A faster out-of-interval result still fails; source provenance and quality equality do not override it.', '',
        'This report describes the current disposable-clone run. Historical reports were retained before replacement; original main-checkout evidence stays separate. Raw evidence is in this checkout under results/phase-3/, results/phase-4/ and results/phase-6/.', '',
        'Limitations: '+ ' '.join(result['limitations']), '',
        'The paired JSON records current run/source identity, individual gates and evidence hashes.']
    (root/'results/phase-6-full-reproduction.md').write_text('\n'.join(lines)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--require-gate', action='store_true')
    args = parser.parse_args()
    root = Path('/work')
    result = build_report(root)
    write_report(root, result)
    print(json.dumps({k: result[k] for k in ('status','tested_source_commit','fresh_clone_context_passed','fresh_clone_gate_passed')}), flush=True)
    if args.require_gate and not result['fresh_clone_gate_passed']:
        raise SystemExit(1)
