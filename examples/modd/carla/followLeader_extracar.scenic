""" Scenario Description
The ego car uses a CNN controller to follow the leader car. 
An ODD monitor (sklearn model) is used to detect unsafe situations, and switch to a safe controller before ego exits its ODD.
"""

import pickle

import sklearn
import numpy as np 
import torch
import torchvision

from scenic.domains.driving.controllers import (
    PIDLateralController,
    PIDLongitudinalController,
)
from controller_training import (
    resNet, 
    CNN,
)
from followCarBehaviorMODD import (
    run_MODD,
    FollowCarBehaviorMODD,
)

from modd_torch import MLP
      
param timeout = 180
param map = localPath('../../../tests/scenic/Town01.xodr')
param carla_map = 'Town01'
param timeBound = 300


model scenic.simulators.carla.model

#CONSTANTS
EGO_MODEL = "vehicle.tesla.model3"
LEADER_SPEED = TimeSeries(VerifaiRange(6,8))
EGO_SPEED = 3
THROTTLE_ACTION = 0.5
EGO_TO_LEADER = Range(-15, -10)
EGO_BRAKING_THRESHOLD = 6
EGO_ACCELERATION_THRESHOLD = 10

monitor_model = None
if globalParameters.monitor != "":
    if globalParameters.monitor_type == "sklearn":
        with open(globalParameters.monitor, 'rb') as f:
            monitor_model = pickle.load(f) 
    else:
        monitor_model = MLP()
        monitor_model.cuda()
        monitor_model.load_state_dict(torch.load(globalParameters.monitor))
        monitor_model.eval()
        print("Monitor loaded")

 
    


behavior EgoBehavior(target_speed = 10, controller_path = None, leaderCar=None, obstacleCar=None, monitor_model=None):
    if monitor_model is None:
        do ControllerBehavior(target_speed, controller_path, leaderCar)
    else:
        try:
            do ControllerBehavior(target_speed=target_speed, controller_path=controller_path, leaderCar=leaderCar, obstacleCar=obstacleCar)
        interrupt when not self.isSafe:
            print("-- Monitor: Not safe! Switching to SafeBehavior.")
            take SetBrakeAction(1.0)
            do EgoBehavior2(target_speed = target_speed, controller_path = controller_path, leaderCar=leaderCar, obstacleCar=obstacleCar, monitor_model=monitor_model)

behavior EgoBehavior2(target_speed = 10, controller_path = None, leaderCar=None, obstacleCar=None, monitor_model=None):
    try:
        do FollowCarBehaviorMODD(target_speed=target_speed, leaderCar=leader, monitor_model=monitor_model)
    interrupt when self.isSafe:
        print("-- Monitor: Safe! Switching back to CNN Controller.")
        do EgoBehavior(target_speed=target_speed, controller_path=controller_path, leaderCar=leaderCar, obstacleCar=obstacleCar, monitor_model=monitor_model)



behavior ControllerBehavior(target_speed = 10, controller_path = None, leaderCar=None, obstacleCar=None, monitor_model=monitor_model):
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
    if not monitor_model is None:
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
        front_img = self.observations["front_rgb"][-1]
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
        if not monitor_model is None:
            run_MODD(self, monitor_model, obstacleCar, leaderCar)
            


#PLACEMENT
lane = Uniform(*network.lanes)
trajectory = [lane]


# PLACEMENT
intersec = Uniform(*network.intersections)
turn_maneuvers = filter(lambda i: i.type != ManeuverType.STRAIGHT, intersec.maneuvers)
turn_maneuver = Uniform(*turn_maneuvers)
startLane = turn_maneuver.startLane 
start = startLane.centerline[-1]

leader = new Car following roadDirection from start for -5,
            with blueprint EGO_MODEL,
            with behavior FollowCarBehaviorMODD(target_speed=LEADER_SPEED),
            with steps_speed 0,
            with color Color(0,0,0),
            with time_steps 0,
            with requireVisible True

obstacle = new Car at 0 @ 25 relative to leader,
            with heading leader 

ego = new Car following roadDirection from leader for EGO_TO_LEADER,
            with blueprint EGO_MODEL,
            with behavior EgoBehavior(target_speed=EGO_SPEED, controller_path=globalParameters.controller, leaderCar=leader, obstacleCar=obstacle, monitor_model=monitor_model),
            with cte 0,
            with distIntersec EGO_TO_LEADER,
            with isSafe 1,
            with sensors {"front_rgb": RGBSensor(offset=(0, 2, 1), width=640, height=320)},





record distance from ego to leader as distLeader 
record distance from ego to intersection as distIntersection
record distance from ego to obstacle as distObstacle 
record ego can see obstacle as visibleObstacle
record ego can see leader as visibleLeader
record ego.isSafe as MonitorNotTriggered
record initial obstacle.color as colorObstacle 
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
    ]) as weather_props 
