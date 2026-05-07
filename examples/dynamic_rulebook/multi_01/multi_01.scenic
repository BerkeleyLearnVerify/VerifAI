"""
TITLE: Multi 01
AUTHOR: Kai-Chun Chang, kaichunchang@berkeley.edu
DESCRIPTION: The ego vehicle is driving along its lane when it encounters a blocking car ahead. The ego attempts to change to the opposite lane to bypass the blocking car before returning to its original lane.
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

param EGO_SPEED = VerifaiRange(6, 9) #7
param DIST_THRESHOLD = VerifaiRange(12, 14) #13
param BLOCKING_CAR_DIST = VerifaiRange(15, 20)
param BYPASS_DIST = VerifaiRange(4, 6) #5

DIST_TO_INTERSECTION = 15
TERM_DIST = 40

#################################
# AGENT BEHAVIORS               #
#################################

behavior EgoBehavior(path):
    current_lane = self.lane
    laneChangeCompleted = False
    bypassed = False
    try:
        do FollowLaneBehavior(globalParameters.EGO_SPEED, laneToFollow=current_lane)
    interrupt when (distance to blockingCar) < globalParameters.DIST_THRESHOLD and not laneChangeCompleted:
        do LaneChangeBehavior(path, is_oppositeTraffic=True, target_speed=globalParameters.EGO_SPEED)
        do FollowLaneBehavior(globalParameters.EGO_SPEED, is_oppositeTraffic=True) until (distance to blockingCar) > globalParameters.BYPASS_DIST
        laneChangeCompleted = True
    interrupt when (blockingCar can see ego) and (distance to blockingCar) > globalParameters.BYPASS_DIST and not bypassed:
        current_laneSection = self.laneSection
        rightLaneSec = current_laneSection._laneToLeft
        do LaneChangeBehavior(rightLaneSec, is_oppositeTraffic=False, target_speed=globalParameters.EGO_SPEED)
        bypassed = True

#################################
# SPATIAL RELATIONS             #
#################################

#Find lanes that have a lane to their left in the opposite direction
laneSecsWithLeftLane = []
for lane in network.lanes:
    for laneSec in lane.sections:
        if laneSec._laneToLeft is not None:
            if laneSec._laneToLeft.isForward is not laneSec.isForward:
                laneSecsWithLeftLane.append(laneSec)

assert len(laneSecsWithLeftLane) > 0, \
    'No lane sections with adjacent left lane with opposing \
    traffic direction in network.'

initLaneSec = Uniform(*laneSecsWithLeftLane)
leftLaneSec = initLaneSec._laneToLeft

spawnPt = new OrientedPoint on initLaneSec.centerline

#################################
# SCENARIO SPECIFICATION        #
#################################

ego = new Car at spawnPt,
    with blueprint MODEL,
    with behavior EgoBehavior(leftLaneSec)
    
blockingCar = new Car following roadDirection from ego for globalParameters.BLOCKING_CAR_DIST,
            with blueprint MODEL,
            with viewAngle 90 deg

require distance from blockingCar to intersection > DIST_TO_INTERSECTION
terminate when distance to spawnPt > TERM_DIST

#################################
# RECORDING                     #
#################################

record initial initLaneSec.polygon.exterior.coords as initLaneCoords
record initial leftLaneSec.polygon.exterior.coords as leftLaneCoords
record ego.lane is initLaneSec.lane as egoIsInInitLane
record ego.lane is leftLaneSec.lane as egoIsInLeftLane
