"""Render local MOT sequence + measured C++ tracks, without changing tracking."""
import argparse
from collections import defaultdict, deque
import hashlib
import json
import time
from pathlib import Path
import cv2
import numpy as np
from phase3_common import sequence_info

def color(identity):
    # Stable ID-derived color, shared by its box and trail.
    hsv=np.array([[[int(identity*68.754)%180,210,255]]],dtype=np.uint8)
    return tuple(int(x) for x in cv2.cvtColor(hsv,cv2.COLOR_HSV2BGR)[0,0])

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--sequence',required=True);p.add_argument('--tracks',required=True)
    p.add_argument('--out',required=True);p.add_argument('--model',required=True)
    p.add_argument('--start',type=int,default=1);p.add_argument('--seconds',type=int,default=12)
    a=p.parse_args();info=sequence_info(a.sequence);fps=int(info['framerate'])
    end=min(int(info['seqlength']),a.start+a.seconds*fps-1)
    target=Path(a.out);target.parent.mkdir(parents=True,exist_ok=True)
    rows=defaultdict(list)
    with open(a.tracks) as f:
        for line in f:
            r=[float(v) for v in line.strip().split(',')]
            rows[int(r[0])].append((int(r[1]),r[2:6]))
    width,height=int(info['imwidth']),int(info['imheight'])
    scale=min(1,1280/width,720/height)
    size=(int(width*scale)//2*2,int(height*scale)//2*2)
    writer=cv2.VideoWriter(str(target),cv2.VideoWriter_fourcc(*'mp4v'),fps,size)
    if not writer.isOpened():raise RuntimeError('VideoWriter failed')
    trails=defaultdict(deque);identities=set();begin=time.perf_counter()
    snapshots={a.start,(a.start+end)//2,end}
    for frame in range(a.start,end+1):
        image=Path(a.sequence)/info['imdir']/f"{frame:06d}{info['imext']}"
        image=cv2.imread(str(image))
        if image is None:raise RuntimeError(f'unreadable frame {frame}')
        image=cv2.resize(image,size)
        # Remove stale paths, and break the path across a detection gap.
        for identity in list(trails):
            while trails[identity] and trails[identity][0][0]<frame-2*fps:trails[identity].popleft()
            if not trails[identity]:del trails[identity]
        for identity,box in rows[frame]:
            identities.add(identity);x,y,w,h=box
            x1,y1,x2,y2=[int(round(v*scale)) for v in (x,y,x+w,y+h)]
            point=((x1+x2)//2,y2);trail=trails[identity]
            if trail and frame-trail[-1][0]>1:trail.clear()
            trail.append((frame,point));c=color(identity)
            if len(trail)>1:cv2.polylines(image,[np.array([v[1] for v in trail],dtype=np.int32)],False,c,2,cv2.LINE_AA)
            cv2.rectangle(image,(x1,y1),(x2,y2),c,2)
            label=f'ID {identity}';text_width=cv2.getTextSize(label,cv2.FONT_HERSHEY_SIMPLEX,.4,1)[0][0]
            # Keep labels visible when a close person extends outside the image.
            label_x=max(0,min(x1,size[0]-text_width-5))
            baseline=max(44,min(y1,size[1]-24))
            cv2.rectangle(image,(label_x,baseline-17),(label_x+text_width+5,baseline),c,-1)
            cv2.putText(image,label,(label_x+2,baseline-4),cv2.FONT_HERSHEY_SIMPLEX,.4,(0,0,0),1,cv2.LINE_AA)
        cv2.rectangle(image,(0,0),(size[0],24),(20,20,20),-1)
        cv2.putText(image,f"Vision Lab | YOLOX {a.model} + C++ ByteTrack | {info['name']} | frame {frame}",
                    (8,17),cv2.FONT_HERSHEY_SIMPLEX,.43,(255,255,255),1,cv2.LINE_AA)
        cv2.rectangle(image,(0,size[1]-22),(size[0],size[1]),(20,20,20),-1)
        cv2.putText(image,'Source: MOTChallenge | CC BY-NC-SA 3.0 | Research demo | 2-second image-space trails',
                    (8,size[1]-7),cv2.FONT_HERSHEY_SIMPLEX,.38,(230,230,230),1,cv2.LINE_AA)
        writer.write(image)
        if frame in snapshots:cv2.imwrite(str(target.with_suffix(f'.frame-{frame}.jpg')),image)
    writer.release()
    cap=cv2.VideoCapture(str(target));decoded=0
    while True:
        ok,image=cap.read()
        if not ok:break
        if image.shape[1::-1]!=size:raise RuntimeError('invalid decoded size')
        decoded+=1
    cap.release()
    if decoded!=end-a.start+1:raise RuntimeError(f'video verification failed: decoded {decoded}')
    metadata={'sequence':info['name'],'model':a.model,'tracks':a.tracks,
        'frame_range':[a.start,end],'fps':fps,'size':size,'decoded_frames':decoded,
        'unique_ids':len(identities),'trail_seconds':2,'render_seconds':time.perf_counter()-begin,
        'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
        'source':'https://motchallenge.net/','license':'CC BY-NC-SA 3.0',
        'note':'Playback rate is the source rate, not measured inference throughput. Colors identify tracker IDs; identity switches remain visible.'}
    target.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps(metadata),flush=True)

if __name__=='__main__':main()
