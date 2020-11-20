#SET MAP AND MODEL (i.e. definitions of all referenceable vehicle types, road library, etc)
param map = localPath('/home/scenic/Desktop/Scenic-devel/tests/formats/opendrive/maps/CARLA/Town03.xodr')  # or other CARLA map that definitely works
param carla_map = 'Town03'
model scenic.simulators.carla.model #located in scenic/simulators/carla/model.scenic
param verifaiSamplerType = 'ce'

DISTANCE_TO_INTERSECTION = VerifaiRange(-20, -10)
HESITATION_TIME = VerifaiRange(0, 10)
UBER_SPEED = VerifaiRange(10, 20)

behavior EgoBehavior(trajectory):
    print([section._laneToRight for section in startLane.sections])
    do FollowTrajectoryBehavior(trajectory=trajectory, target_speed=UBER_SPEED)
    terminate

behavior CrossingCarBehavior(trajectory):
    while simulation().currentTime < HESITATION_TIME:
        wait
    do FollowTrajectoryBehavior(trajectory = trajectory)
    terminate

fourWayIntersection = filter(lambda i: i.is4Way, network.intersections)
intersec = Uniform(*fourWayIntersection)
rightLanes = filter(lambda lane: all([section._laneToRight is None for section in lane.sections]), intersec.incomingLanes)
startLane = Uniform(*rightLanes)
straight_maneuvers = filter(lambda i: i.type == ManeuverType.STRAIGHT, startLane.maneuvers)
straight_maneuver = Uniform(*straight_maneuvers)

otherLane = straight_maneuver.endLane.group.opposite.lanes[-1]
left_maneuvers = filter(lambda i: i.type == ManeuverType.LEFT_TURN, otherLane.maneuvers)
left_maneuver = Uniform(*left_maneuvers)

ego_trajectory = [straight_maneuver.startLane, straight_maneuver.connectingLane, straight_maneuver.endLane]
crossing_car_trajectory = [left_maneuver.startLane, left_maneuver.connectingLane, left_maneuver.endLane]

uberSpawnPoint = startLane.centerline[-1]
crossingSpawnPoint = otherLane.centerline[-1]

ego = Car following roadDirection from uberSpawnPoint for DISTANCE_TO_INTERSECTION,
        with behavior EgoBehavior(trajectory = ego_trajectory)

crossing_car = Car at crossingSpawnPoint,
                with behavior CrossingCarBehavior(crossing_car_trajectory)