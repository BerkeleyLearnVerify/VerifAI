import numpy as np
from verifai.samplers.domain_sampler import BoxSampler, DomainSampler
from verifai.samplers.multi_objective import MultiObjectiveSampler

class DynamicRulebookCrossEntropySampler(DomainSampler):
    verbosity = 1
    
    def __init__(self, domain, dce_params):
        super().__init__(domain)
        rb = getattr(dce_params, 'rulebook', None)
        if rb is None:
            raise ValueError('dce_params.rulebook must be set to a Rulebook instance')
        self.alpha = dce_params.alpha
        self.thres = dce_params.thres
        self.cont_buckets = dce_params.cont.buckets
        self.cont_dist = dce_params.cont.dist
        self.cont_ce = lambda domain, priority_graph: ContinuousDynamicCESampler(domain=domain,
                                                     buckets=self.cont_buckets,
                                                     dist=self.cont_dist,
                                                     alpha=self.alpha,
                                                     thres=self.thres,
                                                     priority_graph=priority_graph)
        self.split_samplers = {}
        for id, priority_graph in rb.priority_graphs.items():
            self.split_samplers[id] = self.cont_ce(domain, priority_graph)
        if not sorted(list(self.split_samplers.keys())) == list(range(len(rb.priority_graphs))):
            raise ValueError('Priority graph IDs should be in order and start from 0')
        self.num_segs = len(self.split_samplers)
        self.sampler_idx = 0
        self.using_sampler = rb.using_sampler # -1: round-robin
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
        except Exception as e:
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
                 buckets=10, dist=None, restart_every=100, priority_graph=None):
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
        if priority_graph is not None:
            self.set_graph(priority_graph)

    def getVector(self):
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
        assert len(rho) == self.num_properties
        
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
