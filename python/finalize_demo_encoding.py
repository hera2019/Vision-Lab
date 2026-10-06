"""Verify an H.264 derivative, replace the clip, and refresh its manifest."""
import argparse
import hashlib
import json
from pathlib import Path
import cv2
p=argparse.ArgumentParser();p.add_argument('--video',required=True)
a=p.parse_args();video=Path(a.video);encoded=video.with_suffix('.h264.mp4')
metadata=json.loads(video.with_suffix('.json').read_text())
cap=cv2.VideoCapture(str(encoded));count=0
fps=cap.get(cv2.CAP_PROP_FPS)
while True:
    ok,frame=cap.read()
    if not ok:break
    if list(frame.shape[1::-1])!=metadata['size']:raise RuntimeError('encoded dimensions changed')
    count+=1
cap.release()
if count!=metadata['decoded_frames'] or abs(fps-metadata['fps'])>1e-6:
    raise RuntimeError('encoded frame count/rate changed')
encoded.replace(video)
metadata.update(codec='H.264 / avc1',encoded_frames_verified=count,
                sha256=hashlib.sha256(video.read_bytes()).hexdigest())
video.with_suffix('.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(json.dumps({'video':str(video),'codec':metadata['codec'],'sha256':metadata['sha256']}),flush=True)
