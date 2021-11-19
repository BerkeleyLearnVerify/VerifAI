
import pytest
from dotmap import DotMap

from verifai.samplers.scenic_sampler import ScenicSampler
from verifai.scenic_server import ScenicServer
from verifai.falsifier import generic_falsifier
from tests.utils import sampleWithFeedback, checkSaveRestore

## Basic

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
        'param x = Range(3, 5)\n'
        'ego = Object',
        maxIterations=1
    )
    sample = sampler.nextSample()
    x = sample.params.x
    assert type(x) is float
    assert 3 <= x <= 5

def test_quoted_param():
    sampler = ScenicSampler.fromScenicCode(
        'param "x/y" = Range(3, 5)\n'
        'ego = Object',
        maxIterations=1
    )
    sample = sampler.nextSample()
    v = sampler.paramDictForSample(sample)['x/y']
    assert type(v) is float
    assert 3 <= v <= 5

def test_lists():
    sampler = ScenicSampler.fromScenicCode(
        'ego = Object with foo [1, -1, 3.3]',
        maxIterations=1
    )
    sample = sampler.nextSample()
    foo = sample.objects.object0.foo
    assert type(foo) is tuple
    assert foo == pytest.approx((1, -1, 3.3))

def test_save_restore(tmpdir):
    sampler = ScenicSampler.fromScenicCode(
        'ego = Object at Range(-1, 1) @ 0',
        maxIterations=1
    )
    checkSaveRestore(sampler, tmpdir)

## Active sampling

def test_active_sampling():
    sampler = ScenicSampler.fromScenicCode(
        'from dotmap import DotMap\n'
        'param verifaiSamplerType = "ce"\n'
        'ce_params = DotMap(alpha=0.9)\n'
        'ce_params.cont.buckets = 2\n'
        'param verifaiSamplerParams = ce_params\n'
        'ego = Object at VerifaiRange(-1, 1) @ 0',
        maxIterations=1
    )
    def f(sample):
        return -1 if sample.objects.object0.position[0] < 0 else 1
    samples = sampleWithFeedback(sampler, 120, f)
    xs = [sample.objects.object0.position[0] for sample in samples]
    assert all(-1 <= x <= 1 for x in xs)
    assert any(x > 0 for x in xs)
    assert 66 <= sum(x < 0 for x in xs[50:])

def test_active_save_restore(tmpdir):
    sampler = ScenicSampler.fromScenicCode(
        'param verifaiSamplerType = "halton"\n'
        'ego = Object at VerifaiRange(-1, 1) @ 0',
        maxIterations=1
    )
    checkSaveRestore(sampler, tmpdir)

## Webots

def runSampler(sampler):
    for i in range(3):
        sample = sampler.nextSample()
        print(f'Sample #{i}:')
        print(sample)

def test_webots_mars(pathToLocalFile):
    path = pathToLocalFile('scenic_mars.scenic')
    sampler = ScenicSampler.fromScenario(path)
    runSampler(sampler)

def test_webots_road(pathToLocalFile):
    path = pathToLocalFile('scenic_road.scenic')
    sampler = ScenicSampler.fromScenario(path)
    runSampler(sampler)

## Driving domain

def test_driving(pathToLocalFile):
    path = pathToLocalFile('scenic_driving.scenic')
    sampler = ScenicSampler.fromScenario(path)
    runSampler(sampler)

## Dynamic scenarios

def test_driving_dynamic(pathToLocalFile):
    path = pathToLocalFile('scenic_driving.scenic')
    sampler = ScenicSampler.fromScenario(path)
    falsifier_params = DotMap(
        n_iters=3,
        save_error_table=False,
        save_safe_table=False,
    )
    server_options = DotMap(maxSteps=2, verbosity=3)
    falsifier = generic_falsifier(sampler=sampler,
                                  falsifier_params=falsifier_params,
                                  server_class=ScenicServer,
                                  server_options=server_options)
    falsifier.run_falsifier()
