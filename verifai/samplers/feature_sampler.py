
"""Samplers generating points in a feature space, possibly subject to
specifications.
"""

from verifai.samplers.domain_sampler import SplitSampler
from verifai.samplers.halton import HaltonSampler
from verifai.samplers.cross_entropy import CrossEntropySampler
from verifai.samplers.random_sampler import RandomSampler
from verifai.samplers.bayesian_optimization import BayesOptSampler
from verifai.samplers.simulated_annealing import SimulatedAnnealingSampler

### Samplers defined over FeatureSpaces

class FeatureSampler:
    """Abstract class for samplers over FeatureSpaces."""

    def __init__(self, space):
        self.space = space

    @classmethod
    def samplerFor(cls, space):
        """Convenience function choosing a default sampler for a space."""
        return cls.randomSamplerFor(space)

    @staticmethod
    def randomSamplerFor(space):
        """Creates a random sampler for a given space"""
        return LateFeatureSampler(space, RandomSampler, RandomSampler)

    @staticmethod
    def haltonSamplerFor(space, halton_params):
        """Creates a Halton sampler for a given space.

        Uses random sampling for lengths of feature lists and any
        Domains that are not continous and standardizable.
        """
        def makeDomainSampler(domain):
            return SplitSampler.fromPredicate(
                domain,
                lambda d: d.standardizedDimension > 0,
                lambda domain: HaltonSampler(domain=domain, halton_params=halton_params),
                RandomSampler)
        return LateFeatureSampler(space, RandomSampler, makeDomainSampler)

    @staticmethod
    def crossEntropySamplerFor(space, ce_params):
        """Creates a cross-entropy sampler for a given space.

        Uses random sampling for lengths of feature lists and any Domains
        that are not standardizable."""

        return LateFeatureSampler(space, RandomSampler,
                                lambda domain: CrossEntropySampler(domain=domain,
                                                                ce_params=ce_params))

    @staticmethod
    def simulatedAnnealingSamplerFor(space, sa_params):
        """Creates a cross-entropy sampler for a given space.

        Uses random sampling for lengths of feature lists and any Domains
        that are not standardizable."""

        return LateFeatureSampler(space, RandomSampler,
                                 lambda domain: SimulatedAnnealingSampler(domain=domain,
                                                                    sa_params=sa_params))

    @staticmethod
    def bayesianOptimizationSamplerFor(space, BO_params):
        """Creates a Bayesian Optimization sampler for a given space.

        Uses random sampling for lengths of feature lists and any
        Domains that are not continous and standardizable.
        """

        return LateFeatureSampler(space, RandomSampler,
                                  lambda domain:BayesOptSampler(domain=domain,
                                                                BO_params=BO_params))

    def nextSample(self):
        """Generate the next sample"""
        raise NotImplementedError('tried to use abstract FeatureSampler')

    def __iter__(self):
        while True:
            yield self.nextSample()

class LateFeatureSampler(FeatureSampler):
    """FeatureSampler that works by first sampling only lengths of feature
    lists, then sampling from the resulting fixed-dimensional Domain.

    e.g. LateFeatureSampler(space, RandomSampler, HaltonSampler) creates a
    FeatureSampler which picks lengths uniformly at random and applies
    Halton sampling to each fixed-length space.
    """

    def __init__(self, space, makeLengthSampler, makeDomainSampler):
        super().__init__(space)
        lengthDomain, fixedDomains = space.domains
        if lengthDomain is None:    # space has no feature lists
            self.lengthSampler = None
            self.domainSampler = makeDomainSampler(fixedDomains)
        else:
            self.lengthDomain = lengthDomain
            self.lengthSampler = makeLengthSampler(lengthDomain)
            self.domainSamplers = {
                point: makeDomainSampler(domain)
                for point, domain in fixedDomains.items()
            }

    def nextSample(self):
        if self.lengthSampler is None:
            domainPoint = self.domainSampler.nextSample()
        else:
            length = self.lengthSampler.nextSample()
            domainPoint = self.domainSamplers[length].nextSample()
        return self.space.makePoint(*domainPoint)
