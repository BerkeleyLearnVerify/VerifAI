from verifai.features import *
from verifai.samplers import *
from dotmap import DotMap

import pytest
from tests.utils import sampleWithFeedback, checkSaveRestore


def test_glisOptimization():
    carDomain = Struct({
        'position': Box([-10,10], [-10,10], [0,1]),
        'heading': Box([0, math.pi]),
    })

    space = FeatureSpace({
        'cars': Feature(Array(carDomain, [2]))
    })

    def f(sample):
        sample = sample.cars[0].heading[0]
        return abs(sample - 0.75)

    sampler = FeatureSampler.glisSamplerFor(space, n_initial_random=10)

    sampleWithFeedback(sampler, 3, f)

def test_save_restore(tmpdir):
    space = FeatureSpace({
        'a': Feature(DiscreteBox([0, 12])),
        'b': Feature(Box((0, 1)), lengthDomain=DiscreteBox((1, 2)))
    })
    sampler = FeatureSampler.glisSamplerFor(space, n_initial_random=3)

    checkSaveRestore(sampler, tmpdir)


