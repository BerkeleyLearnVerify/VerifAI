"""Specialized server for using Scenic's dynamic simulator interfaces."""

import time

from dotmap import DotMap

from verifai.server import Server
from verifai.samplers.scenic_sampler import ScenicSampler
from scenic.core.simulators import SimulationCreationError
from scenic.core.external_params import VerifaiSampler
from scenic.core.distributions import RejectionException
import ray
from ray.util import ActorPool

ray.init(ignore_reinit_error=True)

class ScenicServer(Server):
    def __init__(self, sampling_data, monitor, options={}):
        if sampling_data.sampler is None:
            raise RuntimeError('ScenicServer created without sampler')
        self.sampler = sampling_data.sampler
        if not isinstance(self.sampler, ScenicSampler):
            raise RuntimeError('only a ScenicSampler can be used with ScenicServer')
        self.sample_space = self.sampler.space
        self.simulator = self.sampler.scenario.getSimulator()
        extSampler = self.sampler.scenario.externalSampler
        if extSampler is None:
            self.rejectionFeedback = None
        else:
            self.rejectionFeedback = extSampler.rejectionFeedback
        self.monitor = monitor
        self.lastValue = None
        defaults = DotMap(maxSteps=None, verbosity=0, maxIterations=1)
        defaults.update(options)
        self.maxSteps = defaults.maxSteps
        self.verbosity = defaults.verbosity
        self.maxIterations = defaults.maxIterations

    def run_server(self):
        sample = self.sampler.nextSample(self.lastValue)
        scene = self.sampler.lastScene
        assert scene
        result = self._simulate(scene)
        if result is None:
            self.lastValue = self.rejectionFeedback
        else:
            self.lastValue = (0 if self.monitor is None
                              else self.monitor.evaluate(result.trajectory))
        return sample, self.lastValue

    def _simulate(self, scene):
        startTime = time.time()
        if self.verbosity >= 1:
            print('  Beginning simulation...')
        try:
            result = self.simulator.simulate(scene,
                maxSteps=self.maxSteps, verbosity=self.verbosity,
                maxIterations=self.maxIterations)
        except SimulationCreationError as e:
            if self.verbosity >= 1:
                print(f'  Failed to create simulation: {e}')
            return None
        if self.verbosity >= 1:
            totalTime = time.time() - startTime
            print(f'  Ran simulation in {totalTime:.4g} seconds.')
        return result

    def terminate(self):
        pass

class DummySampler(VerifaiSampler):

    def nextSample(self, feedback):
        return self.last_sample

@ray.remote
class SampleSimulator():

    def __init__(self, scenic_path, worker_num, monitor, options={}):
        self.sampler = ScenicSampler.fromScenario(scenic_path, maxIterations=1)
        # reset self.sampler.scenario.externalSampler to dummy sampler
        # that reads argument
        self.sampler.scenario.externalSampler = DummySampler(self.sampler.scenario.externalParams,
        self.sampler.scenario.params)
        self.simulator = self.sampler.scenario.getSimulator()
        self.monitor = monitor
        # carla_map = self.sampler.scenario.externalParams.carla_map
        # assert carla_map, 'Map must be specified in Scenic script'
        # self.simulator = CarlaSimulator(map=carla_map, port=2002 + 2 * worker_num)
        defaults = DotMap(maxSteps=None, verbosity=0, maxIterations=1)
        defaults.update(options)
        self.maxSteps = defaults.maxSteps
        self.verbosity = defaults.verbosity
        self.maxIterations = defaults.maxIterations

    def get_sample(self, sample):
        self.sampler.scenario.externalSampler.last_sample = sample
        sample = self.sampler.nextSample(sample)

    def simulate(self, sample):
        '''
        Need to generate scene from sample here.
        '''
        self.sampler.scenario.externalSampler.last_sample = sample
        sample = self.sampler.nextSample(sample)
        scene = self.sampler.lastScene
        startTime = time.time()
        if self.verbosity >= 1:
            print('  Beginning simulation...')
        try:
            result = self.simulator.simulate(scene,
                maxSteps=self.maxSteps, verbosity=self.verbosity,
                maxIterations=self.maxIterations)
        except SimulationCreationError as e:
            if self.verbosity >= 1:
                print(f'  Failed to create simulation: {e}')
            return None
        if self.verbosity >= 1:
            totalTime = time.time() - startTime
            print(f'  Ran simulation in {totalTime:.4g} seconds.')
            print(f'Result is {result}')
        if result is None:
            self.lastValue = self.rejectionFeedback
        else:
            self.lastValue = (0 if self.monitor is None
                              else self.monitor.evaluate(result.trajectory))
        return sample, self.lastValue

class ParallelScenicServer(ScenicServer):

    def __init__(self, total_workers, n_iters, sampling_data, scenic_path, monitor, options={}):
        self.total_workers = total_workers
        self.n_iters = n_iters
        sampler = ScenicSampler.fromScenario(scenic_path)
        sampling_data.sampler = sampler
        super().__init__(sampling_data, monitor, options)
        print(f'Sampler class is {type(self.sampler)}')
        self.sample_simulators = [SampleSimulator.remote(scenic_path, i, monitor, options)
        for i in range(self.total_workers)]
        self.simulator_pool = ActorPool(self.sample_simulators)

    def run_server(self):
        '''
        The following need to happen here:

        1. the external sampler is called and the next set of samples retrieved.
        2. the sample is sent to the appropriate SampleSimulator object (self.sample_simulators)
        3. SampleSimulator runs the simulation and returns the result here.
        4. return sample, rho
        '''
        # externalSampler.sample called here
        startTime = time.time()
        samples = []
        while len(samples) < self.n_iters:
            self.sampler.scenario.externalSampler.sample(self.lastValue)
            sample = self.sampler.scenario.externalSampler.cachedSample
            # sample = Samplable.sampleAll(self.sampler.scenario.dependencies)
            sim = self.sample_simulators[0]
            try:
                ray.get(sim.get_sample.remote(sample))
                samples.append(sample)
            except SimulationCreationError as e:
                if self.verbosity >= 1:
                    print(f'  Failed to create simulation: {e}')
                return None
            except RejectionException as e:
                continue
        # only works for passive samplers
        results = self.simulator_pool.map_unordered(lambda a, v: a.simulate.remote(v), samples)
            # if self.verbosity >= 1:
            #     totalTime = time.time() - startTime
            #     print(f'  Ran simulation in {totalTime:.4g} seconds.')
        return results
