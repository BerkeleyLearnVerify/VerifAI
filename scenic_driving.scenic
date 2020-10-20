import scenic

param map = localPath('dynamic-verifai/tests/Town01.xodr')
param carla_map = 'Town01'
param verifaiSamplerType = 'halton'

model scenic.domains.driving.model

simulator scenic.core.simulators.DummySimulator()

ego = Car at VerifaiRange(-5, 5) @ 2, with behavior FollowLaneBehavior
