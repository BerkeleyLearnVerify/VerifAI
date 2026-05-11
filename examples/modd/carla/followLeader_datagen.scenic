""" Scenario Description
The ego car follows the leader car maintaining a normal distance while lane keeping.
Some random noise is added to the movement of ego (both to the steering and speed) to collect diverse data.
The purpose is to generate data to train CNN controllers afterwards.
"""
from scenic.domains.driving.controllers import (
    PIDLateralController,
    PIDLongitudinalController,
)

param timeout = 30
param map = localPath('../../../tests/scenic/Town01.xodr')
param carla_map = 'Town01'
param render = 1

model scenic.simulators.carla.model

from followCarBehaviorMODD import FollowCarBehaviorMODD

#CONSTANTS
EGO_MODEL = "vehicle.tesla.model3"
LEADER_SPEED = Range(8,12)
EGO_SPEED = 5
THROTTLE_ACTION = 0.6
BRAKE_ACTION = 1.0
EGO_TO_LEADER = Range(-15, -10)
EGO_BRAKING_THRESHOLD = 10

#PLACEMENT
lane = Uniform(*network.lanes)
trajectory = [lane]
maneuver = Uniform(*lane.maneuvers)
trajectory += [maneuver.connectingLane, maneuver.endLane]


attrs = {"image_size_x": 640,
         "image_size_y": 320}

start = new OrientedPoint on lane.centerline
leader = new Car at start,
            with blueprint EGO_MODEL,
            with behavior FollowCarBehaviorMODD(target_speed=EGO_SPEED, addNoise=True),
            with color Color(0,0,0),
            with requireVisible True

ego = new Car following roadDirection from leader for EGO_TO_LEADER,
            with blueprint EGO_MODEL,
            with behavior FollowCarBehaviorMODD(target_speed=EGO_SPEED, leaderCar=leader, addNoise=True),
            with cte 0,
            with sensors {"front_rgb": RGBSensor(offset=(0, 2, 1), attributes=attrs)} 




require distance to intersection > 10 
require distance from leader to intersection > 10 

record ego.position.x as ego_position_x
record ego.position.y as ego_position_y






record ego.distanceToClosest(Car) every 0.2 seconds after 3 seconds to "dist.npz"
record ego.speed every 0.2 seconds after 3 seconds to "speed.npz"
record leader.speed every 0.2 seconds after 3 seconds to "leader_speed.npz"
record ego.cte every 0.2 seconds after 3 seconds to "cte.npz"
record ego.observations["front_rgb"] every 0.2 seconds after 3 seconds to "front_rgb_{time:.1f}.jpg"


terminate when ((leader.speed < 0.1 or ego.speed < 0.1) and (distance to start) > 1) 
