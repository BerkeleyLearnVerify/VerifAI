from glis.solvers import GLIS
from verifai.features import *
from verifai.samplers import *
from dotmap import DotMap
from numpy import random as rdm

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

    params = DotMap()
    params.n_initial_random=10
    sampler = FeatureSampler.glisSamplerFor(space, params)

    sampleWithFeedback(sampler, 10, f)

def test_save_restore(tmpdir):
    space = FeatureSpace({
        'a': Feature(DiscreteBox([0, 12])),
        'b': Feature(Box((0, 1)), lengthDomain=DiscreteBox((1, 2)))
    })
    params = DotMap()
    params.n_initial_random=3
    sampler = FeatureSampler.glisSamplerFor(space, params)

    checkSaveRestore(sampler, tmpdir)

def test_direct_vs_verifai():
    fun = lambda x: ((4.0 - 2.1 * x[0] ** 2 + x[0] ** 4 / 3.0) *
                     x[0] ** 2 + x[0] * x[1] + (4.0 * x[1] ** 2 - 4.0) * x[1] ** 2)

    p = {'display': 0, 'n_initial_random': 3}

    # Direct GLIS approach
    rdm.seed(0)
    random.seed(0)

    lb = np.array([-2.0, -1.0])
    ub = np.array([2.0, 1.0])

    prob = GLIS(bounds=(lb, ub), **p)

    X = []
    F = []
    for i in range(6):
        if i == 0:
            x = prob.initialize()
            X.append(x.tolist())
        else:
            f = fun(x)
            x = prob.update(f)
            X.append(x.tolist())
            F.append(f)

    # VerifAI approach
    rdm.seed(0)
    random.seed(0)
    space = FeatureSpace({
        'a': Feature(Box([-2.0, 2.0])),
        'b': Feature(Box([-1.0, 1.0]))
    })

    sampler = FeatureSampler.glisSamplerFor(space, p)

    X_prime = []
    F_prime = []
    for i in range(6):
        if i == 0:
            x_prime = sampler.nextSample(int(1))
            X_prime.append([x_prime[0][0], x_prime[1][0]])
        else:
            f_prime = fun([x_prime[0][0], x_prime[1][0]])
            x_prime = sampler.nextSample(feedback=f_prime)
            X_prime.append([x_prime[0][0], x_prime[1][0]])
            F_prime.append(f_prime)

    assert X == X_prime
    assert F == F_prime