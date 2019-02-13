"""Bayesian Optimization sampler : Defined only for continuous domains.
For discrete inputs define another sampler"""

from verifai.samplers.domain_sampler import DomainSampler
import numpy as np


class BayesOptSampler(DomainSampler):

    def __init__(self, domain, BO_params):
        try:
            import GPyOpt
        except ModuleNotFoundError:
            import sys
            sys.exit('BayesOptSampler requires GPyOpt to be installed')

        super().__init__(domain)
        self.dimension = domain.standardizedDimension
        if not self.dimension:
            raise RuntimeError(f'{self.__class__.__name__} supports only'
                               ' continuous standardizable Domains')
        self.f = BO_params.f
        self.init_num = BO_params.init_num
        self.bounds = []
        for i in range(self.dimension):
            self.bounds.append({'name':'x_'+str(i), 'type': 'continuous',
                                'domain': (0,1)})
        self.X = None
        self.Y = None
        self.BO = None

    def nextSample(self):
        import GPyOpt   # do this here to avoid slow import when unused
        if self.X is None or len(self.X) < self.init_num:
            print("Doing random sampling")
            sample = np.random.uniform(0,1, self.dimension)
            if self.X is None:
                self.X= np.atleast_2d(sample)
                sample = self.domain.unstandardize(sample)
                self.Y = np.atleast_2d(self.f(sample))
            else:
                self.X = np.vstack((self.X, np.atleast_2d(sample)))
                sample = self.domain.unstandardize(sample)
                self.Y = np.vstack((self.Y, np.atleast_2d(self.f(sample))))
            return sample
        print("Doing BO")

        self.BO = GPyOpt.methods.BayesianOptimization(
            f=lambda sample: self.f(self.domain.unstandardize(tuple(sample[0]))),
            domain=self.bounds, X=self.X, Y=self.Y, normalize_Y=False)
        self.BO.run_optimization(1)
        self.X = np.vstack((self.X,np.atleast_2d(self.BO.X[-1])))
        self.Y = np.vstack((self.Y, np.atleast_2d(self.BO.Y[-1])))
        return self.domain.unstandardize(tuple(self.X[-1]))