"""Count actual cached scores for which double vs float32 thresholds differ."""
import argparse
import json
import numpy as np
from phase3_common import ROOT, config
p=argparse.ArgumentParser();p.add_argument('--model',choices=['nano','tiny'])
a=p.parse_args();output={}
for model in ([a.model] if a.model else ('nano','tiny')):
    output[model]={}
    for path in sorted((ROOT/'data/phase-3/dets'/model).glob('*.txt')):
        score=np.loadtxt(path,delimiter=',',ndmin=2)[:,-1].astype(np.float32)
        threshold=config(path.stem).track_thresh
        double=score.astype(np.float64)
        count={
            'high_comparison_difference':int(np.count_nonzero((double>threshold)!=(score>np.float32(threshold)))),
            'low_comparison_difference':int(np.count_nonzero(((double>.1)&(double<threshold))!=((score>np.float32(.1))&(score<np.float32(threshold))))),
            'new_track_comparison_difference':int(np.count_nonzero((double<threshold+.1)!=(score<np.float32(threshold+.1))))}
        output[model][path.stem]=count
suffix='-'+a.model if a.model else ''
(ROOT/'results/phase-3'/f'score-boundaries{suffix}.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output),flush=True)
