import time
import progressbar
from verifai.server import ServerTimings
from abc import ABC
import numpy as np
from verifai.modd.odd_sampler import ODDSampler
import pickle
import os

class Evaluator(ABC):
    def __init__(self, eval_params, sampling_params, global_params):
        self.eval_params = eval_params
        self.sampling_params = sampling_params
        self.global_params = global_params
        self.evaluation_results = None
        self.terminate = False
        self.evals = []
        self.samples = {}

    def evaluate(self, monitor):
        pass



class GenericEvaluator(Evaluator):
    def __init__(self, eval_params, sampling_params, global_params):
        super().__init__(eval_params, sampling_params, global_params)


    def sample_simulations(self, num_simulations, num_steps, save_datagen_path, save_scenes_path):
        i = 0
        print(save_datagen_path)
        print(save_scenes_path)
        self.total_sample_time = 0
        self.total_simulate_time = 0
        self.sampling_params.server.maxSteps = num_steps
        if self.eval_params.verbosity >= 1:
            suffix = ''
            suffix = f' for {num_simulations} simulations'
            suffix += f' for {num_steps} timesteps'
            print('Generating data' + suffix)
        if self.eval_params.verbosity >= 2:
            print(f'Server class is {type(self.sampling_params.server)}')

        if self.eval_params.verbosity >= 1:
            bar = progressbar.ProgressBar(max_value=num_simulations)

        try:
            while True:
                try:
                    if self.sampling_params.mode == "eval" or self.sampling_params.mode == "eval_nomonitor":
                        start = time.time()
                        sample = self.sampling_params.server.get_sample()
                        after_sampling = time.time()
                        scene = self.sampling_params.server.sampler.lastScene
                        assert scene
                        print(scene)
                        print("Server", self.sampling_params.server)
                        print("Sampler", self.sampling_params.server.sampler)
                        print("Scenario", self.sampling_params.server.sampler.scenario)
                        # data = self.sampling_params.server.sampler.scenario.sceneToBytes(scene, allowPickle=True)
                        # if save_scenes_path:
                        #     with open(f"{save_scenes_path}_{i}.scene", 'wb') as f: 
                        #         f.write(data)
                    # if self.sampling_params.mode == "eval_nomonitor":
                    #     if save_scenes_path:
                    #         with open(f"{save_scenes_path}_{i}.scene", 'rb') as f:
                    #             data = f.read()
                    #     scene = self.sampling_params.server.sampler.scenario.sceneFromBytes(data)
                    #     assert scene
                    result = self.sampling_params.server._simulate(scene)
                    print(result)
                    if result is None:
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
                    
                    if self.eval_params.verbosity >= 2:
                        print("Sample no: ", i, "\nSample: ", sample, "\nRho: ", rho, "\nRecords: ", result.records)
                    self.samples[i] = (result.records, rho)
                    self.evals.append(int(rho > 0))
                    i += 1
                    if self.eval_params.verbosity >= 1:
                        bar.update(i)
                    if i == 1:
                        t0 = time.time()
                    if i == num_simulations:
                        filehandler = open(f"{save_datagen_path}_{i}.pkl", 'wb') 
                        pickle.dump(self.samples, filehandler)
                        break
                    if i == 1 or i % 10 == 0:
                        filehandler = open(f"{save_datagen_path}_{i}.pkl", 'wb') 
                        pickle.dump(self.samples, filehandler)

                except:
                    if self.eval_params.verbosity >= 1:
                        if i >= num_simulations:
                            print("Sampler has generated all possible samples")
                        else:
                            print("Sampling failed.")
                            break
                    pass
        finally:
            if self.eval_params.verbosity >= 1:
                bar.finish()
            self.sampling_params.server.terminate()
        if self.eval_params.verbosity >= 1:
            print('All simulations generated.')
        print(f"Total of {len(self.evals)} simulations generated.")
        return 0
    
    def generate(self, num_simulations, num_steps, save_path):
        save_scenes_path=self.eval_params.scenes_save_dir
        self.sample_simulations(num_simulations, num_steps, os.path.abspath(save_path), os.path.abspath(save_scenes_path))
        self.evaluation_data = float(np.mean(np.array(self.evals)))
        print(f"-- Eval score: {self.evaluation_data}")
        return self.evaluation_data

    def evaluate(self, monitor):
        self.init_sampler("eval")
        save_path=self.eval_params.datagen_save_dir
        eval_data = self.generate(self.eval_params.eval_num_simulations, self.eval_params.eval_num_steps, save_path)
        self.evaluation_results = {"eval_score": eval_data}
        self.init_sampler("eval_nomonitor")
        save_path=self.eval_params.datagen_nomon_save_dir
        eval_data_nomon = self.generate(self.eval_params.eval_num_simulations, self.eval_params.eval_num_steps, save_path)
        self.evaluation_results["eval_score_nomon"] =  eval_data_nomon
        return self.evaluation_results
    
    def init_sampler(self, mode):
        self.sampling_params.mode = mode
        self.sampling_params.monitor = self.eval_params.save_model_path 
        self.sampling_params = ODDSampler(sampling_params=self.sampling_params).sampling_params