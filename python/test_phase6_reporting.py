"""Reporting contracts using archived measurements and isolated synthetic gates."""
import contextlib
import csv
import io
import json
import runpy
import shutil
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch
from phase6_context import capture
from report_phase6_full import build_report, write_report

ROOT = Path('/work')
ARCHIVE = ROOT/'results/phase-6/full'


class ReportingContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.base = self.root/'results/phase-6'
        self.base.mkdir(parents=True)
        (self.root/'.git/objects/info').mkdir(parents=True)
        for name in ('cpp','python','scripts'):
            (self.root/name).mkdir()
        for source, target in [
            (ARCHIVE/'phase-3/evaluation-self.json', 'results/phase-3/evaluation-self.json'),
            (ARCHIVE/'phase-3/evaluation-final.json', 'results/phase-3/evaluation-final.json'),
            (ARCHIVE/'phase-4-performance.json', 'results/phase-4-performance.json'),
            (ARCHIVE/'phase-5-failures.json', 'results/phase-5-failures.json')]:
            dest = self.root/target
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dest)
        for name in ('source-commit.txt','source-origin.txt','source-status-before.txt','full-check.json','preflight.json','python-environment.txt'):
            shutil.copyfile(ARCHIVE/name, self.base/name)
        proof = json.loads((ARCHIVE/'clone-proof.json').read_text())
        (self.base/'source-tree.txt').write_text(proof['clone_tree'])
        (self.base/'source-upstream.txt').write_text(proof['clone_commit'])
        (self.base/'run-id.txt').write_text('isolated-report-fixture')
        capture(self.root, disposable=True)
        self.mutate('results/phase-6/full-check.json', lambda v: v.update(run_id='isolated-report-fixture'))

    def mutate(self, relative, change):
        path = self.root/relative
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))

    def numerical_pass_fixture(self):
        def change(value):
            for setting in value['benchmark_settings']:
                setting['median_fps'] = sum(setting['reference_interval'])/2
                setting['inside_interval'] = True
            value['numerical_reproduction_checks_passed'] = True
        self.mutate('results/phase-6/full-check.json', change)

    def test_archived_failure_emits_current_pair(self):
        result = build_report(self.root)
        self.assertFalse(result['fresh_clone_gate_passed'])
        self.assertTrue(result['fresh_clone_context_passed'])
        self.assertEqual(result['speed_settings_failed'], 8)
        write_report(self.root, result)
        saved = json.loads((self.root/'results/phase-6-full-reproduction.json').read_text())
        self.assertEqual(saved['run_id'], 'isolated-report-fixture')
        self.assertIn('acceptance: FAIL', (self.root/'results/phase-6-full-reproduction.md').read_text())

    def test_synthetic_all_pass_gate(self):
        self.numerical_pass_fixture()
        self.assertTrue(build_report(self.root)['fresh_clone_gate_passed'])

    def test_dirty_source_never_accepts_even_if_numbers_pass(self):
        self.numerical_pass_fixture()
        (self.base/'source-status-before.txt').write_text(' M cpp/source.cpp\n')
        capture(self.root, disposable=True)
        self.assertFalse(build_report(self.root)['fresh_clone_gate_passed'])

    def test_checkout_not_matching_upstream_never_accepts(self):
        self.numerical_pass_fixture()
        (self.base/'source-upstream.txt').write_text('0'*40)
        capture(self.root, disposable=True)
        self.assertFalse(build_report(self.root)['fresh_clone_gate_passed'])

    def test_stale_run_identity_rejected(self):
        self.mutate('results/phase-6/full-check.json', lambda v: v.update(run_id='previous-run'))
        with self.assertRaisesRegex(ValueError, 'another run'):
            build_report(self.root)

    def test_missing_self_test_rejected(self):
        (self.root/'results/phase-3/evaluation-self.json').unlink()
        with self.assertRaises(FileNotFoundError):
            build_report(self.root)

    def test_empty_self_tests_cannot_pass_vacuously(self):
        self.mutate('results/phase-3/evaluation-self.json', lambda v: v.update(results={}))
        with self.assertRaisesRegex(ValueError, 'Both evaluator'):
            build_report(self.root)

    def test_failed_self_test_prevents_acceptance(self):
        self.numerical_pass_fixture()
        self.mutate('results/phase-3/evaluation-self.json', lambda v: v['results']['MOT20'].update({'pass':False}))
        self.assertFalse(build_report(self.root)['fresh_clone_gate_passed'])

    def test_reused_evaluation_prevents_acceptance(self):
        self.numerical_pass_fixture()
        self.mutate('results/phase-3/evaluation-final.json', lambda v: v['results']['MOT20']['python']['nano'].update(reused_from='old-report.json'))
        self.assertFalse(build_report(self.root)['fresh_clone_gate_passed'])

    def test_missing_setting_rejected(self):
        self.mutate('results/phase-6/full-check.json', lambda v: v['benchmark_settings'].pop())
        with self.assertRaisesRegex(ValueError, 'twelve'):
            build_report(self.root)

    def test_historical_manual_proof_compatibility(self):
        (self.base/'source-context.json').unlink()
        shutil.copyfile(ARCHIVE/'clone-proof.json', self.base/'clone-proof.json')
        result = build_report(self.root)
        self.assertTrue(result['fresh_clone_context_passed'])
        self.assertFalse(result['fresh_clone_gate_passed'])

    def test_smoke_reports_scope_without_old_source_claims(self):
        # A different run date catches stale human headers, independently of today's date.
        self.mutate('results/phase-6/source-context.json',
                    lambda v: v.update(captured_at_utc='2040-01-02T03:04:05+00:00'))
        line = '1,1,0,0,20,20,0.8,-1,-1,-1\n'
        for model in ('nano','tiny'):
            for kind, ref in [('detections','dets'),('tracks','tracks/end-to-end')]:
                path = self.root/'data/phase-3'/ref/model/'MOT17-02-FRCNN.txt'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(line)
                path = self.root/'data/phase-6'/f'{model}-{kind}.txt'
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(line)
            for repeat in (1,2,3):
                path = self.base/f'{model}-r{repeat}.csv'
                with path.open('w') as handle:
                    writer = csv.DictWriter(handle, fieldnames=['frame','end_to_end_ms'])
                    writer.writeheader()
                    writer.writerows({'frame':frame,'end_to_end_ms':50} for frame in range(51,151))
                path.with_suffix('.json').write_text(json.dumps({'warmup':50,'measured':100,'threads':4,'cpu_max':'400000 100000','peak_rss_kib':1000}))
        for filename in ('edge-python.txt','edge-cpp.txt'):
            (self.root/'data/phase-6'/filename).write_text(line)
        for filename in ('built-image.txt','toolchain-image.txt'):
            (self.base/filename).write_text('synthetic-image')
        module = types.ModuleType('phase3_common'); module.ROOT = self.root
        with patch.dict(sys.modules, {'phase3_common':module}), patch.object(sys, 'argv', ['phase6_smoke_report.py','smoke']), contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(ROOT/'python/phase6_smoke_report.py'))
        text = (self.root/'results/phase-6-reproduction.md').read_text()
        self.assertNotIn('HEAD currently contains only', text)
        self.assertNotIn('Full mode is prepared but unexecuted', text)
        self.assertIn('bounded smoke run', text)
        result = json.loads((self.root/'results/phase-6-reproduction.json').read_text())
        self.assertFalse(result['fresh_clone_gate_passed'])
        self.assertEqual(result['source_context']['run_id'], 'isolated-report-fixture')
        self.assertEqual(result['date'], '2040-01-02')
        self.assertIn('Date: 2040-01-02.', text)


class DriverFailureContract(unittest.TestCase):
    def test_build_failure_cannot_leave_old_completed_report_current(self):
        # Synthetic Git/df/build commands exercise only reporting lifecycle.
        # No image build, container launch, dataset or acceptance measurement occurs.
        with tempfile.TemporaryDirectory(dir=ROOT/'data/phase-6-review') as folder:
            root = Path(folder)
            (root/'scripts').mkdir(); (root/'.git').mkdir()
            (root/'results').mkdir(); (root/'fakebin').mkdir()
            shutil.copyfile(ROOT/'scripts/reproduce.sh', root/'scripts/reproduce.sh')
            previous = {'status':'old-complete','fresh_clone_gate_passed':True}
            (root/'results/phase-6-full-reproduction.json').write_text(json.dumps(previous))
            (root/'results/phase-6-full-reproduction.md').write_text('Old completed report')
            git_stub = '''#!/bin/sh
case "$*" in
  'diff --quiet'|'diff --cached --quiet'|'ls-files --others --exclude-standard'|'status --porcelain --untracked-files=no') exit 0;;
  'rev-parse --show-toplevel') printf '%s\\n' "$DRIVER_FIXTURE_ROOT";;
  'rev-parse HEAD'|'rev-parse @{upstream}') printf '%040d\\n' 1;;
  'rev-parse HEAD^{tree}') printf '%040d\\n' 2;;
  'remote get-url origin') printf '/synthetic/source\\n';;
  *) exit 91;;
esac
'''
            for name, body in [('git',git_stub), ('df',"#!/bin/sh\nprintf 'Filesystem 1024-blocks Used Available Capacity Mounted\\nfake 60000000 10000000 50000000 17%% /fixture\\n'\n"), ('docker','#!/bin/sh\nexit 23\n')]:
                path = root/'fakebin'/name
                path.write_text(body); path.chmod(0o755)
            env = {**os.environ, 'PATH':str(root/'fakebin')+':'+os.environ['PATH'],
                'VL_DISPOSABLE_CLONE':'1','VL_BUILD_NETWORK':'none','DRIVER_FIXTURE_ROOT':str(root)}
            completed = subprocess.run(['bash',str(root/'scripts/reproduce.sh'),'full'], env=env, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 23, completed.stderr)
            current = json.loads((root/'results/phase-6-full-reproduction.json').read_text())
            self.assertEqual(current['status'], 'started-not-finalized')
            self.assertFalse(current['fresh_clone_gate_passed'])
            saved = json.loads((root/'results/phase-6/previous-full-report/report.json').read_text())
            self.assertEqual(saved, previous)


if __name__ == '__main__':
    unittest.main(verbosity=2)
