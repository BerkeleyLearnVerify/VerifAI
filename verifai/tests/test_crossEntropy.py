from verifai.features import *
from verifai.samplers import *
from dotmap import DotMap

def test_crossEntropy():
    carDomain = Struct({
        'position': Box([-10,10], [-10,10], [0,1]),
        'heading': Box([0, math.pi]),
        'model': DiscreteBox([0, 10])
    })

    space = FeatureSpace({
        'weather': Feature(DiscreteBox([0,12])),
        'cars': Feature(Array(carDomain, [2]))
    })

    def f(sample):
        print(sample.cars[0].heading[0] - 0.75)
        return sample.cars[0].heading[0] - 0.75

    ce_params = DotMap()
    ce_params.alpha =0.9
    ce_params.f = f
    ce_params.thres = 0.25
    ce_params.cont.buckets = np.array([5])
    ce_params.cont.dist= None
    ce_params.disc.dist = None

    sampler = FeatureSampler.crossEntropySamplerFor(space, ce_params=ce_params)

    for i in range(3):
        print(f'Sample #{i}:')
        print(sampler.nextSample())
