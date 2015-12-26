# OpenCV show video

import os
import sys
import math
import datetime
import numpy as np
import cv2

from pkg_resources import parse_version
OPCV3 = parse_version(cv2.__version__) >= parse_version('3')

def capPropId(prop):
  return getattr(cv2 if OPCV3 else cv2.cv,
    ("" if OPCV3 else "CV_") + "CAP_PROP_" + prop)


# ELP-USB500W02M-L21 (OMNIVISION OV5640 COLOR CMOS SENSOR 2.1MM LENS)
# 2592x1944@ 15fps MJPEG / 2048x1536@ 15fps MJPEG
# 1600x1200@ 15fps MJPEG / 1920x1080@ 15fps MJPEG
# 1280x1024@15fps MJPEG/ 1280x720@ 30fps MJPEG
# 1024 x 768@ 30fps MJPEG/ 800 x 600@ 30fps MJPEG
# 640x480@ 30fps MJPEG /  320x240@ 30fps MJPEG

    
os.chdir(os.path.expanduser('~/Dropbox/Development/animoid/opencv'))

try:
    fn = sys.argv[1]
except:
    fn = 0

  
cam = cv2.VideoCapture(fn)

cam.set(capPropId('FRAME_WIDTH'), 800)
cam.set(capPropId('FRAME_HEIGHT'), 600)
#cam.set(capPropId('FPS'), 30.0)


# initial frame
ret, img = cam.read()
height, width, channels = img.shape
print('Resolution %dx%dx%d' % (width, height, channels))
ratio = float(width) / height

# compute display size to be no larger than 800 but keep aspect
if width > 800:
    display_width = 800
    display_height = int(height / (width/800.0))
else:
    display_width = width
    display_height = height
print('Displaying video with dimensions %dx%d' % (display_width, display_height))
    

img = cv2.resize(img,(display_width, display_height))
cv2.imshow('img',img)


print('Hit ESC to exit (from video window)')
print('Press v to enable video display')
show = False
start_time = datetime.datetime.now()
frame = 0
try:
    while True:
        ret, img = cam.read()
        frame += 1
        
        if show:
            img = cv2.resize(img,(display_width, display_height))
            cv2.imshow('img',img)
            
        if frame%15 == 0:
            time_span = datetime.datetime.now() - start_time
            if time_span.seconds > 0:
                print('FPS:%.2f' % (float(frame) / time_span.seconds))
            ch = 0xFF & cv2.waitKey(10)
        
            if ch == 27 or ch == ord('q'):  # ESC or 'q'uit
                break
            elif ch == ord('v'):
                show = not show
                print('video display %s' % ('on' if show else 'off'))
            
except Exception as e:
    print(e)
finally:
    cv2.destroyAllWindows()
    del cam


time_span = datetime.datetime.now() - start_time
print('FPS:%.2f' % (float(frame) / time_span.seconds))

   