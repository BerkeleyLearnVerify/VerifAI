"""GLIS Optimization sampler : Defined only for continuous domains.
For discrete inputs define another sampler"""

from glis.solvers import GLIS
from verifai.samplers.domain_sampler import BoxSampler

class GLISSampler(BoxSampler):
    '''
    Integrates the GLIS sampler with VerifAI
    ---
    Parameters:
        domain : FeatureSpace
        params : DotMap
    ---
    Note: see the definition of the GLIS class for the available parameters or the GLIS documentation
    https://pypi.org/project/glis/
    '''
    def __init__(self, domain, params):
        super().__init__(domain)
        from numpy import zeros, ones

        self.rho = None

        dim = domain.flattenedDimension
        self.lb = zeros(dim)
        self.ub = ones(dim)
        self.sampler = GLIS(bounds=(self.lb, self.ub), **params)


    def getVector(self):
        if self.rho is None:
            self.x = self.sampler.initialize()
        elif not self.rho == int(1):
            self.x = self.sampler.update(self.rho)

        return tuple(self.x), None

    def updateVector(self, vector, info, rho):
        self.rho = rho