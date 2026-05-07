"""
TITLE: Multi 03
AUTHOR: Kai-Chun Chang, kaichunchang@berkeley.edu
"""

#################################
# MAP AND MODEL                 #
#################################

param map = localPath('../maps/Town05.xodr')
param carla_map = 'Town05'
model scenic.domains.driving.model

#################################
# CONSTANTS                     #
#################################

MODEL = 'vehicle.lincoln.mkz_2017'
MODEL_ADV = 'vehicle.lincoln.mkz_2017'

EGO_INIT_DIST = [30, 40]
param EGO_SPEED = VerifaiRange(7, 10)
EGO_BRAKE = 1.0

ADV1_DIST = -8
ADV_INIT_DIST = [15, 25]
param ADV_SPEED = VerifaiRange(5, 8)
param ADV1_SPEED = VerifaiRange(9, 12)
param ADV2_SPEED = VerifaiRange(4, 7)
ADV_BRAKE = 1.0

PED_MIN_SPEED = 1.0
PED_THRESHOLD = 20
PED_FINAL_SPEED = 1.0

#param SAFETY_DIST = VerifaiRange(8, 12)
SAFETY_DIST = 8
CRASH_DIST = 5
TERM_DIST = 80

#################################
# AGENT BEHAVIORS               #
#################################

behavior EgoBehavior(trajectory):
    '''The ego vehicle follows the planned trajectory, and brakes if the pedestrian is within the safety distance and is in the drivable region. Ego will keep braking until the pedestrian is out of the safety distance + 3 meters. The condition will only be triggered once to ensure the ego can make progress.'''
    flag = True
    try:
        do FollowTrajectoryBehavior(target_speed=globalParameters.EGO_SPEED, trajectory=trajectory)
        do FollowLaneBehavior(target_speed=globalParameters.ADV_SPEED)
    interrupt when withinDistanceToAnyObjs(self, SAFETY_DIST) and (ped in network.drivableRegion) and flag:
        flag = False
        while withinDistanceToAnyObjs(self, SAFETY_DIST + 3):
            take SetBrakeAction(EGO_BRAKE)

behavior Adv1Behavior(trajectory):
    try:
        do FollowTrajectoryBehavior(target_speed=globalParameters.ADV1_SPEED, trajectory=trajectory)
    interrupt when (distance from adv1 to ego) < SAFETY_DIST:
        take SetBrakeAction(ADV_BRAKE)

behavior Adv2Behavior(trajectory):
    try:
        do FollowTrajectoryBehavior(target_speed=globalParameters.ADV_SPEED, trajectory=trajectory)
        do FollowLaneBehavior(target_speed=globalParameters.ADV2_SPEED)
    interrupt when (distance from self to ped) < SAFETY_DIST:
        take SetBrakeAction(ADV_BRAKE)

behavior Adv3Behavior(trajectory):
    try:
        do FollowTrajectoryBehavior(target_speed=globalParameters.ADV_SPEED, trajectory=trajectory)
        do FollowLaneBehavior(target_speed=globalParameters.ADV_SPEED)
    interrupt when (distance from self to ped) < SAFETY_DIST:
        take SetBrakeAction(ADV_BRAKE)

behavior Adv4Behavior(trajectory):
    try:
        do FollowTrajectoryBehavior(target_speed=globalParameters.ADV_SPEED, trajectory=trajectory)
    interrupt when withinDistanceToAnyObjs(self, SAFETY_DIST):
        take SetBrakeAction(ADV_BRAKE)

behavior Pedbehavior():
    take SetWalkingSpeedAction(speed=PED_MIN_SPEED)

#################################
# SPATIAL RELATIONS             #
#################################

intersection = Uniform(*filter(lambda i: i.is4Way, network.intersections))

# ego: right turn from S to E
egoManeuver = Uniform(*filter(lambda m: m.type is ManeuverType.RIGHT_TURN, intersection.maneuvers))
egoInitLane = egoManeuver.startLane
egoTrajectory = [egoInitLane, egoManeuver.connectingLane, egoManeuver.endLane]
egoSpawnPt = new OrientedPoint in egoInitLane.centerline

# adv1: straight from S to N
adv1InitLane = egoInitLane
adv1Maneuver = Uniform(*filter(lambda m: m.type is ManeuverType.STRAIGHT, adv1InitLane.maneuvers))
adv1Trajectory = [adv1InitLane, adv1Maneuver.connectingLane, adv1Maneuver.endLane]

# adv2: straight from W to E
adv2InitLane = Uniform(*filter(lambda m: m.type is ManeuverType.STRAIGHT,
        Uniform(*filter(lambda m: m.type is ManeuverType.STRAIGHT, egoInitLane.maneuvers)).conflictingManeuvers)).startLane
adv2Maneuver = Uniform(*filter(lambda m: m.type is ManeuverType.STRAIGHT, adv2InitLane.maneuvers))
adv2Trajectory = [adv2InitLane, adv2Maneuver.connectingLane, adv2Maneuver.endLane]
adv2SpawnPt = new OrientedPoint in adv2InitLane.centerline

# adv3: left-turn from E to S
adv3InitLane = Uniform(*filter(lambda m: m.type is ManeuverType.STRAIGHT, adv2Maneuver.reverseManeuvers)).startLane
adv3Maneuver = Uniform(*filter(lambda m: m.type is ManeuverType.LEFT_TURN, adv3InitLane.maneuvers))
adv3Trajectory = [adv3InitLane, adv3Maneuver.connectingLane, adv3Maneuver.endLane]

# adv4: left-turn from N to E
adv4InitLane = Uniform(*filter(lambda m: m.type is ManeuverType.STRAIGHT,
        Uniform(*filter(lambda m: m.type is ManeuverType.STRAIGHT, egoInitLane.maneuvers)).reverseManeuvers)).startLane
adv4Maneuver = Uniform(*filter(lambda m: m.type is ManeuverType.LEFT_TURN, adv4InitLane.maneuvers))
adv4Trajectory = [adv4InitLane, adv4Maneuver.connectingLane, adv4Maneuver.endLane]

# pedestrian
tempSpawnPt = egoInitLane.centerline[-1]
pedSpawnPt = new OrientedPoint right of tempSpawnPt by 5
pedEndPt = new OrientedPoint at pedSpawnPt offset by (0, 5, 0)

#################################
# SCENARIO SPECIFICATION        #
#################################

ego = new Car at egoSpawnPt,
    with blueprint MODEL,
    with behavior EgoBehavior(egoTrajectory)

adv1 = new Car following roadDirection for ADV1_DIST,
    with blueprint MODEL_ADV,
    with behavior Adv1Behavior(adv1Trajectory)

adv2 = new Car at adv2SpawnPt,
    with blueprint MODEL_ADV,
    with behavior Adv2Behavior(adv2Trajectory)

adv3 = new Car at adv2 offset by -10 @ 70,
    with blueprint MODEL_ADV,
    with behavior Adv3Behavior(adv3Trajectory)

adv4 = new Car at ego offset by -10 @ 85,
    with blueprint MODEL_ADV,
    with behavior Adv3Behavior(adv4Trajectory)

ped = new Pedestrian at pedSpawnPt,
    facing toward pedEndPt,
    with regionContainedIn everywhere,
    with behavior Pedbehavior()

require EGO_INIT_DIST[0] <= (distance to intersection) <= EGO_INIT_DIST[1]
require ADV_INIT_DIST[0] <= (distance from adv2 to intersection) <= ADV_INIT_DIST[1]
require adv3InitLane.road is egoManeuver.endLane.road
terminate when (distance to egoSpawnPt) > TERM_DIST

#################################
# RECORDING                     #
#################################

record ego in network.drivableRegion as egoIsInDrivableRegion
record distance from ego to network.drivableRegion as egoDistToDrivableRegion
record distance from ego to egoInitLane.group as egoDistToEgoInitLane
record distance from ego to egoManeuver.endLane.group as egoDistToEgoEndLane
record distance from ego to ego.lane.centerline as egoDistToEgoLaneCenterline
record distance from ego to intersection as egoDistToIntersection

record distance from ego to adv1 as egoDistToAdv1
record distance to egoSpawnPt as egoDistToEgoSpawnPt
