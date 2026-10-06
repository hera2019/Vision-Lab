"""Early parity check on one complete sequence (criterion 3a, same evaluator)."""
import argparse
import json
from pathlib import Path
from phase3_common import ROOT
from compare_tracking import compare
import motmetrics as mm
mm.lap.default_solver='lap'
p=argparse.ArgumentParser();p.add_argument('--sequence',required=True);p.add_argument('--model',required=True)
a=p.parse_args();seq=Path(a.sequence);model=a.model
gt=mm.io.loadtxt(seq/'gt/gt.txt',fmt='mot15-2D',min_confidence=1)
paths={impl:ROOT/'data/phase-3/tracks'/impl/model/(seq.name+'.txt') for impl in ('python','cpp')}
accs=[mm.utils.compare_to_groundtruth(gt,mm.io.loadtxt(path,fmt='mot15-2D',min_confidence=-1),'iou',distth=.5)
      for path in paths.values()]
scores=mm.metrics.create().compute_many(accs,names=list(paths),metrics=['mota','idf1'])
delta={k:float(abs(scores.loc['cpp',k]-scores.loc['python',k])*100) for k in ('mota','idf1')}
result={'sequence':seq.name,'model':model,'evaluator':'motmetrics 1.4.0',
        'scores':{impl:{k:float(scores.loc[impl,k]*100) for k in ('mota','idf1')} for impl in paths},
        'delta_pp':delta,'pass':all(x<=.1 for x in delta.values()),
        'output_comparison':compare(paths['python'],paths['cpp'])}
out=ROOT/'results/phase-3'/f'parity-{model}-{seq.name}.json'
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
