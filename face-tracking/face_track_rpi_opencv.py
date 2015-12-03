# OpenCV Face detection 

import os
import sys
import math
import numpy as np
import cv2
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
from datetime import datetime

os.chdir(os.path.expanduser('~/dev/picam'))

import pantiltcontrol_rc_ard as sc

# camera resolution
cw=1280
ch=720

# scale down by:
s = 3.0

cw = int(cw/s)
ch = int(ch/s)
print('Using video frame size %dx%d' % (cw,ch))

# utility
def argmin(l):
  return l.index(min(l))
  
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')
assert not face_cascade.empty(), 'classifier loaded'

camera = PiCamera()
camera.resolution = (cw,ch)
camera.framerate = 16
rawCapture = PiRGBArray(camera, size=(cw,ch))
time.sleep(.1)

# init pan/tilt
print('initializing pan/tilt')

pan_center = 87.0
tilt_center = 110.0

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
    for frame in camera.capture_continuous(rawCapture, format='bgr', use_video_port=True):
	img = frame.array
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	img = cv2.flip(img, 0) # Pi CAM is 'up-side-down'
        faces = face_cascade.detectMultiScale(img, 1.3, 5)
        
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
            cv2.rectangle(img,tracked_center,(tracked_center[0]+4,tracked_center[1]+4),(0,0,255),2)

            # move pan/tilt
            cdx = tracked_center[0] - cw/2
            cdy = tracked_center[1] - ch/2
          
            prev_pan = pan
            prev_tilt = tilt  

            if cdx < -10:
                pan -= 1.0
            elif cdx > 10:
                pan += 1.0

            if cdy < -8:
                tilt += 0.5
            elif cdy > 8:
                tilt -= 0.5
            

            # keep in reasonable ranges
            if pan < pan_center - 20.0:
                pan = pan_center - 20.0
            elif pan > pan_center + 20.0:
                pan = pan_center + 20
            if tilt < tilt_center - 15:
                tilt = tilt_center - 15
            elif tilt > tilt_center + 15:
                tilt = tilt_center + 15

            print('#:%d - %d,%d | d:%d,%d  pt:%d,%d' % (
                  consecutive_count, tracked_center[0], tracked_center[1],
                  int(cdx), int(cdy), int(pan), int(tilt)
            ))

            if prev_pan != pan or prev_tilt != tilt:
                sc.set_pan_tilt(pan, tilt)

        if frame_num % 5 == 0:
            cv2.imshow('img',img)
        
	rawCapture.truncate(0)

        ch = 0xFF & cv2.waitKey(1)
        if ch == 27:
            break

        frame_num += 1
	frame_times += [datetime.now()]


except Exception as e:
    print(e)
finally:
    cv2.destroyAllWindows()
    # compute average FPS
    frame_durations = np.array(map(lambda dt1, dt2: (dt2-dt1).microseconds if dt2 is not None else np.nan, frame_times,frame_times[1:]))
    frame_durations = frame_durations[~np.isnan(frame_durations)]
    print('Average FPS: %.2f' % (1000000.0/np.mean(frame_durations)))



