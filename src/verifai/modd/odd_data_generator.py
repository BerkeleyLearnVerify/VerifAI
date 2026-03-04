import time
import progressbar
from verifai.server import ServerTimings
from abc import ABC
from verifai.modd.odd_sampler import ODDSampler
import pickle
import numpy as np

class DataGenerator(ABC):
    def __init__(self,datagen_params, sampling_params,global_params):
        self.datagen_params = datagen_params
        self.sampling_params = sampling_params
        self.global_params = global_params
        self.training_data = None
        self.samples = {}

    def sample_simulations(self):
        pass

    def generate(self):
        pass

class GenericDataGenerator(DataGenerator):
    def __init__(self, datagen_params, sampling_params, global_params):
        if not datagen_params.has_key("preprocessing"):
            datagen_params.preprocessing = None
        if not datagen_params.has_key("labeler"):
            datagen_params.labeler = None


        super().__init__(datagen_params, sampling_params, global_params)

    def sample_simulations(self, num_simulations, num_steps, save_path):
        i = 0
        self.total_sample_time = 0
        self.total_simulate_time = 0
        self.sampling_params.server.maxSteps = num_steps
        if self.datagen_params.verbosity >= 1:
            suffix = ''
            suffix = f' for {num_simulations} simulations'
            suffix += f' for {num_steps} timesteps'
            print('Generating data' + suffix)
        if self.datagen_params.verbosity >= 2:
            print(f'Server class is {type(self.sampling_params.server)}')

        if self.datagen_params.verbosity >= 1:
            bar = progressbar.ProgressBar(max_value=num_simulations)

        try:
            while True:
                try:
                    start = time.time()
                    sample = self.sampling_params.server.get_sample() 
                    after_sampling = time.time()
                    scene = self.sampling_params.server.sampler.lastScene
                    assert scene
                    result = self.sampling_params.server._simulate(scene)
                    if result is None:
                        print(self.sampling_params.server.rejectionFeedback)
                        return self.sampling_params.server.rejectionFeedback
                    print(f"Time steps run for this simulation: {len(result.trajectory)}")
                    value = (0 if self.sampling_params.server.monitor is None
                            else self.sampling_params.server.monitor.evaluate(result))
                    self.sampling_params.server.lastValue = value
                    
                    after_simulation = time.time()
                    timings = ServerTimings(sample_time=(after_sampling - start),
                                            simulate_time=(after_simulation - after_sampling))
                    rho = self.sampling_params.server.lastValue
                    self.total_sample_time += timings.sample_time
                    self.total_simulate_time += timings.simulate_time
                except:
                    if self.datagen_params.verbosity >= 1:
                        if i >= num_simulations:
                            print("Sampler has generated all possible samples")
                        else:
                            print("Sampling failed.")
                if self.datagen_params.verbosity >= 2:
                    print("Sample no: ", i, "\nSample: ", sample, "\nRho: ", rho, "\nRecords: ", result.records)
                self.samples[i] = (result.records, rho)
                if self.datagen_params.verbosity >= 1:
                    bar.update(i)
                i += 1
                if i == 1:
                    t0 = time.time()
                if i == num_simulations:
                    filehandler = open(f"{save_path}_{i}.pkl", 'wb') 
                    pickle.dump(self.samples, filehandler)
                    break
                if i == 1 or i % 10 == 0:
                    print(f"Saving in {save_path}_{i}.pkl")
                    filehandler = open(f"{save_path}_{i}.pkl", 'wb') 
                    pickle.dump(self.samples, filehandler)

        finally:
            if self.datagen_params.verbosity >= 1:
                bar.finish()
            self.sampling_params.server.terminate()
        if self.datagen_params.verbosity >= 1:
            print('All simulations generated.')
        print(f"Total of {len(self.samples)} simulations generated.")
        return 0
    
    def load_simulations(self, load_path):
        print(load_path)
        import os
        print(os.listdir("./out/"))
        with open(load_path, 'rb') as f:
            return pickle.load(f)

    def generate(self, num_simulations, num_steps):
        self.init_sampler()
        save_path=self.datagen_params.datagen_save_dir
        self.sample_simulations(num_simulations, num_steps, save_path)
        self.samples = self.load_simulations(f"{save_path}_{num_simulations}.pkl") 
        if self.datagen_params.preprocessing:
            self.training_data = self.datagen_params.preprocessing(self.samples)
        if self.datagen_params.labeler:
            self.training_data = self.datagen_params.labeler(self.training_data)
        print("Data generated: ", len(self.training_data))
        self.training_data = {"X": self.training_data[:,:-1], "y": self.training_data[:,-1]}
        return self.training_data
    
    def init_sampler(self):
        self.sampling_params.mode = "train"
        self.sampling_params = ODDSampler(sampling_params=self.sampling_params).sampling_params
