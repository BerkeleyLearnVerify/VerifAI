from scenic.domains.driving.controllers import (
    PIDLateralController,
    PIDLongitudinalController,
)

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


