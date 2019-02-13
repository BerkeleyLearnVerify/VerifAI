from verifai.features import *
from verifai.samplers import *
from dotmap import DotMap

import pytest

pytest.importorskip('GPyOpt')

def test_bayesianOptimization():
    carDomain = Struct({
        'position': Box([-10,10], [-10,10], [0,1]),
        'heading': Box([0, math.pi]),
    })

    space = FeatureSpace({
        'cars': Feature(Array(carDomain, [2]))
    })

    def f(sample):
        sample = sample.cars[0].heading[0]
        return np.array(sample - 0.75)

    bo_params = DotMap()
    bo_params.init_num = 2
    bo_params.f = f

    sampler = FeatureSampler.bayesianOptimizationSamplerFor(space, BO_params=bo_params)

    for i in range(3):
        print(f'Sample #{i}:')
        print(sampler.nextSample())
