import math
import itertools
import os.path

from verifai.features import (Struct, Array, Box, DiscreteBox,
                              Feature, TimeSeriesFeature, FeatureSpace)
from verifai.samplers import RandomSampler, FeatureSampler

def test_feature_sampling():
    space = FeatureSpace({
        'a': Feature(DiscreteBox([0, 12])),
        'b': Feature(Box((0, 1)), lengthDomain=DiscreteBox((0, 2))),
        'c': TimeSeriesFeature(Box((2,5)), lengthDomain=DiscreteBox((0,4)))
    },
    timeBound=10)
    sampler = FeatureSampler.randomSamplerFor(space)

    static_sample = sampler.getSample()

    static_dict = static_sample[0]._asdict()
    assert "a" in static_dict
    assert "b" in static_dict
    assert "c" not in static_dict

    assert len(static_dict["a"]) == 1
    assert 0 <= static_dict["a"][0] <= 12
    assert 0 <= len(static_dict["b"]) <= 2
    assert all(0 <= v <= 1 for v in static_dict["b"])

## Random sampling

def test_domain_random():
    carDomain = Struct({
        'position': Box([-10,10], [-10,10], [0,1]),
        'heading': Box([0, math.pi]),
    })
    domain = Array(carDomain, (2, 2))
    sampler = RandomSampler(domain)

    def check(samples):
        for sample in samples:
            assert type(sample) is tuple
            assert len(sample) == 2
            for row in sample:
                assert type(row) is tuple
                assert len(row) == 2
                for car in row:
                    assert type(car) is carDomain.makePoint
                    position = car.position
                    assert type(position) is tuple
                    assert len(position) == 3
                    heading = car.heading
                    assert type(heading) is tuple
                    assert len(heading) == 1
        assert any(sample[0][0].position[0] > sample[1][1].position[0]
                   for sample in samples)
        assert any(sample[0][0].position[0] < sample[1][1].position[0]
                   for sample in samples)

    check([sampler.nextSample() for i in range(100)])
    check(list(itertools.islice(sampler, 100)))

def test_space_random():
    space = FeatureSpace({
        'a': Feature(DiscreteBox([0, 12])),
        'b': Feature(Box((0, 1)), lengthDomain=DiscreteBox((0, 2)))
    })
    sampler = FeatureSampler.randomSamplerFor(space)

    def check(samples):
        for sample in samples:
            assert type(sample) is space.makePoint
            a = sample.a
            assert type(a) is tuple
            assert len(a) == 1
            assert type(a[0]) is int
            assert 0 <= a[0] <= 12
            b = sample.b
            assert type(b) is tuple
            l = len(b)
            assert 0 <= l <= 2
            if l > 0:
                assert type(b[0]) is tuple
                assert len(b[0]) == 1
                assert 0 <= b[0][0] <= 1
            if l > 1:
                assert type(b[1]) is tuple
                assert len(b[1]) == 1
                assert 0 <= b[1][0] <= 1
        assert any(sample.a[0] > 6 for sample in samples)
        assert any(sample.a[0] < 6 for sample in samples)
        assert any(len(sample.b) == 0 for sample in samples)
        assert any(len(sample.b) == 1 for sample in samples)
        assert any(len(sample.b) == 2 for sample in samples)

    check([sampler.nextSample() for i in range(100)])
    check(list(itertools.islice(sampler, 100)))

def test_random_restore(tmpdir):
    space = FeatureSpace({
        'a': Feature(DiscreteBox([0, 12])),
        'b': Feature(Box((0, 1)), lengthDomain=DiscreteBox((0, 2)))
    })
    sampler = FeatureSampler.randomSamplerFor(space)

    path = os.path.join(tmpdir, 'blah.dat')
    sampler.saveToFile(path)
    sample1 = sampler.nextSample()
    sampler = FeatureSampler.restoreFromFile(path)
    sample2 = sampler.nextSample()
    assert sample1 == sample2
