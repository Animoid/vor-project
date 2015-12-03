# OpenCV Face detection test

import os
import sys
import math
import numpy as np
import cv2


os.chdir(os.path.expanduser('~/Dropbox/Development/animoid/opencv'))

try:
    fn = sys.argv[1]
except:
    fn = 0

# utility
def argmin(l):
  return l.index(min(l))
  
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')
assert not face_cascade.empty(), 'classifier loaded'

cam = cv2.VideoCapture(fn)

try:
    consecutive_count = 0
    prev_center = None
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
            # if center is near prev_center
            if prev_center is not None:
                face_diffs[fi] = math.sqrt((face_centers[fi][0] - prev_center[0])**2 + (face_centers[fi][1] - prev_center[1])**2)
                #print('%d %f' % (fi,diff))
                            
            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
            #roi_gray = gray[y:y+h, x:x+w]
            #roi_color = img[y:y+h, x:x+w]
    
            fi += 1 # next face
    
        # which detected face was closest to the one we're tracking?
        if len(faces) > 0:
            if prev_center is not None:
                closest_fi = argmin(face_diffs)
                if face_diffs[closest_fi] < 20.0:
                    prev_center = face_centers[closest_fi]
                    consecutive_count += 1
                else:  # closest match is too far away, drop tracking
                    prev_center = None
                    consecutive_count = 0
                    print('tracking lost - too far away')
            else:  # not currently tracking a face, so choose one to start tracking 
                # first for now.. make closest to center later..
                prev_center = face_centers[0]
                print('starting to track')
        else:  # no faces detected, tracking lost
            if consecutive_count > 0:
                print('tracking lost - no faces detected')
            prev_center = None
            consecutive_count = 0
    
    
        if consecutive_count > 0:
            print('#:%d - %d,%d' % (consecutive_count, prev_center[0], prev_center[1]))
            cv2.rectangle(img,prev_center,(prev_center[0]+4,prev_center[1]+4),(0,0,255),2)

        cv2.imshow('img',img)
        
        ch = 0xFF & cv2.waitKey(1)
        if ch == 27:
            break
except Exception as e:
    print(e)
finally:
    cv2.destroyAllWindows()
    del cam

   