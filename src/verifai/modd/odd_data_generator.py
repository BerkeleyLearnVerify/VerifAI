import pickle
import os
from abc import ABC

from verifai.modd.odd_sampler import ODDSampler


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
        self.sampling_params.server.maxSteps = num_steps
        if self.datagen_params.verbosity >= 1:
            suffix = ''
            suffix = f' for {num_simulations} simulations'
            suffix += f' for {num_steps} timesteps'
            print('Generating data' + suffix)
        if self.datagen_params.verbosity >= 2:
            print(f'Server class is {type(self.sampling_params.server)}')

        try:
            while True:
                try:
                    sample, _, _ = self.sampling_params.server.run_server()
                    scene = self.sampling_params.server.sampler.lastScene
                    assert scene
                    result = self.sampling_params.server._simulate(scene)
                    if result is None:
                        print(self.sampling_params.server.rejectionFeedback)
                        return self.sampling_params.server.rejectionFeedback
                    value = (0 if self.sampling_params.server.monitor is None
                            else self.sampling_params.server.monitor.evaluate(result))
                    self.sampling_params.server.lastValue = value
                    rho = self.sampling_params.server.lastValue
                    if self.datagen_params.verbosity >= 2:
                        print("Sample no: ", i, "\nSample: ", sample, "\nRho: ", rho, "\nRecords: ", result.records)
                    self.samples[i] = (result.records, rho)
                    i += 1
                    if i == num_simulations:
                        with open(f"{save_path}training_{i}.pkl", 'wb') as filehandler:
                            pickle.dump(self.samples, filehandler)
                        break
                    if i == 1 or i % 10 == 0:
                        print(f"Saving in {save_path}training_{i}.pkl")
                        with open(f"{save_path}training_{i}.pkl", 'wb') as filehandler:
                            pickle.dump(self.samples, filehandler)
                except Exception:
                    if self.datagen_params.verbosity >= 1:
                        if i >= num_simulations:
                            print("Sampler has generated all possible samples")
                        else:
                            print("Sampling failed.")
                except KeyboardInterrupt:
                    break
                

        finally:
            self.sampling_params.server.terminate()
        if self.datagen_params.verbosity >= 1:
            print('All simulations generated.')
        print(f"Total of {len(self.samples)} simulations generated.")
        return 0
    
    def load_simulations(self, load_path):
        with open(load_path, 'rb') as f:
            return pickle.load(f)

    def generate(self, num_simulations, num_steps):
        self.init_sampler()
        save_path=self.datagen_params.datagen_save_dir
        os.makedirs(save_path, exist_ok=True)
        self.sample_simulations(num_simulations, num_steps, save_path)
        filename = os.path.join(save_path, f"training_{num_simulations}.pkl")
        self.samples = self.load_simulations(filename) 
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