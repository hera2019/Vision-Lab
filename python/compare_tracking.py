"""Compare complete MOT outputs without hiding serialization differences."""
import argparse
import json
from pathlib import Path
import numpy as np

def compare(left, right):
    a_lines=Path(left).read_text().splitlines()
    b_lines=Path(right).read_text().splitlines()
    a=np.loadtxt(left,delimiter=',',ndmin=2) if a_lines else np.empty((0,10))
    b=np.loadtxt(right,delimiter=',',ndmin=2) if b_lines else np.empty((0,10))
    same_shape=a.shape==b.shape
    result={'left_lines':len(a_lines),'right_lines':len(b_lines),
        'byte_identical':Path(left).read_bytes()==Path(right).read_bytes(),
        'identical_line_share':sum(x==y for x,y in zip(a_lines,b_lines))/max(len(a_lines),len(b_lines),1),
        'same_frame_and_id':same_shape and bool(np.array_equal(a[:,:2],b[:,:2]))}
    if same_shape and len(a):
        result['max_box_difference']=float(np.max(np.abs(a[:,2:6]-b[:,2:6])))
        result['max_score_difference']=float(np.max(np.abs(a[:,6]-b[:,6])))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('left');p.add_argument('right');p.add_argument('--out')
    args=p.parse_args();result=compare(args.left,args.right)
    if args.out:Path(args.out).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
