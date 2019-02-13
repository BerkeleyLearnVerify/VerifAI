
"""Samplers generating points in a Domain, possibly subject to specifications.
"""

### Exceptions pertaining to sampling

class SamplingError(Exception):
    """Exception raised if a Sampler is unable to produce a sample"""
    pass

### Samplers defined over fixed Domains

## Abstract samplers

class DomainSampler:
    """Abstract sampler class"""

    def __init__(self, domain):
        self.domain = domain

    def nextSample(self):
        """Generate the next sample"""
        raise NotImplementedError('tried to use abstract Sampler')

    def __iter__(self):
        while True:
            yield self.nextSample()

class ConstrainedSampler(DomainSampler):
    """Abstract DomainSampler constrained by a specification."""

    def __init__(self, domain, spec):
        super().__init__(domain)
        self.specification = spec

class SplitSampler(DomainSampler):
    """Sampler using different strategies for different types of domains"""

    def __init__(self, domain, samplers):
        super().__init__(domain)
        self.samplers = tuple(samplers)

    def nextSample(self):
        return self.domain.rejoinPoints(
            *(sampler.nextSample() for sampler in self.samplers))

    @classmethod
    def fromPartition(cls, domain, partition, defaultSampler=None):
        samplers = []
        remaining = domain
        for predicate, makeSampler in partition:
            component, remaining = remaining.partition(predicate)
            if component:
                samplers.append(makeSampler(component))
            if not remaining:
                break
        if remaining:
            if defaultSampler is None:
                raise RuntimeError('tried to make SplitSampler with'
                                   ' non-exhaustive partition')
            else:
                samplers.append(defaultSampler(remaining))
        assert len(samplers) > 0
        return cls(domain, samplers)

    @classmethod
    def fromPredicate(cls, domain, predicate, leftSampler, rightSampler):
        return cls.fromPartition(domain,
                                 ((predicate, leftSampler),),
                                 rightSampler)

class BoxSampler(DomainSampler):
    """Samplers defined only over unit hyperboxes"""
    def __init__(self, domain):
        self.dimension = domain.standardizedDimension
        if not self.dimension:
            raise RuntimeError(f'{self.__class__.__name__} supports only'
                               ' continuous standardizable Domains')
        super().__init__(domain)

    def nextSample(self):
        sample = self.nextVector()
        return self.domain.unstandardize(sample)

    def nextVector(self):
        raise NotImplementedError('tried to use abstract BoxSampler')

class DiscreteBoxSampler(DomainSampler):
    """Samplers defined only over discrete hyperboxes"""
    def __init__(self, domain):
        self.intervals = domain.standardizedIntervals
        if not self.intervals:
            raise RuntimeError(f'{self.__class__.__name__} supports only'
                               ' discrete standardizable Domains')
        super().__init__(domain)

    def nextSample(self):
        sample = self.nextVector()
        return self.domain.unstandardize(sample)

    def nextVector(self):
        raise NotImplementedError('tried to use abstract DiscreteBoxSampler')
