"""Collect early 3a/3b status from actual scores and verified end-to-end bytes."""
import argparse
import json
from phase3_common import ROOT
from compare_tracking import compare
p=argparse.ArgumentParser();p.add_argument('--model',choices=['nano','tiny'],required=True)
a=p.parse_args();model=a.model
data=json.loads((ROOT/'results/phase-3'/f'evaluation-parity-MOT17-{model}.json').read_text())['results']['MOT17']
py=data['python'][model]['scores']['motmetrics'];cpp=data['cpp'][model]['scores']['motmetrics']
delta={name:{metric:abs(cpp[name][metric]-py[name][metric]) for metric in ('mota','idf1')}
       for name in cpp if name!='OVERALL'}
checks={}
for name in delta:
    paths={impl:ROOT/'data/phase-3/tracks'/impl/model/(name+'.txt') for impl in ('python','cpp','end-to-end')}
    checks[name]={'cpp_vs_python':compare(paths['python'],paths['cpp']),
                 'end_to_end_vs_cached_cpp':compare(paths['cpp'],paths['end-to-end'])}
end_equal=all(v['end_to_end_vs_cached_cpp']['byte_identical'] for v in checks.values())
published={'nano':{'mota':69.0,'idf1':66.3},'tiny':{'mota':77.1,'idf1':71.5}}[model]
gap={m:cpp['OVERALL'][m]-published[m] for m in published}
result={'model':model,'evaluator':'motmetrics 1.4.0','3a':{'per_sequence_delta_pp':delta,
    'pass':all(abs(v)<=.1 for seq in delta.values() for v in seq.values())},
    '3b':{'scores':cpp['OVERALL'],'published':published,'delta_pp':gap,
          'pass':end_equal and all(abs(v)<=1 for v in gap.values()),
          'evaluation_input':'cached C++ outputs; end-to-end bytes independently checked'},
    'end_to_end_equals_cached_cpp':end_equal,'comparisons':checks}
out=ROOT/'results/phase-3'/f'completed-MOT17-{model}.json'
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
