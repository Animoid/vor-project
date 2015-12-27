
import sys

import rlglue.RLGlue as RLGlue

whichEpisode=0

def runEpisode(stepLimit):
    global whichEpisode
    terminal=RLGlue.RL_episode(stepLimit)
    totalSteps=RLGlue.RL_num_steps()
    totalReward=RLGlue.RL_return()

    print "Episode "+str(whichEpisode)+"\t "+str(totalSteps)+ " steps \t" + str(totalReward) + " total reward\t " + str(terminal) + " natural end"

    whichEpisode=whichEpisode+1

#Main Program starts here

print "\n\nStarting face saccade experiment."
taskSpec = RLGlue.RL_init()
print "Environment task spec: " + taskSpec

runEpisode(0)

totalSteps = RLGlue.RL_num_steps()
totalReward = RLGlue.RL_return()
print "Steps:" + str(totalSteps) + "; Total reward: " + str(totalReward)
RLGlue.RL_cleanup()
