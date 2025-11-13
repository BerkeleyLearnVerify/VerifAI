
import os.path

from verifai.samplers import FeatureSampler

def sampleWithFeedback(sampler, num_samples, f):
    samples = []
    for i in range(num_samples):
        sample = sampler.getSample()
        feedback = f(sample)
        sample.update(feedback)
        print(f'Sample #{i}:')
        print(sample)
        samples.append(sample)
    return samples

def checkSaveRestore(sampler, tmpdir, iterations=1):
    path = os.path.join(tmpdir, 'blah.dat')
    feedback = None
    for i in range(iterations):
        sampler.saveToFile(path)
        # sample1 = sampler.nextSample(feedback)
        # sample2 = sampler.nextSample(-1)
        sample1 = sampler.getSample()
        sample1.update(-1)
        sample2 = sampler.getSample()
        sampler = FeatureSampler.restoreFromFile(path)
        # sample1b = sampler.nextSample(feedback)
        # sample2b = sampler.nextSample(-1)
        sample1b = sampler.getSample()
        sample1b.update(-1)
        sample2b = sampler.getSample()
        sample2b.update(1)
        assert sample1.staticSample != sample2.staticSample
        assert sample1.staticSample == sample1b.staticSample
        assert sample2.staticSample == sample2b.staticSample
        sampler.saveToFile(path)
        # sample3 = sampler.nextSample(1)
        sample3 = sampler.getSample()
        sampler = FeatureSampler.restoreFromFile(path)
        sample3b = sampler.getSample()
        assert sample3.staticSample not in (sample1.staticSample, sample2.staticSample)
        assert sample3.staticSample == sample3b.staticSample
        # feedback = 1
        sample3b.update(1)
