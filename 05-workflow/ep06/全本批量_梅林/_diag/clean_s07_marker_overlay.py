import cv2, numpy as np, subprocess, tempfile
from pathlib import Path
src=Path(r'05-workflow/ep06/全本批量_梅林/视频草稿/EP06_S07_v2_本地_空间标记控制.mp4')
out=Path(r'05-workflow/ep06/全本批量_梅林/视频草稿/EP06_S07_v2_本地_空间控制_标记清理.mp4')
cap=cv2.VideoCapture(str(src)); fps=cap.get(cv2.CAP_PROP_FPS); w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)); count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
with tempfile.TemporaryDirectory() as td:
    temp=Path(td)/'cleaned.mp4'; writer=cv2.VideoWriter(str(temp),cv2.VideoWriter_fourcc(*'mp4v'),fps,(w,h)); n=0
    while True:
        ok,frame=cap.read()
        if not ok: break
        if n/fps < 2.1:
            mask=np.zeros((h,w),np.uint8)
            cv2.rectangle(mask,(75,211),(325,523),255,14)
            cv2.rectangle(mask,(350,185),(540,500),255,14)
            cv2.rectangle(mask,(570,285),(815,390),255,14)
            mask=cv2.dilate(mask,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(3,3)),iterations=1)
            frame=cv2.inpaint(frame,mask,8,cv2.INPAINT_TELEA)
        writer.write(frame); n+=1
    cap.release();writer.release()
    if n!=count:raise RuntimeError(f'{n}!={count}')
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(temp),'-i',str(src),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(out)],check=True)
print(f'cleaned first 2.1s across {n} frames; {out.stat().st_size} bytes')
