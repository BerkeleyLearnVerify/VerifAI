"""GLIS Optimization sampler : Defined only for continuous domains.
For discrete inputs define another sampler"""

from glis.solvers import GLIS
from verifai import RandomSampler, RejectionSampler, LateFeatureSampler
from verifai.samplers.domain_sampler import BoxSampler, SplitSampler

def makeRandomSampler(domain):
    """Utility function making a random sampler for a domain."""
    sampler = RandomSampler(domain)
    if domain.requiresRejection:
        sampler = RejectionSampler(sampler)
    return sampler

def glisSamplerFor(space, n_initial_random):
    """Creates a GLIS Optimization sampler for a given space.
    Uses random sampling for lengths of feature lists and any
    Domains that are not continous and standardizable.
    """

    def makeDomainSampler(domain):
        return SplitSampler.fromPredicate(
            domain,
            lambda d: d.standardizedDimension > 0,
            lambda domain: GLISSampler(domain=domain,
                                           n_initial_random=n_initial_random),
            makeRandomSampler)

    return LateFeatureSampler(space, RandomSampler, makeDomainSampler)

class GLISSampler(BoxSampler):
    def __init__(self, domain, n_initial_random):
        super().__init__(domain)
        from numpy import array

        # Extract lower and upper bounds of Verifai ranges
        lb = list()
        ub = list()
        for bound in self.domain.domains:
            lb.append(bound.intervals[0][0])
            ub.append(bound.intervals[0][1])
        self.lb = array(lb)
        self.ub = array(ub)
        self.prob = GLIS(bounds=(lb, ub), n_initial_random=n_initial_random)


    def nextVector(self, feedback=None):
        if feedback is None or feedback == int(1):
            x = self.prob.initialize()
        else:
            x = self.prob.update(feedback)
        # normalize to [0,1]
        x = (x - self.lb)/(self.ub - self.lb)

        return tuple(x)