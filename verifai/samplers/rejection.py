"""Rejection sampling"""

from verifai.utils.utils import RejectionException
from verifai.samplers.domain_sampler import ConstrainedSampler, SamplingError

class RejectionSampler(ConstrainedSampler):
    """Enforces a spec over some other sampler by rejection.

    RejectionSampler(RandomSampler(domain), spec)
    """

    def __init__(self, sampler, spec=None, maxRejections=1000):
        super().__init__(sampler.domain, spec)
        self.sampler = sampler
        self.maxRejections = maxRejections

    def nextSample(self, feedback=None):
        reject = True
        samples = 0
        while reject:
            if samples >= self.maxRejections:
                raise SamplingError(
                    f'exceeded RejectionSampler limit of {samples} rejections')
            samples += 1
            try:
                sample = self.sampler.nextSample(feedback)
                if self.specification is not None:
                    reject = not self.specification.isSatisfiedBy(sample)
                else:
                    reject = False
            except RejectionException:
                reject = True
        return sample

    def __repr__(self):
        return (f'RejectionSampler({self.sampler}, {self.spec}, '
                'maxRejections={self.maxRejections})')
