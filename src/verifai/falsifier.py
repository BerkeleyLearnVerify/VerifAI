from abc import ABC
from verifai.server import Server, ParallelServer
from verifai.scenic_server import ScenicServer, ParallelScenicServer
from verifai.samplers import TerminationException
from dotmap import DotMap
from verifai.monitor import mtl_specification, specification_monitor, multi_objective_monitor
from verifai.error_table import error_table
import numpy as np
import pickle
import progressbar
import ray
from statsmodels.stats.proportion import proportion_confint
import time

def parallelized(server_class):
    if server_class == Server:
        return ParallelServer
    elif server_class == ScenicServer:
        return ParallelScenicServer

class falsifier(ABC):
    def __init__(self, monitor, sampler_type=None, sampler=None, sample_space=None,
                 falsifier_params=None, server_options={}, server_class=Server):
        self.sample_space = sample_space
        self.sampler_type = sampler_type
        self.sampler = sampler
        self.samples = {}
        self.monitor = monitor

        params = DotMap(
            save_error_table=True, save_safe_table=True,
            error_table_path=None, safe_table_path=None,
            n_iters=1000, ce_num_max=np.inf, fal_thres=0,
            sampler_params=None, verbosity=0,
        )
        if falsifier_params is not None:
            params.update(falsifier_params)
        if params.sampler_params is None:
            params.sampler_params = DotMap(thres=params.fal_thres)
        self.save_error_table = params.save_error_table
        self.save_safe_table = params.save_safe_table
        self.error_table_path = params.error_table_path
        self.safe_table_path = params.safe_table_path
        if not hasattr(self, 'num_workers'):
            self.num_workers = 1
        self.n_iters, self.ce_num_max = params.n_iters, params.ce_num_max
        if self.n_iters is None:
            self.max_time = params.max_time
        else:
            self.max_time = None
        self.fal_thres = params.fal_thres
        self.sampler_params = params.sampler_params
        self.verbosity = params.verbosity

        server_params = DotMap(init=True)
        if server_options is not None:
            server_params.update(server_options)
        if server_params.init:
            self.init_server(server_params, server_class)
            self.init_error_table()

    def init_server(self, server_options, server_class):
        if self.verbosity >= 1:
            print("Initializing server")
        sampling_data = DotMap()
        if self.sampler_type is None:
            self.sampler_type = 'random'
        sampling_data.sampler_type = self.sampler_type
        sampling_data.sample_space = self.sample_space
        sampling_data.sampler_params = self.sampler_params
        sampling_data.sampler = self.sampler

        self.server = server_class(sampling_data, self.monitor, options=server_options)

    def init_error_table(self):
        # Initializing error table
        if self.save_error_table:
            self.error_table = error_table(space = self.server.sample_space)
        if self.save_safe_table:
            self.safe_table = error_table(space = self.server.sample_space)

    def populate_error_table(self, sample, rho, error=True):
        if error:
            self.error_table.update_error_table(sample, rho)
            if self.error_table_path:
                self.write_table(self.error_table.table, self.error_table_path)
        else:
            self.safe_table.update_error_table(sample, rho)
            if self.safe_table_path:
                self.write_table(self.safe_table.table, self.safe_table_path)

    @staticmethod
    def write_table(table, path):
        if len(table) <= 1:
            table.to_csv(path)
        else:
            table.tail(1).to_csv(path, mode='a', header=False)

    def analyze_error_table(self, analysis_params= None, error=None):
        if self.save_error_table and (error is None or error is True):
            self.error_analysis = self.error_table.analyze(analysis_params)

            if 'k_closest' in self.error_analysis:
                self.error_analysis.k_closest_samples = \
                    [self.samples[i] for i in self.error_analysis.k_closest]
            if 'random' in self.error_analysis:
                self.error_analysis.random_samples = \
                    [self.samples[i] for i in self.error_analysis.random]
        if self.save_safe_table and (error is None or error is False):
            self.safe_analysis = self.safe_table.analyze(analysis_params)

            if 'k_closest' in self.safe_analysis:
                self.safe_analysis.k_closest_samples = \
                    [self.samples[i] for i in self.safe_analysis.k_closest]
            if 'random' in self.safe_analysis:
                self.safe_analysis.random_samples = \
                    [self.samples[i] for i in self.safe_analysis.random]

    def get_confidence_interval(self, confidence_level=0.95):
        N = len(self.samples)
        c = len(self.error_table.table)
        return proportion_confint(c, N, alpha=1 - confidence_level, method='beta')

    def run_falsifier(self):
        i = 0
        ce_num = 0
        counterexamples = []
        server_samples = []
        rhos = []
        # print(f'Running falsifier; server class is {type(self.server)}')
        if self.n_iters is not None:
            bar = progressbar.ProgressBar(max_value=self.n_iters)
        else:
            widgets = ['Scenes generated: ', progressbar.Counter('%(value)d'),
               ' (', progressbar.Timer(), ')']
            bar = progressbar.ProgressBar(widgets=widgets)
        # bar = progressbar.ProgressBar(max_value=self.n_iters)
        while True:
            try:
                sample, rho = self.server.run_server()
                # print(f'sample = {sample}, rho = {rho}')
            except TerminationException:
                if self.verbosity >= 1:
                    print("Sampler has generated all possible samples")
                break
            # if self.verbosity >= 1:
            #     print("Sample no: ", i, "\nSample: ", sample, "\nRho: ", rho)
            self.samples[i] = sample
            server_samples.append(sample)
            counterexamples.append(rho <= self.fal_thres)
            rhos.append(rho)
            i += 1
            bar.update(i)
            if i == 1:
                t0 = time.time()
            if self.n_iters is not None and i == self.n_iters:
                break
            if self.max_time is not None and time.time() - t0 >= self.max_time:
                break
        if isinstance(self.monitor, multi_objective_monitor):
            counterexamples = self.server.sampler.scenario.externalSampler.sampler.domainSampler.split_sampler.samplers[0].counterexample_values
        for sample, ce, rho in zip(server_samples, counterexamples, rhos):
            # if isinstance(rho, (list, tuple)):
            #     check_var = rho[-1]
            # else:
            #     check_var = rho
            if ce:
                if self.save_error_table:
                    self.populate_error_table(sample, rho)
                ce_num = ce_num + 1
                if ce_num >= self.ce_num_max:
                    break
            elif self.save_safe_table:
                self.populate_error_table(sample, rho, error=False)
        self.server.terminate()


class generic_falsifier(falsifier):
    def __init__(self,  monitor=None, sampler_type= None, sample_space=None, sampler=None,
                 falsifier_params=None, server_options={}, server_class=Server, scenic_path=None,
                 scenario_params={}):
        if monitor is None:
            class monitor(specification_monitor):
                def __init__(self):
                    def specification(traj):
                        return np.inf
                    super().__init__(specification)
            monitor = monitor()

        super().__init__(sample_space=sample_space, sampler_type=sampler_type,
                         monitor=monitor, falsifier_params=falsifier_params, sampler=sampler,
                         server_options=server_options, server_class=server_class)

class mtl_falsifier(generic_falsifier):
    def __init__(self, specification, sampler_type = None, sample_space=None, sampler=None,
                 falsifier_params=None, server_options={}, server_class=Server):
        monitor = mtl_specification(specification=specification)
        super().__init__(sample_space=sample_space, sampler_type=sampler_type,
                         monitor=monitor, falsifier_params=falsifier_params, sampler=sampler,
                         server_options=server_options, server_class=server_class)

class parallel_falsifier(falsifier):

    def __init__(self, monitor, sampler_type=None, sample_space=None,
                 falsifier_params=None, server_options={}, server_class=Server, num_workers=5,
                 scenic_path=None, use_carla=False):
        self.scenic_path = scenic_path
        self.num_workers = num_workers
        self.use_carla = use_carla
        super().__init__(sample_space=sample_space, sampler_type=sampler_type,
                         monitor=monitor, falsifier_params=falsifier_params, sampler=None,
                         server_options=server_options, server_class=parallelized(server_class))

class generic_parallel_falsifier(parallel_falsifier):
    def __init__(self, monitor=None, sampler_type= None, sample_space=None, sampler=None,
                 falsifier_params=None, server_options={}, server_class=Server, num_workers=5,
                 scenic_path=None, use_carla=False, scenario_params={}):
        if monitor is None:
            class monitor(specification_monitor):
                def __init__(self):
                    def specification(traj):
                        return np.inf
                    super().__init__(specification)
            monitor = monitor()
        self.scenario_params = scenario_params

        super().__init__(sample_space=sample_space, sampler_type=sampler_type,
                         monitor=monitor, falsifier_params=falsifier_params,
                         server_options=server_options, server_class=server_class,
                         num_workers=num_workers, scenic_path=scenic_path)

    def init_server(self, server_options, server_class):
        if self.verbosity >= 1:
            print("Initializing server")
        sampling_data = DotMap()
        if self.sampler_type is None:
            self.sampler_type = 'random'
        sampling_data.sampler_type = self.sampler_type
        sampling_data.sample_space = self.sample_space
        sampling_data.sampler_params = self.sampler_params

        self.server = server_class(self.num_workers, self.n_iters, sampling_data, self.scenic_path,
        self.monitor, options=server_options, use_carla=self.use_carla, max_time=self.max_time,
        scenario_params=self.scenario_params)

    def run_falsifier(self):
        i = 0
        ce_num = 0
        outputs = self.server.run_server()
        samples, rhos = zip(*outputs)
        if isinstance(self.monitor, multi_objective_monitor):
            counterexamples = self.server.sampler.scenario.externalSampler.sampler.domainSampler.split_sampler.samplers[0].counterexample_values
        else:
            counterexamples = [r <= self.fal_thres for r in rhos]
        for i, (sample, ce, rho) in enumerate(zip(samples, counterexamples, rhos)):
            if self.verbosity >= 1:
                print("Sample no: ", i, "\nSample: ", sample, "\nRho: ", rho)
            self.samples[i] = sample
            # if isinstance(rho, (list, tuple)):
            #     check_var = rho[-1]
            # else:
            #     check_var = rho
            if ce:
                if self.save_error_table:
                    self.populate_error_table(sample, rho)
                ce_num = ce_num + 1
                if ce_num >= self.ce_num_max:
                    break
            elif self.save_safe_table:
                self.populate_error_table(sample, rho, error=False)
        # while True:
        # ray.get(self.server.terminate.remote())