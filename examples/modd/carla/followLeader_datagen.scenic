""" Scenario Description
The ego car follows the leader car maintaining a normal distance while lane keeping.
"""
import pickle
import sklearn
import numpy as np 
import random
import os 
import re
from scenic.domains.driving.controllers import (
    PIDLateralController,
    PIDLongitudinalController,
)


param timeout = 30
param map = localPath('../../../tests/scenic/Town01.xodr')
param carla_map = 'Town01'
param render = 1

model scenic.simulators.carla.model

#CONSTANTS
EGO_MODEL = "vehicle.tesla.model3"
LEADER_SPEED = Range(8,12)
EGO_SPEED = 5
THROTTLE_ACTION = 0.6
BRAKE_ACTION = 1.0
EGO_TO_LEADER = Range(-15, -10)
EGO_BRAKING_THRESHOLD = 10


behavior FollowLaneBehaviorModified(target_speed = 10, laneToFollow=None, is_oppositeTraffic=False, leaderCar=None):
    """ 
    Follow's the lane on which the vehicle is at, unless the laneToFollow is specified.
    Once the vehicle reaches an intersection, by default, the vehicle will take the straight route.
    If straight route is not available, then any availble turn route will be taken, uniformly randomly. 
    If turning at the intersection, the vehicle will slow down to make the turn, safely. 

    This behavior does not terminate. A recommended use of the behavior is to accompany it with condition,
    e.g. do FollowLaneBehavior() until ...

    :param target_speed: Its unit is in m/s. By default, it is set to 10 m/s
    :param laneToFollow: If the lane to follow is different from the lane that the vehicle is on, this parameter can be used to specify that lane. By default, this variable will be set to None, which means that the vehicle will follow the lane that it is currently on.
    """

    past_steer_angle = 0
    past_speed = 0 # making an assumption here that the agent starts from zero speed
    if laneToFollow is None:
        current_lane = self.lane
    else:
        current_lane = laneToFollow

    current_centerline = current_lane.centerline
    in_turning_lane = False # assumption that the agent is not instantiated within a connecting lane
    intersection_passed = False
    entering_intersection = False # assumption that the agent is not instantiated within an intersection
    end_lane = None
    original_target_speed = target_speed
    TARGET_SPEED_FOR_TURNING = 3 # KM/H
    TRIGGER_DISTANCE_TO_SLOWDOWN = 10 # FOR TURNING AT INTERSECTIONS

    if current_lane.maneuvers != ():
        nearby_intersection = current_lane.maneuvers[0].intersection
        if nearby_intersection == None:
            nearby_intersection = current_lane.centerline[-1]
    else:
        nearby_intersection = current_lane.centerline[-1]
    
    # instantiate longitudinal and lateral controllers
    _lon_controller, _lat_controller = simulation().getLaneFollowingControllers(self)

    while True:

        if self.speed is not None:
            current_speed = self.speed
        else:
            current_speed = past_speed

        if not entering_intersection and (distance from self.position to nearby_intersection) < TRIGGER_DISTANCE_TO_SLOWDOWN:
            entering_intersection = True
            intersection_passed = False
            
            if distance from self to intersection < TRIGGER_DISTANCE_TO_SLOWDOWN:
                if leaderCar is None:
                    maneuvers = current_lane.maneuvers
                    select_maneuver = Uniform(*maneuvers)
                    self.select_maneuver = select_maneuver
                    print(self.select_maneuver)
                else:
                    select_maneuver = leaderCar.select_maneuver

            elif len(current_lane.maneuvers) > 0:
                select_maneuver = Uniform(*current_lane.maneuvers)
                print(select_maneuver)
            else:
                take SetBrakeAction(1.0)
                break

            # print(select_maneuver.type)

            # assumption: there always will be a maneuver
            if select_maneuver.connectingLane != None:
                current_centerline = concatenateCenterlines([current_centerline, select_maneuver.connectingLane.centerline, \
                    select_maneuver.endLane.centerline])
            else:
                current_centerline = concatenateCenterlines([current_centerline, select_maneuver.endLane.centerline])

            current_lane = select_maneuver.endLane
            end_lane = current_lane

            if current_lane.maneuvers != ():
                nearby_intersection = current_lane.maneuvers[0].intersection
                if nearby_intersection == None:
                    nearby_intersection = current_lane.centerline[-1]
            else:
                nearby_intersection = current_lane.centerline[-1]

            if select_maneuver.type != ManeuverType.STRAIGHT:
                in_turning_lane = True
                target_speed = TARGET_SPEED_FOR_TURNING

                # do TurnBehavior(trajectory = current_centerline, target_speed=target_speed)
                trajectory = current_centerline
                target_speed = target_speed
                if isinstance(trajectory, PolylineRegion):
                    trajectory_centerline = trajectory
                else:
                    trajectory_centerline = concatenateCenterlines([traj.centerline for traj in trajectory])

                # instantiate longitudinal and lateral controllers
                # _lon_controller, _lat_controller = simulation().getTurningControllers(self)
                dt = simulation().timestep
                _lon_controller = PIDLongitudinalController(K_P=0.5, K_D=0.1, K_I=0.7, dt=dt)
                _lat_controller = PIDLateralController(K_P=0.8, K_D=0.6, K_I=0.0, dt=dt)

                past_steer_angle = 0

                while self in network.intersectionRegion:
                    if self.speed is not None:
                        current_speed = self.speed
                    else:
                        current_speed = 0

                    cte = trajectory_centerline.signedDistanceTo(self.position)
                    speed_error = target_speed - current_speed

                    # compute throttle : Longitudinal Control
                    throttle = _lon_controller.run_step(speed_error)

                    # compute steering : Latitudinal Control
                    current_steer_angle = _lat_controller.run_step(cte)

                    take RegulatedControlAction(throttle, current_steer_angle, past_steer_angle)
                    past_steer_angle = current_steer_angle


        if (end_lane is not None) and (self.position in end_lane) and not intersection_passed:
            intersection_passed = True
            in_turning_lane = False
            entering_intersection = False 
            target_speed = original_target_speed
            # _lon_controller, _lat_controller = simulation().getLaneFollowingControllers(self)
            dt = simulation().timestep
            _lon_controller = PIDLongitudinalController(K_P=0.5, K_D=0.1, K_I=0.7, dt=dt)
            _lat_controller = PIDLateralController(K_P=0.2, K_D=0.5, K_I=0.0, dt=dt)

        nearest_line_points = current_centerline.nearestSegmentTo(self.position)
        nearest_line_segment = PolylineRegion(nearest_line_points)
        self.cte = nearest_line_segment.signedDistanceTo(self.position)
        if is_oppositeTraffic:
            self.cte = -self.cte

        #if leaderCar:
        #    print(self.cte)
        speed_error = target_speed - current_speed

        #if leaderCar:
        #     speed_error += random.randrange(-2,2)

        # compute throttle : Longitudinal Control
        throttle = _lon_controller.run_step(speed_error)

        # compute steering : Lateral Control
        # if distance from self to intersection < TRIGGER_DISTANCE_TO_SLOWDOWN:
        #     print("Entering intersection?")
        #     print(len(current_lane.maneuvers))
        #    self.cte = 0
        current_steer_angle = _lat_controller.run_step(self.cte) 

        if leaderCar:
            # current_steer_angle += 1/2 * random.randrange(-1,2) * random.random()
            if distance from self to leaderCar > 10:
                throttle = 0.6
            if distance from self to leaderCar < 4:
                take SetBrakeAction(1.0)
        

        

        take RegulatedControlAction(throttle, current_steer_angle, past_steer_angle)
        past_steer_angle = current_steer_angle
        past_speed = current_speed



#EGO BEHAVIOR: Follow lane and brake when reaches threshold distance to obstacle
behavior EgoBehavior(speed, leader, leaderCar=None): 
    try:
        do FollowLaneBehaviorModified(target_speed=speed)

    interrupt when self._intersection:
        if leader:
            maneuvers = self._intersection.maneuversAt(self.position)
            select_maneuver = Uniform(maneuvers)
            if maneuver.connectingLane:
                self.trajectory = [maneuver.startLane, maneuver.connectingLane, maneuver.endLane]
            else:
                self.trajectory = [maneuver.startLane, maneuver.endLane]
            #print(maneuver.type)
            do FollowTrajectoryBehavior(trajectory=self.trajectory, target_speed=EGO_SPEED)
        else:
            do FollowTrajectoryBehavior(trajectory=leaderCar.trajectory, target_speed=EGO_SPEED)

#PLACEMENT
lane = Uniform(*network.lanes)
trajectory = [lane]
#for _ in range(1):
maneuver = Uniform(*lane.maneuvers)
trajectory += [maneuver.connectingLane, maneuver.endLane]


attrs = {"image_size_x": 640,
         "image_size_y": 320}

start = new OrientedPoint on lane.centerline
leader = new Car at start,
            with blueprint EGO_MODEL,
            with behavior FollowLaneBehaviorModified(target_speed=EGO_SPEED),
            with color Color(0,0,0) 

ego = new Car following roadDirection from leader.position for EGO_TO_LEADER,
            with blueprint EGO_MODEL,
            with behavior FollowLaneBehaviorModified(target_speed=EGO_SPEED, leaderCar=leader),
            with cte 0,
            with sensors {"front_rgb": RGBSensor(offset=(0, 2, 1), attributes=attrs)
                        } 




require distance to intersection > 10 and distance from leader to intersection > 10 and ego can see leader

record ego.position.x as ego_position_x
record ego.position.y as ego_position_y
record obstacle.position.x as obstacle_position_x
record obstacle.position.y as obstacle_position_y






record ego.distanceToClosest(Car) every 0.2 seconds after 3 seconds to "dist.npz"
record ego.speed every 0.2 seconds after 3 seconds to "speed.npz"
record leader.speed every 0.2 seconds after 3 seconds to "leader_speed.npz"
record ego.cte every 0.2 seconds after 3 seconds to "cte.npz"
record ego.observations["front_rgb"] every 0.2 seconds after 3 seconds to "front_rgb_{time:.1f}.jpg"


terminate when ((leader.speed < 0.1 or ego.speed < 0.1) and (distance to start) > 1) 
