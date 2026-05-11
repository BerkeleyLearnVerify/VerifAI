"""
TITLE: Multi 02
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

param EGO_SPEED = VerifaiRange(8, 12)
param EGO_BRAKE = VerifaiRange(0.7, 1.0)
param ADV_SPEED = VerifaiRange(3, 6)
param ADV3_SPEED = VerifaiRange(3, 6)

ADV1_DIST = 12
ADV2_DIST = -6
ADV3_DIST = 6

BYPASS_DIST = 10
SAFE_DIST = 10
INIT_DIST = 40
TERM_DIST = 80

#################################
# AGENT BEHAVIORS               #
#################################

behavior EgoBehavior():
    try:
        do FollowLaneBehavior(target_speed=globalParameters.EGO_SPEED)
    interrupt when (distance from adv2 to ego) > BYPASS_DIST:
        fasterLaneSec = self.laneSection.fasterLane
        do LaneChangeBehavior(
                laneSectionToSwitch=fasterLaneSec,
                target_speed=globalParameters.EGO_SPEED)
        try:
            do FollowLaneBehavior(
                    target_speed=globalParameters.EGO_SPEED,
                    laneToFollow=fasterLaneSec.lane)
        interrupt when (distance from adv3 to ego) < SAFE_DIST:
            take SetBrakeAction(globalParameters.EGO_BRAKE)
    interrupt when (distance from adv1 to ego) < SAFE_DIST:
        take SetBrakeAction(globalParameters.EGO_BRAKE)

behavior Adv1Behavior():
    do FollowLaneBehavior(target_speed=globalParameters.ADV_SPEED)

behavior Adv2Behavior():
    fasterLaneSec = self.laneSection.fasterLane
    do LaneChangeBehavior(
            laneSectionToSwitch=fasterLaneSec,
            target_speed=globalParameters.ADV_SPEED)
    do FollowLaneBehavior(target_speed=globalParameters.ADV_SPEED)

behavior Adv3Behavior():
    fasterLaneSec = self.laneSection.fasterLane
    do LaneChangeBehavior(
            laneSectionToSwitch=fasterLaneSec,
            target_speed=globalParameters.ADV_SPEED)
    do FollowLaneBehavior(target_speed=globalParameters.ADV3_SPEED)

#################################
# SPATIAL RELATIONS             #
#################################

initLane = Uniform(*network.lanes)
egoSpawnPt = new OrientedPoint in initLane.centerline

#################################
# SCENARIO SPECIFICATION        #
#################################

ego = new Car at egoSpawnPt,
    with blueprint MODEL,
    with behavior EgoBehavior()

adv1 = new Car following roadDirection for ADV1_DIST,
    with blueprint MODEL,
    with behavior Adv1Behavior()

adv2 = new Car following roadDirection for ADV2_DIST,
    with blueprint MODEL,
    with behavior Adv2Behavior()

adv3 = new Car following roadDirection for ADV3_DIST,
    with blueprint MODEL,
    with behavior Adv3Behavior()

require distance to intersection > INIT_DIST
require distance from adv1 to intersection > INIT_DIST
require distance from adv2 to intersection > INIT_DIST
require distance from adv3 to intersection > INIT_DIST
require always adv1.laneSection._fasterLane is not None
terminate when distance to egoSpawnPt > TERM_DIST

#################################
# RECORDING                     #
#################################

record ego.lane is initLane or ego.lane is not adv2.lane as egoIsInInitLane
record adv2.lane is initLane as adv2IsInInitLane # start evaluation only when adv2 reaches another lane
record adv3.lane is initLane as adv3IsInInitLane # start evaluation only when adv3 reaches another lane
