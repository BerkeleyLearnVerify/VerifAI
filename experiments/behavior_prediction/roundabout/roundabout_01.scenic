"""
TITLE: Behavior Prediction - Roundabout 01
AUTHOR: Francis Indaheng, findaheng@berkeley.edu
DESCRIPTION: 
"""

#################################
# MAP AND MODEL                 #
#################################

param map = localPath('../../../../tests/formats/opendrive/maps/CARLA/Town03.xodr')
param carla_map = 'Town03'
model scenic.simulators.carla.model

#################################
# CONSTANTS                     #
#################################

EGO_INIT_DIST = [20, 25]
EGO_SPEED = VerifaiRange(7, 10)
EGO_BRAKE = VerifaiRange(0.5, 1.0)

ADV_INIT_DIST = [15, 20]
ADV_SPEED = VerifaiRange(7, 10)

SAFETY_DIST = VerifaiRange(10, 20)
TERM_DIST = 70

#################################
# AGENT BEHAVIORS               #
#################################



#################################
# SPATIAL RELATIONS             #
#################################

roundabout = Uniform(*filter(lambda i: len(i.incomingLanes) == 7, network.intersections))

egoInitLane = Uniform(*roundabout.incomingLanes)

egoManeuver = Uniform(*filter(lambda m: m.type is ManeuverType.STRAIGHT, egoInitLane.maneuvers))

#################################
# SCENARIO SPECIFICATION        #
#################################

ego = Car at egoSpawnPt,
	with behavior FollowLaneBehavior(EGO_SPEED)

require EGO_INIT_DIST[0] <= (distance to intersection) <= EGO_INIT_DIST[1]
terminate when (distance to egoSpawnPt) > TERM_DIST
