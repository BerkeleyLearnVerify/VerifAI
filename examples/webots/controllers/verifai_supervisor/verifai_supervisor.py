from verifai.simulators.webots.webots_task import webots_task
from verifai.simulators.webots.client_webots import ClientWebots
try:
    from controller import Supervisor
except ModuleNotFoundError:
    import sys
    sys.exit('This functionality requires webots to be installed')

from dotmap import DotMap
import numpy as np

import math  
import sys
sys.path.append('../driver')
from driver import Driver

DEBUG = True

def getRobotSampleXYTh(robot):
    translationValues = robot.getField('translation').getSFVec3f()
    rotationValues = robot.getField('rotation').getSFRotation()
    xyth = (translationValues[0], translationValues[2], rotationValues[3])
    return xyth


# Defining the task as a webots task
class simpleWebotsTask(webots_task):
    collision = []

    def __init__(self, N_SIM_STEPS, supervisor):
        super().__init__(N_SIM_STEPS, supervisor)
        self.robot1 = self.supervisor.getFromDef('ROBOT1')
        self.robot2 = self.supervisor.getFromDef('ROBOT2')
        self.robot3 = self.supervisor.getFromDef('ROBOT3')

        self.getSampleTraj()
        return
        

    def getSampleTraj(self):
        # time stamp
        timeStamp = self.supervisor.getTime()
        robot1xyth = getRobotSampleXYTh(self.robot1)
        robot2xyth = getRobotSampleXYTh(self.robot2)
        robot3xyth = getRobotSampleXYTh(self.robot3)
        
        dist12 = math.sqrt((robot2xyth[0] - robot1xyth[0])**2 + (robot2xyth[1] - robot1xyth[1])**2)
        dist13 = math.sqrt((robot3xyth[0] - robot1xyth[0])**2 + (robot3xyth[1] - robot1xyth[1])**2)
        dist23 = math.sqrt((robot3xyth[0] - robot2xyth[0])**2 + (robot3xyth[1] - robot2xyth[1])**2)
        minDist = min(dist12, dist13, dist23)

        if DEBUG:
            print('time is ' + str(timeStamp))
            print('robot1 is located at ' + str(robot1xyth))
            print('robot2 is located at ' + str(robot2xyth))
            print('robot3 is located at ' + str(robot3xyth))
            
        self.collision.append( (timeStamp, minDist ) )
        return


    def use_sample(self, sample):
        print('Sample recieved')
        print(sample)

        cPos = self.robot1.getField('translation').getSFVec3f()
        sPos = sample.control_params.ROBOT1pos
        self.robot1.getField('translation').setSFVec3f([sPos[0], cPos[1], sPos[1]])

        cPos = self.robot2.getField('translation').getSFVec3f()
        sPos = sample.control_params.ROBOT2pos
        self.robot2.getField('translation').setSFVec3f([sPos[0], cPos[1], sPos[1]])
        
        cPos = self.robot3.getField('translation').getSFVec3f()
        sPos = sample.control_params.ROBOT3pos
        self.robot3.getField('translation').setSFVec3f([sPos[0], cPos[1], sPos[1]])

        self.dt = 0.032
        return

    def run_task(self, sample):
        print("Runing Task")

        self.use_sample(sample)
        self.supervisor.initialization()

        #who manage time step is not clear. Supervisor or webots_task?
        while self.supervisor.step(self.supervisor.timeStep) != -1:
            self.getSampleTraj()

            if self.supervisor.getTime()>= self.N_SIM_STEPS*self.dt:
                break

        print("Finish")

        # Saving necessary trajectories for monitor
        sim_results = {
            'collision': self.collision,
        }

        return sim_results


PORT = 8888
BUFSIZE = 4096
N_SIM_STEPS = 50
supervisor = Driver()
simulation_data = DotMap()
simulation_data.port = PORT
simulation_data.bufsize = BUFSIZE
simulation_data.task = simpleWebotsTask(N_SIM_STEPS=N_SIM_STEPS, supervisor=supervisor)
client_task = ClientWebots(simulation_data)
if not client_task.run_client():
    print("End of simulations")
    #supervisor.simulationQuit(True) #this code leads miss open webot world.
    #supervisor.simulationReset()
    supervisor.simulationSetMode(supervisor.SIMULATION_MODE_PAUSE)