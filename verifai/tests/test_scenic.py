
import pytest

from verifai.samplers.scenic_sampler import ScenicSampler

def test_objects():
    sampler = ScenicSampler.fromScenicCode(
        'ego = Object at 4 @ 9',
        maxIterations=1
    )
    sample = sampler.nextSample()
    objects = sample.objects
    assert len(objects) == 1
    pos = objects.object0.position
    assert type(pos) is tuple
    assert pos == (4, 9)

def test_params():
    sampler = ScenicSampler.fromScenicCode(
        'param x = (3, 5)\n'
        'ego = Object',
        maxIterations=1
    )
    sample = sampler.nextSample()
    x = sample.params.x
    assert type(x) is float
    assert 3 <= x <= 5

def test_lists():
    sampler = ScenicSampler.fromScenicCode(
        'ego = Object with foo [1, -1, 3.3]',
        maxIterations=1
    )
    sample = sampler.nextSample()
    foo = sample.objects.object0.foo
    assert type(foo) is tuple
    assert foo == pytest.approx((1, -1, 3.3))

def test_webots_mars(pathToLocalFile):
    path = pathToLocalFile('scenic_mars.sc')
    sampler = ScenicSampler.fromScenario(path)

    for i in range(3):
        sample = sampler.nextSample()
        print(f'Sample #{i}:')
        print(sample)

def test_webots_road(pathToLocalFile):
    path = pathToLocalFile('scenic_road.sc')
    sampler = ScenicSampler.fromScenario(path)

    for i in range(3):
        sample = sampler.nextSample()
        print(f'Sample #{i}:')
        print(sample)
