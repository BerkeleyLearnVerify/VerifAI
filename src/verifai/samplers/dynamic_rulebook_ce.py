import numpy as np
import networkx as nx
from itertools import product
from verifai.samplers.domain_sampler import BoxSampler, DiscreteBoxSampler, \
    DomainSampler, SplitSampler
from verifai.samplers.random_sampler import RandomSampler
from verifai.samplers.cross_entropy import DiscreteCrossEntropySampler
from verifai.samplers.multi_objective import MultiObjectiveSampler
from verifai.rulebook import rulebook

class DynamicRulebookCrossEntropySampler(DomainSampler):
    verbosity = 1
    
    def __init__(self, domain, dce_params):
        super().__init__(domain)
        self.alpha = dce_params.alpha
        self.thres = dce_params.thres
        self.cont_buckets = dce_params.cont.buckets
        self.cont_dist = dce_params.cont.dist
        self.disc_dist = dce_params.disc.dist
        self.cont_ce = lambda domain: ContinuousDynamicCESampler(domain=domain,
                                                     buckets=self.cont_buckets,
                                                     dist=self.cont_dist,
                                                     alpha=self.alpha,
                                                     thres=self.thres)
        self.disc_ce = lambda domain: DiscreteDynamicCESampler(domain=domain,
                                                   dist=self.disc_dist,
                                                   alpha=self.alpha,
                                                   thres=self.thres)
        partition = (
            (lambda d: d.standardizedDimension > 0, self.cont_ce),
            (lambda d: d.standardizedIntervals, self.disc_ce)
        )
        self.split_samplers = {}
        for id, priority_graph in rulebook.priority_graphs.items():
            self.split_samplers[id] = SplitSampler.fromPartition(domain,
                                                                partition,
                                                                RandomSampler)
            for subsampler in self.split_samplers[id].samplers:
                if isinstance(subsampler, ContinuousDynamicCESampler):
                    subsampler.set_graph(priority_graph)
                elif isinstance(subsampler, DiscreteDynamicCESampler):
                    assert True
                else:
                    assert isinstance(subsampler, RandomSampler)
        if not sorted(list(self.split_samplers.keys())) == list(range(len(rulebook.priority_graphs))):
            raise ValueError('Priority graph IDs should be in order and start from 0')
        self.num_segs = len(self.split_samplers)
        self.sampler_idx = 0
        self.using_sampler = rulebook.using_sampler # -1: round-robin
        assert self.using_sampler < self.num_segs

    def getSample(self):
        if self.using_sampler == -1:
            # Sample from each segment in a round-robin fashion
            idx = self.sampler_idx % self.num_segs
        else:
            idx = self.using_sampler
        return self.split_samplers[idx].getSample()

    def update(self, sample, info, rhos):
        # Update each sampler based on the corresponding segment
        try:
            iter(rhos)
        except:
            for i in range(len(self.split_samplers)):
                self.split_samplers[i].update(sample, info, rhos)
            return
        if self.using_sampler == -1:
            if self.verbosity >= 2:
                print('(dynamic_ce.py) Getting feedback from segment', self.sampler_idx % self.num_segs)
            for i in range(len(rhos)):
                self.split_samplers[i].update(sample, info, rhos[i])
        else:
            if self.verbosity >= 2:
                print('(dynamic_ce.py) Getting feedback from segment', self.using_sampler)
            self.split_samplers[self.using_sampler].update(sample, info, rhos[self.using_sampler])
        self.sampler_idx += 1

class ContinuousDynamicCESampler(BoxSampler, MultiObjectiveSampler):
    verbosity = 2

    def __init__(self, domain, alpha, thres,
                 buckets=10, dist=None, restart_every=100):
        super().__init__(domain)
        if isinstance(buckets, int):
            buckets = np.ones(self.dimension) * buckets
        elif len(buckets) > 1:
            assert len(buckets) == self.dimension
        else:
            buckets = np.ones(self.dimension) * buckets[0]
        if dist is not None:
            assert (len(dist) == len(buckets))
        if dist is None:
            dist = np.array([np.ones(int(b))/b for b in buckets])
        self.buckets = buckets # 1*d, each element specifies the number of buckets in that dimension
        self.dist = dist # N*d
        self.alpha = alpha
        self.thres = thres
        self.current_sample = None

    def getVector(self):
        return self.generateSample()
    
    def generateSample(self):
        bucket_samples = np.array([np.random.choice(int(b), p=self.dist[i])
                                   for i, b in enumerate(self.buckets)])
        self.current_sample = bucket_samples
        ret = tuple(np.random.uniform(bs, bs+1.)/b for b, bs
              in zip(self.buckets, bucket_samples))
        return ret, bucket_samples
    
    def updateVector(self, vector, info, rho):
        assert rho is not None
        self.update_dist_from_multi(vector, info, rho)
    
    def update_dist_from_multi(self, sample, info, rho):
        try:
            iter(rho)
        except:
            return
        if len(rho) != self.num_properties:
            return
        
        is_ce = True
        for node in self.priority_graph.nodes:
            if rho[node] >= self.thres[node]:
                is_ce = False
                break
        
        if not is_ce:
            return
        for row, b in zip(self.dist, info):
            row *= self.alpha
            row[b] += 1 - self.alpha

class DiscreteDynamicCESampler(DiscreteCrossEntropySampler):
    pass
