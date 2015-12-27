import random
import sys
import copy
from rlglue.agent.Agent import Agent
from rlglue.agent import AgentLoader as AgentLoader
from rlglue.types import Action
from rlglue.types import Observation

from random import Random

class SingleEyeAgent(Agent):

    rand_generator = Random()
    # scale down by:
    s = 2.0

    def __init__(self):
        self.last_action = Action()
        self.last_observation = Observation()

        # video image dimensions
        self.cw = 800
        self.ch = 600

        self.cw = int(self.cw/self.s)
        self.ch = int(self.ch/self.s)

        self.pan_center = 87.0
        self.tilt_center = 130.0


    def agent_init(self, task_spec):
        self.last_action = Action()
        self.last_observation = Observation()

        self.pan = self.pan_center
        self.tilt = self.tilt_center


    def agent_start(self, observation):

        action=Action()
        action.intArray=[self.pan, self.tilt]

        self.last_action=copy.deepcopy(action)
        self.last_observation=copy.deepcopy(observation)

        return action


    def agent_step(self, reward, observation):

        face_in_view = observation.intArray[0]
        face_x = observation.doubleArray[0]
        face_y = observation.doubleArray[1]

        if face_in_view:
            print('got face %d, %d' % (face_x, face_y))
            # move pan/tilt
            cdx = face_x - self.cw/2
            cdy = face_y - self.ch/2

            self.prev_pan = self.pan
            self.prev_tilt = self.tilt

            if cdx < -10:
                self.pan += 1.0
            elif cdx > 10:
                self.pan -= 1.0

            if cdy < -8:
                self.tilt += 0.5
            elif cdy > 8:
                self.tilt -= 0.5


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
                tilt = self.tilt_center + 35
                print('top limit')
        else:
            print('no face in view')

        action=Action()
        action.intArray=[self.pan, self.tilt]

        self.last_action=copy.deepcopy(action)
        self.last_observation=copy.deepcopy(observation)

        return action


    def agent_end(self,reward):
        pass

    def agent_cleanup(self):
        pass

    def agent_message(self, message):
        print('got agent message:'+message)
        return '?'


if __name__=="__main__":
    AgentLoader.loadAgent(SingleEyeAgent())
    
