""" Scenario Description
The ego car follows the leader car maintaining a normal distance while lane keeping.
"""

import warnings
warnings.filterwarnings("ignore") 

import pickle
import sklearn
import numpy as np 
import random
import os
import re
import torch

import pandas as pd
import torch
import torchvision
import sys
import cv2
from scenic.domains.driving.controllers import (
    PIDLateralController,
    PIDLongitudinalController,
)

if globalParameters.seed != "":
    random.seed(globalParameters.seed)
    np.random.seed(globalParameters.seed)

torch.set_default_device('cuda')

class resNet(torch.nn.Module):
    """
    Use restnet from torchvision
    """

    def __init__(self, layers="18", pre_trained=False):
        super(resNet, self).__init__()
        if layers == "18":
            self.model = torchvision.models.resnet18(pretrained=pre_trained)
        else:
            raise NotImplementedError

    def forward(self, x):
        return self.model(x)
        

class CNN(torch.nn.Module):
    def __init__(self, resnet=False, pretrained=False):
        super(CNN, self).__init__()
        if resnet:
            self.model = resNet(pre_trained=pretrained)
        else:
            raise NotImplementedError
        self.fc1 = torch.nn.Linear(1000,1024)
        self.head = torch.nn.Linear(1024, 2)
        
    def forward(self, x):
        x = self.model(x)
        x = self.fc1(x)
        h = self.head(x)
        return h


param timeout = 180
param map = localPath('../../../tests/scenic/Town01.xodr')
param carla_map = 'Town01'
param timeBound = 300


model scenic.simulators.carla.model

#CONSTANTS
EGO_MODEL = "vehicle.tesla.model3"
# Old speed before TimeSeries:
LEADER_SPEED = TimeSeries(VerifaiRange(6,8))
EGO_SPEED = 3
THROTTLE_ACTION = 0.5
BRAKE_ACTION = 1.0
EGO_TO_LEADER = Range(-15, -10)
EGO_BRAKING_THRESHOLD = 6
EGO_ACCELERATION_THRESHOLD = 10

monitor_model = None
if globalParameters.monitor != "":
    with open(globalParameters.monitor, 'rb') as f:
        monitor_model = pickle.load(f) 
   
    


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
        if leaderCar:
            current_lane = leaderCar.lane
        else:
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
    TRIGGER_DISTANCE_TO_SLOWDOWN = 20 # FOR TURNING AT INTERSECTIONS

    if current_lane.maneuvers != ():
        nearby_intersection = current_lane.maneuvers[0].intersection
        if nearby_intersection == None:
            nearby_intersection = current_lane.centerline[-1]
    else:
        nearby_intersection = current_lane.centerline[-1]
    
    # instantiate longitudinal and lateral controllers
    _lon_controller, _lat_controller = simulation().getLaneFollowingControllers(self)

    if leaderCar is None:
        self.steps_speed = 0
    else: 
        steps_running = 0

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
                    turn_maneuvers = filter(lambda i : i.type != ManeuverType.STRAIGHT, maneuvers)
                    if len(turn_maneuvers) > 0:
                        select_maneuver = Uniform(*turn_maneuvers)
                        self.turn_maneuver = select_maneuver
                    else:
                        select_maneuver = Uniform(*maneuvers) 
                    self.select_maneuver = select_maneuver
                else:
                    select_maneuver = leaderCar.turn_maneuver

            elif len(current_lane.maneuvers) > 0:
                select_maneuver = Uniform(*current_lane.maneuvers)
            else:
                take SetBrakeAction(1.0)
                break


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
                if leaderCar is None:
                    self.turn_centerline = current_centerline
                else:
                    current_centerline = leaderCar.turn_centerline


                in_turning_lane = True
                target_speed = TARGET_SPEED_FOR_TURNING

                trajectory = current_centerline
                target_speed = target_speed
                if isinstance(trajectory, PolylineRegion):
                    trajectory_centerline = trajectory
                else:
                    trajectory_centerline = concatenateCenterlines([traj.centerline for traj in trajectory])
                
                dt = simulation().timestep
                _lon_controller = PIDLongitudinalController(K_P=0.5, K_D=0.1, K_I=0.7, dt=dt)
                _lat_controller = PIDLateralController(K_P=0.8, K_D=0.6, K_I=0.0, dt=dt)

                past_steer_angle = 0

                while distance from self to intersection < TRIGGER_DISTANCE_TO_SLOWDOWN:
                    if self.speed is not None:
                        current_speed = self.speed
                    else:
                        current_speed = 0

                    self.cte = trajectory_centerline.signedDistanceTo(self.position)

                    speed_error = target_speed - current_speed

                    # compute throttle : Longitudinal Control
                    throttle = _lon_controller.run_step(speed_error)

                    # compute steering : Latitudinal Control
                    current_steer_angle = _lat_controller.run_step(self.cte)


                    take RegulatedControlAction(throttle, current_steer_angle, past_steer_angle)
                    past_steer_angle = current_steer_angle

                    
                    if leaderCar is None:
                        self.steps_speed += 1
                        if self.steps_speed > 20:
                            original_target_speed = LEADER_SPEED.getSample()
                            self.steps_speed = 0
                    else:
                        steps_running += 1

                    if leaderCar and monitor_model and steps_running > 80:
                        # Input format: (weather, np.array([r,g,b, distIntersection, distObstacle, visibleObstacle, visibleLeader]))
                        distIntersection = distance from self to intersection
                        distObstacle = distance from self to obstacle
                        visibleObstacle = int(ego can see obstacle)
                        visibleLeader = int(ego can see leader)

                        input_features = np.concatenate((self.weather, np.array([self.r,self.g,self.b, distIntersection, distObstacle, visibleObstacle, visibleLeader])))
                        input_features = np.expand_dims(input_features, axis=0)
                        self.isSafe = monitor_model.predict(input_features)[0]


        if (end_lane is not None) and (self.position in end_lane) and not intersection_passed:
            intersection_passed = True
            in_turning_lane = False
            entering_intersection = False 
            target_speed = original_target_speed
            dt = simulation().timestep
            _lon_controller = PIDLongitudinalController(K_P=0.5, K_D=0.1, K_I=0.7, dt=dt)
            _lat_controller = PIDLateralController(K_P=0.2, K_D=0.1, K_I=0.0, dt=dt)

        nearest_line_points = current_centerline.nearestSegmentTo(self.position)
        nearest_line_segment = PolylineRegion(nearest_line_points)
        self.cte = nearest_line_segment.signedDistanceTo(self.position)
        if is_oppositeTraffic:
            self.cte = -self.cte

        speed_error = target_speed - current_speed


        # compute throttle : Longitudinal Control
        throttle = _lon_controller.run_step(speed_error)

        # compute steering : Lateral Control
        current_steer_angle = _lat_controller.run_step(self.cte) 
        
        if leaderCar:
            if distance from self to leaderCar < EGO_BRAKING_THRESHOLD:
                take SetBrakeAction(1.0)


        take RegulatedControlAction(throttle, current_steer_angle, past_steer_angle)
        past_steer_angle = current_steer_angle
        past_speed = current_speed

        
        if leaderCar is None:
            self.steps_speed += 1
            if self.steps_speed > 20:
                original_target_speed = LEADER_SPEED.getSample()
                self.steps_speed = 0
            
        else:
            steps_running += 1

        if leaderCar and monitor_model and steps_running > 80:
            distIntersection = distance from self to intersection
            distObstacle = distance from self to obstacle
            visibleObstacle = int(ego can see obstacle)
            visibleLeader = int(ego can see leader)

            input_features = np.concatenate((self.weather, np.array([self.r,self.g,self.b, distIntersection, distObstacle, visibleObstacle, visibleLeader])))
            input_features = np.expand_dims(input_features, axis=0)
            self.isSafe = monitor_model.predict(input_features)[0]





behavior EgoBehavior(target_speed = 10, controller_path = None, leaderCar=None, obstacleCar=None):
    if monitor_model is None:
        do ControllerBehavior(target_speed, controller_path, leaderCar)
    else:
        try:
            do ControllerBehavior(target_speed=target_speed, controller_path=controller_path, leaderCar=leaderCar, obstacleCar=obstacleCar)
        interrupt when not self.isSafe:
            print("-- Monitor: Not safe! Switching to SafeBehavior.")
            take SetBrakeAction(1.0)
            do EgoBehavior2(target_speed = target_speed, controller_path = controller_path, leaderCar=leaderCar, obstacleCar=obstacleCar)

behavior EgoBehavior2(target_speed = 10, controller_path = None, leaderCar=None, obstacleCar=None):
    try:
        do FollowLaneBehaviorModified(target_speed=target_speed, leaderCar=leader)
    interrupt when self.isSafe:
        print("-- Monitor: Safe! Switching back to CNN Controller.")
        do EgoBehavior(target_speed=target_speed, controller_path=controller_path, leaderCar=leaderCar, obstacleCar=obstacleCar)



behavior ControllerBehavior(target_speed = 10, controller_path = None, leaderCar=None, obstacleCar=None):
    TARGET_SPEED_FOR_TURNING = 3 # KM/H

    past_steer_angle = 0
    past_speed = 0 # making an assumption here that the agent starts from zero speed

    original_target_speed = target_speed

    current_lane = self.lane
    nearby_intersection = current_lane.centerline[-1]

    
    # instantiate longitudinal and lateral controllers
    dt = simulation().timestep
    _lon_controller = PIDLongitudinalController(K_P=0.5, K_D=0.1, K_I=0.7, dt=dt)
    _lat_controller_turn = PIDLateralController(K_P=0.8, K_D=0.2, K_I=0.0, dt=dt)
    _lat_controller_straight = PIDLateralController(K_P=0.2, K_D=0.1, K_I=0.0, dt=dt)

    # instantiate model
    controller = CNN(resnet=True)
    controller.cuda()
    controller.load_state_dict(torch.load(controller_path))
    controller.eval()

    # Features for monitor
    if monitor_model:
        color = obstacle.color
        self.r,self.g,self.b = color.r, color.g, color.b
        self.weather = np.array([
            self.carlaActor.get_world().get_weather().cloudiness,
            self.carlaActor.get_world().get_weather().precipitation,
            self.carlaActor.get_world().get_weather().precipitation_deposits,
            self.carlaActor.get_world().get_weather().wind_intensity,
            self.carlaActor.get_world().get_weather().sun_azimuth_angle,
            self.carlaActor.get_world().get_weather().sun_altitude_angle,
            self.carlaActor.get_world().get_weather().fog_density,
            self.carlaActor.get_world().get_weather().fog_distance,
            self.carlaActor.get_world().get_weather().wetness,
            self.carlaActor.get_world().get_weather().fog_falloff,
            self.carlaActor.get_world().get_weather().scattering_intensity,
            self.carlaActor.get_world().get_weather().mie_scattering_scale,
            self.carlaActor.get_world().get_weather().rayleigh_scattering_scale,
            self.carlaActor.get_world().get_weather().dust_storm  
        ])

    while True:
        front_img = self.sensors["front_rgb"]._lastObservation
        if isinstance(front_img, np.ndarray):
            front_img = front_img[80:160, 40:600,:] / 255
            _dot = controller(torch.Tensor(front_img).permute(2,0,1).unsqueeze(0).cuda())
            _dot = _dot.cpu().detach().numpy()[0]
            cte_pred, dist_pred = _dot[0].item(), _dot[1].item() * 30
        else:
            cte_pred, dist_pred = 0, 0

        if self.speed is not None:
            current_speed = self.speed
        else:
            current_speed = past_speed

        speed_error = target_speed - current_speed


        # compute throttle : Longitudinal Control
        throttle = _lon_controller.run_step(speed_error)

        # compute steering : Lateral Control
        if abs(cte_pred) > 0.5: 
            _lat_controller = _lat_controller_turn
        else:
            _lat_controller = _lat_controller_straight
        current_steer_angle = _lat_controller.run_step(cte_pred) 

        if dist_pred > EGO_ACCELERATION_THRESHOLD:
            throttle = THROTTLE_ACTION
        if dist_pred < EGO_BRAKING_THRESHOLD:
            take SetBrakeAction(1.0)
        else:
            take RegulatedControlAction(throttle, current_steer_angle, past_steer_angle)
        past_steer_angle = current_steer_angle
        past_speed = current_speed
        

        # Monitor trigger
        if monitor_model:
            distIntersection = distance from self to intersection
            distObstacle = distance from self to obstacle
            distLeader = distance from self to leader
            visibleObstacle = int(ego can see obstacle)
            visibleLeader = int(ego can see leader)

            input_features = np.concatenate((self.weather, np.array([self.r,self.g,self.b, distIntersection, distObstacle, visibleObstacle, visibleLeader])))
            input_features = np.expand_dims(input_features, axis=0)
            self.isSafe = monitor_model.predict(input_features)[0]






#PLACEMENT
lane = Uniform(*network.lanes)
trajectory = [lane]


# PLACEMENT
EGO_TO_LEADER = Range(-15,10)
intersec = Uniform(*network.intersections)
turn_maneuvers = filter(lambda i: i.type != ManeuverType.STRAIGHT, intersec.maneuvers)
turn_maneuver = Uniform(*turn_maneuvers)
startLane = turn_maneuver.startLane 
start = startLane.centerline[-1]

leader = new Car following roadDirection from start for -5,
            with blueprint EGO_MODEL,
            with behavior FollowLaneBehaviorModified(target_speed=LEADER_SPEED),
            with steps_speed 0,
            with color Color(0,0,0),
            with time_steps 0

obstacle = new Car at 0 @ 25 relative to leader,
            with heading leader 

ego = new Car following roadDirection from leader.position for EGO_TO_LEADER,
            with blueprint EGO_MODEL,
            with behavior EgoBehavior(target_speed=EGO_SPEED, controller_path=globalParameters.monitor, leaderCar=leader, obstacleCar=obstacle),
            with cte 0,
            with distIntersec EGO_TO_LEADER,
            with isSafe 1,
            with sensors {"front_rgb": RGBSensor(offset=(0, 2, 1), width=640, height=320),
                        "aerial_rgb": RGBSensor(offset=(0, -10, 4), width=1280, height=640)
                        },



require ego can see leader



record distance from ego to leader as distLeader # to "dist_follow_leader.npz"
record distance from ego to intersection as distIntersection # to "dist_intersection.npz"
record distance from ego to obstacle as distObstacle # to "dist_obstacle.npz"
record ego can see obstacle as visibleObstacle
record ego can see leader as visibleLeader
if globalParameters.monitor != "":
    record ego.isSafe as MonitorNotTriggered
record initial obstacle.color as colorObstacle # to "color.npz"
record initial np.array([
        ego.carlaActor.get_world().get_weather().cloudiness,
        ego.carlaActor.get_world().get_weather().precipitation,
        ego.carlaActor.get_world().get_weather().precipitation_deposits,
        ego.carlaActor.get_world().get_weather().wind_intensity,
        ego.carlaActor.get_world().get_weather().sun_azimuth_angle,
        ego.carlaActor.get_world().get_weather().sun_altitude_angle,
        ego.carlaActor.get_world().get_weather().fog_density,
        ego.carlaActor.get_world().get_weather().fog_distance,
        ego.carlaActor.get_world().get_weather().wetness,
        ego.carlaActor.get_world().get_weather().fog_falloff,
        ego.carlaActor.get_world().get_weather().scattering_intensity,
        ego.carlaActor.get_world().get_weather().mie_scattering_scale,
        ego.carlaActor.get_world().get_weather().rayleigh_scattering_scale,
        ego.carlaActor.get_world().get_weather().dust_storm  
    ]) as weather_props # to "weather.npz"
