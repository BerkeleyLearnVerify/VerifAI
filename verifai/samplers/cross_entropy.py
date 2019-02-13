"""Cross-entropy samplers"""

import numpy as np
from verifai.samplers.domain_sampler import BoxSampler, DiscreteBoxSampler, \
    DomainSampler, SplitSampler
from verifai.samplers.random_sampler import RandomSampler

class CrossEntropySampler(DomainSampler):
    def __init__(self, domain, ce_params):
        super().__init__(domain)
        self.f = ce_params.f
        self.alpha = ce_params.alpha
        self.thres = ce_params.thres
        self.cont_buckets = ce_params.cont.buckets
        self.cont_dist = ce_params.cont.dist
        self.disc_dist = ce_params.disc.dist
        self.cont_ce = lambda domain: ContinuousCrossEntropySampler(domain=domain,
                                                     buckets=self.cont_buckets,
                                                     dist=self.cont_dist,
                                                     alpha=self.alpha)
        self.disc_ce = lambda domain: DiscreteCrossEntropySampler(domain=domain,
                                                   dist=self.disc_dist,
                                                   alpha=self.alpha)
        partition = (
            (lambda d: d.standardizedDimension, self.cont_ce),
            (lambda d: d.standardizedIntervals, self.disc_ce)
        )
        self.split_sampler = SplitSampler.fromPartition(domain,
                                                        partition,
                                                        RandomSampler)

    def nextSample(self):
        current_sample = self.split_sampler.nextSample()
        f_val = self.f(current_sample)
        if f_val < self.thres:
            for sampler in self.split_sampler.samplers:
                sampler.update_dist()
        return current_sample

class ContinuousCrossEntropySampler(BoxSampler):
    def __init__(self, domain, alpha, buckets=np.array([10]), dist=None):
        super().__init__(domain)
        if len(buckets) > 1:
            assert len(buckets) == self.dimension
        else:
            buckets = np.ones(self.dimension)*buckets[0]
        if dist is not None:
            assert (len(dist) == len(buckets))
        if dist is None:
            dist = np.array([np.ones(int(b))/b for b in buckets])
        self.buckets = buckets
        self.dist = dist
        self.alpha = alpha

    def nextVector(self):
        bucket_samples = np.array([np.random.choice(int(b), p=self.dist[i])
                                   for i, b in enumerate(self.buckets)])
        self.current_sample = bucket_samples
        return tuple(np.random.uniform(bs, bs+1.)/b for b, bs
              in zip(self.buckets, bucket_samples))

    def update_dist(self):
        update_dist = np.array([np.zeros(int(b)) for b in self.buckets])
        for ud,b in zip(update_dist,self.current_sample):
            ud[b] = 1.
        self.dist = self.alpha*self.dist + (1-self.alpha)*update_dist


class DiscreteCrossEntropySampler(DiscreteBoxSampler):
    def __init__(self, domain, alpha, dist=None):
        super().__init__(domain)
        if dist is not None:
            assert (len(dist) == len(domain.standardizedIntervals))
        if dist is None:
            dist = np.array([np.ones(right-left)/(right-left) for
                             left, right in domain.standardizedIntervals])
        self.dist = dist
        self.alpha = alpha

    def nextVector(self):
        self.current_sample=\
            tuple(left + np.random.choice(right-left, p=self.dist[i])
                     for i, (left, right) in enumerate(self.domain.standardizedIntervals))
        return self.current_sample

    def update_dist(self):
        update_dist = np.array([np.zeros(right-left)
                                for left, right in self.domain.standardizedIntervals])
        for i, (ud, b) in enumerate(zip(update_dist, self.current_sample)):
            left, _ = self.domain.standardizedIntervals[i]
            ud[b-left] = 1.

        self.dist = self.alpha * self.dist + (1 - self.alpha) * update_dist
