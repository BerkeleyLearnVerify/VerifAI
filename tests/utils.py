
import os.path

from verifai.samplers import FeatureSampler

def sampleWithFeedback(sampler, num_samples, f):
    samples = []
    for i in range(num_samples):
        sample = sampler.getSample()
        feedback = f(sample)
        sample.complete(feedback)
        print(f'Sample #{i}:')
        print(sample)
        samples.append(sample)
    return samples

def checkSaveRestore(sampler, tmpdir, iterations=1):
    path = os.path.join(tmpdir, 'blah.dat')
    feedback = None
    for i in range(iterations):
        sampler.saveToFile(path)
        sample1 = sampler.getSample().complete(-1)
        sample2 = sampler.getSample().complete(0)
        sampler = FeatureSampler.restoreFromFile(path)
        sample1b = sampler.getSample().complete(-1)
        sample2b = sampler.getSample().complete(1)
        assert sample1 != sample2
        assert sample1 == sample1b
        assert sample2 == sample2b
        sampler.saveToFile(path)
        sample3 = sampler.getSample().complete(0)
        sampler = FeatureSampler.restoreFromFile(path)
        sample3b = sampler.getSample().complete(1)
        assert sample3 not in (sample1, sample2)
        assert sample3 == sample3b
