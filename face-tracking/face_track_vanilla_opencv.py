# OpenCV Face detection test

import os
import sys
import math
import time
from datetime import datetime
import numpy as np
import cv2


os.chdir(os.path.expanduser('~/Dropbox/Development/animoid/opencv'))

import pantiltcontrol_rc_ard as sc

try:
    fn = sys.argv[1]
except:
    fn = 0

# utility
def argmin(l):
  return l.index(min(l))

from pkg_resources import parse_version
OPCV3 = parse_version(cv2.__version__) >= parse_version('3')

def capPropId(prop):
  return getattr(cv2 if OPCV3 else cv2.cv,
    ("" if OPCV3 else "CV_") + "CAP_PROP_" + prop)

  
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')
assert not face_cascade.empty(), 'classifier loaded'

cam = cv2.VideoCapture(fn)
cam.set(capPropId('FRAME_WIDTH'), 800)
cam.set(capPropId('FRAME_HEIGHT'), 600)
cw = 800
ch = 600

# scale down by:
s = 2.0

cw = int(cw/s)
ch = int(ch/s)
print('Using video frame size %dx%d' % (cw,ch))


# init pan/tilt
print('initializing pan/tilt')

pan_center = 87.0
tilt_center = 130.0

sc.init_servo_control()
time.sleep(4)

pan = pan_center
tilt = tilt_center
sc.set_pan_tilt(pan,tilt)


frame_num = 1
try:
    print('starting tracking loop')
    consecutive_count = 0
    tracked_center = None
    frame_times = [datetime.now()]
    
    while True:
        ret, img = cam.read()
        img = cv2.resize(img,None,fx=.5, fy=.5)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        face_centers = [None]*len(faces) # center of detected faces in this frame
        face_diffs = [999.0]*len(faces)  # cartesian distance between set of detected faces and the one we're tracking
        fi = 0  # face index
        for (x,y,w,h) in faces:
            face_centers[fi] = (x+w/2, y+h/2)
            # if center is near tracked_center
            if tracked_center is not None:
                face_diffs[fi] = math.sqrt((face_centers[fi][0] - tracked_center[0])**2 + (face_centers[fi][1] - tracked_center[1])**2)
                #print('%d %f' % (fi,diff))
                            
            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
            #roi_gray = gray[y:y+h, x:x+w]
            #roi_color = img[y:y+h, x:x+w]
    
            fi += 1 # next face
    
        # which detected face was closest to the one we're tracking?
        if len(faces) > 0:
            if tracked_center is not None:
                closest_fi = argmin(face_diffs)
                if face_diffs[closest_fi] < 20.0:
                    tracked_center = face_centers[closest_fi]
                    consecutive_count += 1
                else:  # closest match is too far away, drop tracking
                    tracked_center = None
                    consecutive_count = 0
                    print('tracking lost - too far away')
            else:  # not currently tracking a face, so choose one to start tracking 
                # first for now.. make closest to center later..
                tracked_center = face_centers[0]
                print('starting to track')
        else:  # no faces detected, tracking lost
            if consecutive_count > 0:
                print('tracking lost - no faces detected')
            tracked_center = None
            consecutive_count = 0
    
    
        if consecutive_count > 0:
            #print('#:%d - %d,%d' % (consecutive_count, tracked_center[0], tracked_center[1]))
            cv2.rectangle(img,tracked_center,(tracked_center[0]+4,tracked_center[1]+4),(0,0,255),2)

            # move pan/tilt
            cdx = tracked_center[0] - cw/2
            cdy = tracked_center[1] - ch/2
          
            prev_pan = pan
            prev_tilt = tilt  

            if cdx < -10:
                pan += 1.0
            elif cdx > 10:
                pan -= 1.0

            if cdy < -8:
                tilt += 0.5
            elif cdy > 8:
                tilt -= 0.5
            

            # keep in reasonable ranges
            if pan < pan_center - 40.0:
                pan = pan_center - 40.0
                print('left limit')
            elif pan > pan_center + 40.0:
                pan = pan_center + 40
                print('right limit')
            if tilt < tilt_center - 25:
                tilt = tilt_center - 25
                print('bottom limit')
            elif tilt > tilt_center + 35:
                tilt = tilt_center + 35
                print('top limit')

            print('#:%d - %d,%d | d:%d,%d  pt:%d,%d' % (
                  consecutive_count, tracked_center[0], tracked_center[1],
                  int(cdx), int(cdy), int(pan), int(tilt)
            ))

            if prev_pan != pan or prev_tilt != tilt:
                sc.set_pan_tilt(pan, tilt)

        if frame_num % 5 == 0:
            cv2.imshow('img',img)

        ch = 0xFF & cv2.waitKey(1)
        if ch == 27 or ch == ord('q'):
            break

        frame_num += 1
        frame_times += [datetime.now()]


except Exception as e:
    print(e)
finally:
    cv2.destroyAllWindows()
    del cam
    # compute average FPS
    frame_durations = np.array(map(lambda dt1, dt2: (dt2-dt1).microseconds if dt2 is not None else np.nan, frame_times,frame_times[1:]))
    frame_durations = frame_durations[~np.isnan(frame_durations)]
    print('Average FPS: %.2f' % (1000000.0/np.mean(frame_durations)))

   