""" Scenario Description
Based on 2019 Carla Challenge Traffic Scenario 03.
Leading vehicle decelerates suddenly due to an obstacle and 
ego-vehicle must react, performing an emergency brake or an avoidance maneuver.
"""
import pickle
import sklearn
import numpy as np 
import os

param map = localPath('../../../tests/scenic/Town01.xodr')
param carla_map = 'Town01'
model scenic.simulators.newtonian.driving_model

#CONSTANTS
EGO_SPEED = 10
THROTTLE_ACTION = 0.6
BRAKE_ACTION = 1.0
EGO_TO_OBSTACLE = Range(-20, -15)
EGO_BRAKING_THRESHOLD = 10

monitor_model = None
if not globalParameters.monitor is None:
    monitor_model = globalParameters.monitor

#EGO BEHAVIOR: Follow lane and brake when reaches threshold distance to obstacle
behavior EgoBehavior(speed=10):   
    try:
        if monitor_model is None:
            do FollowLaneBehavior(speed)
        else:
            dist = self.distanceToClosest(Car)
            good = monitor_model.predict(np.array([[dist]]))
            if good:
                do FollowLaneBehavior(speed)
            else:
                do FollowLaneBehavior(speed/4)

    interrupt when withinDistanceToAnyObjs(self, EGO_BRAKING_THRESHOLD):
        take SetBrakeAction(BRAKE_ACTION)


#PLACEMENT
obstacle = new Car at 171.87 @ 2.04

ego = new Car following roadDirection from obstacle.position for EGO_TO_OBSTACLE,
    with behavior EgoBehavior(EGO_SPEED)

# record ego.position.x as ego_position_x
# record ego.position.y as ego_position_y
# record obstacle.position.x as obstacle_position_x
# record obstacle.position.y as obstacle_position_y
record ego.distanceToClosest(Car) as dist
record ego.speed as speed
