
"""Samplers generating points in a feature space, possibly subject to
specifications.
"""

import random

import dill
from dotmap import DotMap
import numpy as np
from abc import ABC, abstractmethod
from contextlib import contextmanager

from verifai.features import FilteredDomain, TimeSeriesFeature
from verifai.samplers.domain_sampler import SplitSampler, TerminationException
from verifai.samplers.rejection import RejectionSampler
from verifai.samplers.halton import HaltonSampler
from verifai.samplers.cross_entropy import CrossEntropySampler
from verifai.samplers.random_sampler import RandomSampler
from verifai.samplers.multi_armed_bandit import MultiArmedBanditSampler
from verifai.samplers.eg_sampler import EpsilonGreedySampler
from verifai.samplers.bayesian_optimization import BayesOptSampler
from verifai.samplers.simulated_annealing import SimulatedAnnealingSampler
from verifai.samplers.grid_sampler import GridSampler

class Sample(ABC):
    def __init__(self, space):
        self.space = space
        self.dynamicSampleHistory = []

    @property
    @abstractmethod
    def staticSample(self):
        pass

    @abstractmethod
    def _getDynamicSample(self, info):
        pass

    def getDynamicSample(self, info=None):
        sample = self._getDynamicSample(info)
        self.dynamicSampleHistory.append(sample)
        return sample

    @abstractmethod
    def update(self, rho):
        pass

### Samplers defined over FeatureSpaces

class FeatureSampler(ABC):
    """Abstract class for samplers over FeatureSpaces."""

    def __init__(self, space):
        self.space = space
        self.last_sample = None

    @classmethod
    def samplerFor(cls, space):
        """Convenience function choosing a default sampler for a space."""
        return cls.randomSamplerFor(space)

    @staticmethod
    def randomSamplerFor(space):
        """Creates a random sampler for a given space"""
        return LateFeatureSampler(space, RandomSampler, RandomSampler)

    @staticmethod
    def haltonSamplerFor(space, halton_params=None):
        """Creates a Halton sampler for a given space.

        Uses random sampling for lengths of feature lists and any
        Domains that are not continous and standardizable.
        """
        if halton_params is None:
            halton_params = default_sampler_params('halton')
        def makeDomainSampler(domain):
            return SplitSampler.fromPredicate(
                domain,
                lambda d: d.standardizedDimension > 0,
                lambda domain: HaltonSampler(domain=domain,
                                             halton_params=halton_params),
                makeRandomSampler)
        return LateFeatureSampler(space, RandomSampler, makeDomainSampler)

    @staticmethod
    def crossEntropySamplerFor(space, ce_params=None):
        """Creates a cross-entropy sampler for a given space.

        Uses random sampling for lengths of feature lists and any Domains
        that are not standardizable.
        """
        if ce_params is None:
            ce_params = default_sampler_params('ce')
        return LateFeatureSampler(space, RandomSampler,
            lambda domain: CrossEntropySampler(domain=domain,
                                               ce_params=ce_params))

    @staticmethod
    def epsilonGreedySamplerFor(space, eg_params=None):
        """Creates an epsilon-greedy sampler for a given space.

        Uses random sampling for lengths of feature lists and any Domains
        that are not standardizable.
        """
        if eg_params is None:
            eg_params = default_sampler_params('eg')
        return LateFeatureSampler(space, RandomSampler,
            lambda domain: EpsilonGreedySampler(domain=domain,
                                                eg_params=eg_params))

    @staticmethod
    def multiArmedBanditSamplerFor(space, mab_params=None):
        """Creates a multi-armed bandit sampler for a given space.

        Uses random sampling for lengths of feature lists and any Domains
        that are not standardizable.
        """
        if mab_params is None:
            mab_params = default_sampler_params('mab')
        return LateFeatureSampler(space, RandomSampler,
            lambda domain: MultiArmedBanditSampler(domain=domain,
                                                   mab_params=mab_params))

    @staticmethod
    def gridSamplerFor(space, grid_params=None):
        """Creates a grid sampler for a given space.

        Uses random sampling for lengths of feature lists and any Domains
        that are not standardizable."""

        def makeDomainSampler(domain):
            return SplitSampler.fromPredicate(
                domain,
                lambda d: d.isStandardizable,
                lambda domain: GridSampler(domain=domain,
                                           grid_params=grid_params),
                makeRandomSampler)
        return LateFeatureSampler(space, RandomSampler, makeDomainSampler)

    @staticmethod
    def simulatedAnnealingSamplerFor(space, sa_params=None):
        """Creates a cross-entropy sampler for a given space.

        Uses random sampling for lengths of feature lists and any Domains
        that are not continuous and standardizable.
        """
        if sa_params is None:
            sa_params = default_sampler_params('sa')
        def makeDomainSampler(domain):
            return SplitSampler.fromPredicate(
                domain,
                lambda d: d.standardizedDimension > 0,
                lambda domain: SimulatedAnnealingSampler(domain=domain,
                                                         sa_params=sa_params),
                makeRandomSampler)
        return LateFeatureSampler(space, RandomSampler, makeDomainSampler)

    @staticmethod
    def bayesianOptimizationSamplerFor(space, BO_params=None):
        """Creates a Bayesian Optimization sampler for a given space.

        Uses random sampling for lengths of feature lists and any
        Domains that are not continous and standardizable.
        """
        if BO_params is None:
            BO_params = default_sampler_params('bo')
        def makeDomainSampler(domain):
            return SplitSampler.fromPredicate(
                domain,
                lambda d: d.standardizedDimension > 0,
                lambda domain: BayesOptSampler(domain=domain,
                                               BO_params=BO_params),
                makeRandomSampler)
        return LateFeatureSampler(space, RandomSampler, makeDomainSampler)

    def update(self, sample_id, rho):
        """Update the state of the sampler after evaluating a sample."""
        pass

    @abstractmethod
    def getSample(self):
        """Returns a `Sample` object"""
        pass

    def set_graph(self, graph):
        self.scenario.set_graph(graph)

    def saveToFile(self, path):
        with open(path, 'wb') as outfile:
            randState = random.getstate()
            numpyRandState = np.random.get_state()
            allState = (randState, numpyRandState, self)
            dill.dump(allState, outfile)

    @staticmethod
    def restoreFromFile(path):
        with open(path, 'rb') as infile:
            allState = dill.load(infile)
            randState, numpyRandState, sampler = allState
            random.setstate(randState)
            np.random.set_state(numpyRandState)
            return sampler

    def __iter__(self):
        try:
            while True:
                sample = self.getSample()
                rho = yield sample
                sample.update(rho)
        except TerminationException:
            return

class LateFeatureSample(Sample):
    def __init__(self, space, staticSample, dynamicSampleList, updateCallback):
        super().__init__(space)
        self._staticSample = staticSample
        self._dynamicSampleList = dynamicSampleList
        self._updateCallback = updateCallback
        self._i = 0

    @property
    def staticSample(self):
        return self._staticSample

    def _getDynamicSample(self, info):
        if self.space.timeBound == 0:
            raise RuntimeError("Called `getDynamicSample` with `timeBound` of `FeatureSpace` set to 0")

        if self._i >= self.space.timeBound:
            raise RuntimeError("Exceeded `timeBound` of `FeatureSpace`")
        
        assert self._i < len(self._dynamicSampleList)

        dynamic_sample = self._dynamicSampleList[self._i]
        self._i += 1

        return dynamic_sample

    def update(self, rho):
        return self._updateCallback(rho)

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
            self.domainSamplers = {None: makeDomainSampler(fixedDomains)}
        else:
            self.lengthDomain = lengthDomain
            self.lengthSampler = makeLengthSampler(lengthDomain)
            self.domainSamplers = {
                point: makeDomainSampler(domain)
                for point, domain in fixedDomains.items()
            }

        self.id_metadata_dict = {}
        self._last_id = 0

    def get_info_id(self, info, length, sample):
        self._last_id += 1
        self.id_metadata_dict[self._last_id] = (info, length, sample)
        return self._last_id

    def getSample(self):
        if self.lengthSampler is None:
            length, info1 = None, None
        else:
            length, info1 = self.lengthSampler.getSample()

        domainPoint, info2 = self.domainSamplers[length].getSample()
        info = (info1, info2)
        
        sample_id = self.get_info_id(info, length, domainPoint)
        update_callback = lambda rho: self.update(sample_id, rho)

        # Make static points and iterable over dynamic points
        static_features = [v for v in domainPoint._asdict().items()
                            if v[0] in self.space.staticFeatureNamed]
        dynamic_features = [v for v in domainPoint._asdict().items()
                            if v[0] not in self.space.staticFeatureNamed]
        static_point = self.space.makeStaticPoint(*[v[1] for v in static_features])

        dynamic_points = []
        if any(isinstance(f, TimeSeriesFeature) for f in self.space.features):
            for t in range(self.space.timeBound):
                point_dict = {}

                for f, val in dynamic_features:
                    if not self.space.featureNamed[f].lengthDomain:
                        point_dict[f] = val[t]
                    else:
                        feat_list = []
                        for l in range(len(val)):
                            feat_list.append(val[l][t])
                        point_dict[f] = tuple(feat_list)

                dynamic_points.append(self.space.makeDynamicPoint(*point_dict.values()))

        return LateFeatureSample(self.space, static_point, dynamic_points, update_callback)

    def update(self, sample_id, rho):
        info, lengthPoint, domainPoint = self.id_metadata_dict[sample_id]

        if self.lengthSampler is None:
            self.domainSamplers[None].update(domainPoint, info[1], rho)
        else:
            self.lengthSampler.update(domainPoint, info[0], rho)

            self.domainSamplers[lengthPoint].update(domainPoint, info[1], rho)
### Utilities

def makeRandomSampler(domain):
    """Utility function making a random sampler for a domain."""
    sampler = RandomSampler(domain)
    if domain.requiresRejection:
        sampler = RejectionSampler(sampler)
    return sampler

def default_sampler_params(sampler_type):
    if sampler_type == 'halton':
        return DotMap(sample_index=0, bases_skipped=0)
    elif sampler_type in ('ce', 'eg', 'mab'):
        cont = DotMap(buckets=5, dist=None)
        disc = DotMap(dist=None)
        return DotMap(alpha=0.9, thres=0.0, cont=cont, disc=disc)
    elif sampler_type == 'bo':
        return DotMap(init_num=5)
    return DotMap()
