"""Collect partial reproduction evidence without upgrading a snapshot to clone acceptance."""
import ast
import hashlib
import json
from phase3_common import ROOT

base = ROOT/'results/phase-6'
r = json.loads((ROOT/'results/phase-6-reproduction-local.json').read_text())
clone_files = set((base/'clone-files.txt').read_text().splitlines())
required = ['README.md', 'scripts/reproduce.sh', 'cpp/src/track_sequence.cpp', 'cpp/src/benchmark_pipeline.cpp']
missing = [p for p in required if p not in clone_files]
assert missing and not (base/'clone-status.txt').read_text().strip()
root_check = json.loads((base/'root-check.json').read_text())
r.update(status='phase-6-partial-local-validation-complete', full_mode_executed=False,
    clone_inventory={'head':(base/'clone-head.txt').read_text().strip(), 'clean':True,
        'required_source_missing':missing, 'full_current_source_available':False},
    source_archive_sha256=(base/'source-archive-sha256.txt').read_text().split()[0],
    standalone_cpp_build={'offline_exit_code':int((base/'root-build-exit.txt').read_text()),
        'online_build_succeeded':True, 'image':(base/'root-image.txt').read_text().strip(),
        'environment':json.loads((base/'root-environment.json').read_text()),
        'packages':(base/'root-packages.txt').read_text().splitlines(), 'validation':root_check,
        'limits':'Original C++ recipe tested; fresh Python dependency installation/full experiment not performed.'},
    retained_failures=[{'kind':'offline-root-build','log':'results/phase-6/root-build-offline.log'},
        {'kind':'Docker-unshared-temporary-path','log':'results/phase-6/snapshot-first-attempt.log'},
        {'kind':'read-only-missing-submount-directory','log':'results/phase-6/snapshot-mountpoint-attempt.log'},
        {'kind':'tiny-smoke-median-outside-frozen-repeat-range','report':'results/phase-6-reproduction-local.json'}])
for name in ('phase6_preflight.py','phase6_smoke_report.py','finalize_phase6.py','report_phase4.py'):
    ast.parse((ROOT/'python'/name).read_text(), filename=name)
r['phase6_python_syntax']='pass'
r['evidence_sha256']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in (base/'root-build-network.log', base/'root-check.json', base/'clone-files.txt', base/'preflight.json')}
(ROOT/'results/phase-6-reproduction.json').write_text(json.dumps(r,indent=2)+'\n')
text=(ROOT/'results/phase-6-reproduction-local.md').read_text()
text += '\n## Actual clone and standalone build\n\n'
text += f'Actual clean HEAD clone: `{r["clone_inventory"]["head"]}`. Missing current required files: '+', '.join(f'`{p}`' for p in missing)+'. No commit or push was made.\n\n'
text += 'The root C++ recipe initially failed offline because its apt layer was unavailable. After using the existing owner download authorization for the original dependency recipe, the online build succeeded with the SHA-checked ORT release. Its environment check passed; both FP32 models’ first-50-frame detection and track outputs are byte-identical to the frozen slices. This does not establish a fresh Python dependency build or a full fresh-clone run.\n\n'
text += 'Initial unshared temporary-path and missing read-only mountpoint failures are retained. The successful snapshot used an independent directory within the already shared project, empty submount destinations and explicit read-only input mounts. No Docker global setting or runtime protection changed. The strict tiny speed failure remains in the original smoke report, despite its faster measured throughput.\n\n'
text += 'Full mode rejects uncommitted source before builds or experiment writes. It is prepared and syntax-checked, not executed. Phase 6 remains partial: complete-source commit, independently inspected clone, full quality/INT8/all-budget execution and review are still required. A numerical-check result alone does not assert fresh-clone acceptance.\n'
(ROOT/'results/phase-6-reproduction.md').write_text(text)
print(json.dumps({'status':r['status'],'fresh_clone_gate_passed':False,'root_cpp_outputs_identical':root_check['all_byte_identical'],'clone_missing':missing}),flush=True)
