#
# Environment for Pan/Tilt Test Rig camera
#  (simple RC servo pan/tilt with USB camera)
#
# 'Motor' outputs are pan and tilt positions
# 'Sensors' are the x,y image coordinates of a detected face in the camera image
#            (and flag indicating if a face is detected or not)

import sys
import time
import random
import math
from rlglue.environment.Environment import Environment
from rlglue.environment import EnvironmentLoader as EnvironmentLoader
from rlglue.types import Observation
from rlglue.types import Action
from rlglue.types import Reward_observation_terminal

from datetime import datetime
import numpy as np
import cv2


import pantiltcontrol_rc_ard as sc


# utility
def argmin(l):
  return l.index(min(l))

from pkg_resources import parse_version
OPCV3 = parse_version(cv2.__version__) >= parse_version('3')

def capPropId(prop):
  return getattr(cv2 if OPCV3 else cv2.cv,
    ("" if OPCV3 else "CV_") + "CAP_PROP_" + prop)



class PanTiltCameraEnvironment(Environment):

    fn = 0  # camera 0

    # scale down by:
    s = 2.0

    show_img = True

    def __init__(self):
        self.face_in_view = 0  # False
        self.face_x = 0.
        self.face_y = 0.
        self.pan = 0
        self.tilt = 0

        # video image dimensions
        self.frame_w = 800
        self.frame_h = 600

        self.cw = int(self.frame_w/self.s)
        self.ch = int(self.frame_h/self.s)


    def env_init(self):

        print('Using video frame size %dx%d scaled to %dx%d' % (self.frame_w, self.frame_h, self.cw,self.ch))

        # Use standard OpenCV Haar Cascade face detector
        self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')
        assert not self.face_cascade.empty(), 'classifier loaded'

        self.cam = cv2.VideoCapture(self.fn)
        self.cam.set(capPropId('FRAME_WIDTH'), self.frame_w)
        self.cam.set(capPropId('FRAME_HEIGHT'), self.frame_h)

        # init pan/tilt
        print('initializing pan/tilt')

        self.pan_center = 87.0
        self.tilt_center = 130.0

        sc.init_servo_control()
        time.sleep(4)

        self.pan = self.pan_center
        self.tilt = self.tilt_center
        self.prev_pan = self.pan
        self.prev_tilt = self.tilt

        sc.set_pan_tilt(self.pan, self.tilt)

        return "VERSION RL-Glue-3.0 PROBLEMTYPE episodic DISCOUNTFACTOR 1.0 OBSERVATIONS DOUBLES (0 1) INTS (0) ACTIONS DOUBLES (0 1)  REWARDS (-1.0 1.0)  EXTRA Simple PanTilt camera environment."


    def env_start(self):
        self.face_in_view=0
        self.face_x = 0.
        self.face_y = 0.

        self.frame_num = 1
        self.consecutive_count = 0
        self.tracked_center = None
        self.frame_times = [datetime.now()]

        obs=Observation()
        obs.intArray=[self.face_in_view]
        obs.doubleArray=[self.face_x, self.face_y]

        return obs


    def env_step(self, action):

        self.pan = action.intArray[0]
        self.tilt = action.intArray[1]

        print('action: pan %d tilt %d' % (self.pan, self.tilt))

        # keep in reasonable ranges
        if self.pan < self.pan_center - 40.0:
            self.pan = self.pan_center - 40.0
            print('left limit')
        elif self.pan > self.pan_center + 40.0:
            self.pan = self.pan_center + 40
            print('right limit')
        if self.tilt < self.tilt_center - 25:
            self.tilt = self.tilt_center - 25
            print('bottom limit')
        elif self.tilt > self.tilt_center + 35:
            self.tilt = self.tilt_center + 35
            print('top limit')


        if self.prev_pan != self.pan or self.prev_tilt != self.tilt:
            sc.set_pan_tilt(self.pan, self.tilt)


        # Next video frame
        ret, img = self.cam.read()
        img = cv2.resize(img,(self.cw, self.ch))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # detect faces
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

        face_centers = [None]*len(faces) # center of detected faces in this frame
        face_diffs = [999.0]*len(faces)  # cartesian distance between set of detected faces and the one we're tracking
        fi = 0  # face index
        for (x,y,w,h) in faces:
            face_centers[fi] = (x+w/2, y+h/2)
            # if center is near tracked_center
            if self.tracked_center is not None:
                face_diffs[fi] = math.sqrt((face_centers[fi][0] - self.tracked_center[0])**2 + (face_centers[fi][1] - self.tracked_center[1])**2)
                #print('%d %f' % (fi,diff))

            cv2.rectangle(img,(x,y),(x+w,y+h),(255,0,0),2)
            #roi_gray = gray[y:y+h, x:x+w]
            #roi_color = img[y:y+h, x:x+w]

            fi += 1 # next face

        # which detected face was closest to the one we're tracking?
        if len(faces) > 0:
            if self.tracked_center is not None:
                closest_fi = argmin(face_diffs)
                if face_diffs[closest_fi] < 20.0:
                    self.tracked_center = face_centers[closest_fi]
                    self.consecutive_count += 1
                else:  # closest match is too far away, drop tracking
                    self.tracked_center = None
                    self.consecutive_count = 0
                    print('tracking lost - too far away')
            else:  # not currently tracking a face, so choose one to start tracking
                # first for now.. make closest to center later..
                self.tracked_center = face_centers[0]
                print('starting to track')
        else:  # no faces detected, tracking lost
            if self.consecutive_count > 0:
                print('tracking lost - no faces detected')
            self.tracked_center = None
            self.consecutive_count = 0


        if self.consecutive_count > 0:
            #print('#:%d - %d,%d' % (consecutive_count, tracked_center[0], tracked_center[1]))
            cv2.rectangle(img,self.tracked_center,(self.tracked_center[0]+4,self.tracked_center[1]+4),(0,0,255),2)
            self.face_in_view = 1
            self.face_x = self.tracked_center[0]
            self.face_y = self.tracked_center[1]
        else:
            self.face_in_view = 0


        if self.show_img and (self.frame_num % 5 == 0):
            cv2.imshow('img',img)


        # reward function
        #  currently just inverse of linear dist from face to center
        if self.face_in_view == 1:
            cdx = self.tracked_center[0] - self.cw/2
            cdy = self.tracked_center[1] - self.ch/2

            face_dist_to_center = math.sqrt(cdx**2 + cdy**2)
            max_dist = math.sqrt(self.cw**2 + self.ch**2)/2.  # 1/2 diag img dist

            reward = max_dist - face_dist_to_center
        else:
            reward = 0

        episode_over = 0

        ch = 0xFF & cv2.waitKey(1)
        if ch == 27 or ch == ord('q'):
            episode_over = 1

        obs = Observation()
        obs.intArray = [self.face_in_view]
        obs.doubleArray = [self.face_x, self.face_y]

        reward_obs_term = Reward_observation_terminal()
        reward_obs_term.r = reward
        reward_obs_term.o = obs
        reward_obs_term.terminal = episode_over
        if reward > 0:
            print('reward: %d' % reward)

        self.frame_num += 1
        self.frame_times += [datetime.now()]

        return reward_obs_term


    def env_cleanup(self):
        cv2.destroyAllWindows()
        del self.cam
        # compute average FPS
        frame_durations = np.array(map(lambda dt1, dt2: (dt2-dt1).microseconds if dt2 is not None else np.nan, self.frame_times,self.frame_times[1:]))
        frame_durations = frame_durations[~np.isnan(frame_durations)]
        print('Average FPS: %.2f' % (1000000.0/np.mean(frame_durations)))

    def env_message(self, message):
        print('got message:'+message)
        return '?'


if __name__=="__main__":
    EnvironmentLoader.loadEnvironment(PanTiltCameraEnvironment())
