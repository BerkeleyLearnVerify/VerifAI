""" Scenario Description
Based on 2019 Carla Challenge Traffic Scenario 03.
Leading vehicle decelerates suddenly due to an obstacle and 
ego-vehicle must react, performing an emergency brake or an avoidance maneuver.
"""
param map = localPath('../map/Town01.xodr')  # or other CARLA map that definitely works
param carla_map = 'Town01'
model scenic.simulators.newtonian.model

#CONSTANTS
EGO_SPEED = 10
THROTTLE_ACTION = 0.6
BRAKE_ACTION = 1.0
EGO_TO_OBSTACLE = Range(-20, -15)
EGO_BRAKING_THRESHOLD = 11

#EGO BEHAVIOR: Follow lane and brake when reaches threshold distance to obstacle
behavior EgoBehavior(speed=10):    
    try:
        do FollowLaneBehavior(speed)

    interrupt when withinDistanceToAnyObjs(self, EGO_BRAKING_THRESHOLD):
        take SetBrakeAction(BRAKE_ACTION)


#PLACEMENT
obstacle = Car at 171.87 @ 2.04

ego = Car following roadDirection from obstacle.position for EGO_TO_OBSTACLE,
    with behavior EgoBehavior(EGO_SPEED)
