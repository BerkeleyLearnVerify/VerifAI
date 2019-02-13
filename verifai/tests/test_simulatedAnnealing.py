import math

from verifai.features import *
from verifai.samplers import *
from dotmap import DotMap
import math

def test_simulatedAnnealing():
    carDomain = Struct({
        'position': Box([-10,10], [-10,10], [0,1]),
        'heading': Box([0, math.pi]),
    })

    space = FeatureSpace({
        'cars': Feature(Array(carDomain, [2]))
    })

    def f(sample):
        return sample.cars[0].heading[0] - 0.75

    def proposal_func(sample, iteration, decay_rate, num_variables):

        decayed_width = decay_rate**iteration*1
        lower_bound = [(sample[i] - decayed_width/2) for i in range(num_variables)]
        upper_bound = [(sample[i] + decayed_width/2) for i in range(num_variables)]

        for index in range(num_variables): # check whether updated range for each parameter is within original ranges
            if lower_bound[index] < 0:
                lower_bound[index] = 0
            if upper_bound[index] > 1:
                upper_bound[index] = 1
                
        return np.random.uniform(lower_bound, upper_bound)


    sa_params = DotMap()
    sa_params.T = 10
    sa_params.decay_rate = 0.9
    sa_params.iterations = 3
    sa_params.reset_temp = 5
    sa_params.num_epoch = 4
    sa_params.loss_f = f
    sa_params.temp_f = lambda t: 0.91*t
    sa_params.iter_f = lambda length: int(math.ceil(0.5*length))
    sa_params.proposal_f = proposal_func



    sampler = FeatureSampler.simulatedAnnealingSamplerFor(space, sa_params=sa_params)

    for i in range(10):
        print(f'Sample #{i}:')
        print(sampler.nextSample())
