"""Behavioral fixtures for score tiers, empty frames, recovery and expiry.

Run --prepare before both tracker tools; --check after their outputs exist.
No detector is used and external tracker code stays unchanged.
"""
import argparse
import json
from pathlib import Path
from compare_tracking import compare
from phase3_common import ROOT

base=ROOT/'data/phase-3/edge-cases'
p=argparse.ArgumentParser();p.add_argument('--action',choices=['prepare','check'],required=True)
a=p.parse_args()
if a.action=='prepare':
    base.mkdir(parents=True,exist_ok=True)
    (base/'seqinfo.ini').write_text('[Sequence]\nname=Synthetic-edge-cases\nimDir=img1\nframeRate=30\nseqLength=80\nimWidth=640\nimHeight=480\nimExt=.jpg\n')
    rows=[]
    # One continuously present person drives the frame counter; another is
    # temporarily low-confidence, absent, recovered, then expires and returns.
    for frame in range(1,81):
        if frame==5:continue  # evaluator must skip this truly empty frame
        rows.append((frame,-1,400,80,440,180,{18:.6,20:.1}.get(frame,.9)))
        if frame in (1,2,3,4,6,9,10,50,51):
            score=.2 if frame in (3,4) else .9
            rows.append((frame,-1,100+frame*.1,100,140+frame*.1,200,score))
        # An unconfirmed one-frame false positive should be removed.
        if frame==12:rows.append((frame,-1,250,120,280,220,.85))
        if frame in (22,23,24):rows.append((frame,-1,250,120,280,220,.7 if frame==22 else .9))
    (base/'dets.txt').write_text(''.join(','.join(str(x) for x in row)+'\n' for row in rows))
else:
    result=compare(base/'python.txt',base/'cpp.txt')
    result['pass']=(result['same_frame_and_id'] and result.get('max_box_difference',0)<=.100001
                    and result.get('max_score_difference',0)<1e-6)
    result['covers']=['high/low confidence','empty-frame skip','lost recovery','expiry','unconfirmed removal',
                      'float32 threshold equality at 0.1, 0.6 and 0.7']
    (ROOT/'results/phase-3/edge-cases.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    if not result['pass']:raise RuntimeError('tracker behavioral fixture mismatch')
