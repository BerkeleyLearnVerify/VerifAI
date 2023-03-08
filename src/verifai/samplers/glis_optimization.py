"""GLIS Optimization sampler : Defined only for continuous domains.
For discrete inputs define another sampler"""

from glis.solvers import GLIS
from verifai.samplers.domain_sampler import BoxSampler

class GLISSampler(BoxSampler):
    def __init__(self, domain, n_initial_random):
        super().__init__(domain)
        from numpy import array, zeros, ones

        # Extract lower and upper bounds of Verifai ranges
        dim = domain.flattenedDimension
        #lb = list()
        #ub = list()
        self.lb = zeros(dim)
        self.ub = ones(dim)
        #for bound in self.domain.domains:
        #    lb.append(bound.intervals[0][0])
        #    ub.append(bound.intervals[0][1])
        #self.lb = array(lb)
        #self.ub = array(ub)
        #self.prob = GLIS(bounds=(lb, ub), n_initial_random=n_initial_random)
        self.prob = GLIS(bounds=(self.lb, self.ub), n_initial_random=n_initial_random)


    def nextVector(self, feedback=None):
        if feedback is None or feedback == int(1):
            x = self.prob.initialize()
        else:
            x = self.prob.update(feedback)
        # normalize to [0,1]
        #x = (x - self.lb)/(self.ub - self.lb)

        return tuple(x)

    def getVector(self, feedback=None):
        if feedback is None or feedback == int(1):
            x = self.prob.initialize()
        else:
            x = self.prob.update(feedback)
        # normalize to [0,1]
        #x = (x - self.lb)/(self.ub - self.lb)

        return tuple(x), None