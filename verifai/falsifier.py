from abc import ABC
from verifai.server import Server
from dotmap import DotMap
from verifai.monitor import mtl_specification, specification_monitor
from verifai.error_table import error_table
import numpy as np

class falsifier(ABC):
    def __init__(self, monitor, sampler_type=None, sampler=None, sample_space=None,
                 falsifier_params=None, server_options={}):
        self.sample_space= sample_space
        self.sampler_type = sampler_type
        self.sampler = sampler
        self.samples = {}

        if falsifier_params is None:
            self.save_error_table = True
            self.save_good_samples = True
            self.n_iters = 1000
            self.sampler_params = None
            self.fal_thres = 0.2
        else:
            self.save_error_table = falsifier_params.save_error_table \
                if 'save_error_table' in falsifier_params else True
            self.save_good_samples = falsifier_params.save_good_samples \
                if 'save_good_samples' in falsifier_params else True
            self.n_iters = falsifier_params.n_iters \
                if 'n_iters' in falsifier_params else 1000
            self.sampler_params = falsifier_params.sampler_params \
                if 'sampler_params' in falsifier_params else None

            if 'fal_thres' in falsifier_params:
                self.fal_thres = falsifier_params.fal_thres
            elif self.sampler_params is None or 'thres' not in self.sampler_params:
                self.fal_thres = 0.0
            else:
                self.fal_thres = self.sampler_params.thres

            if self.sampler_params is None:
                sampler_params = DotMap()
                sampler_params.thres = self.fal_thres
                self.sampler_params = sampler_params
            else:
                self.sampler_params.thres = self.fal_thres

        self.monitor = monitor
        self.init_server(server_options)
        self.init_error_table()

    def init_server(self, server_options):
        sampling_data = DotMap()
        if self.sampler_type is None:
            self.sampler_type = 'random'
        sampling_data.sampler_type = self.sampler_type
        sampling_data.sample_space = self.sample_space
        sampling_data.sampler_params = self.sampler_params
        sampling_data.sampler = self.sampler

        self.server = Server(sampling_data, self.monitor, options=server_options)

    def init_error_table(self):
        # Initializing error table
        if self.save_error_table:
            self.error_table = error_table(space = self.server.sample_space)
        if self.save_good_samples:
            self.safe_table = error_table(space = self.server.sample_space)

    def populate_error_table(self, sample, error=True):
        if error:
            self.error_table.update_error_table(sample)
        else:
            self.safe_table.update_error_table(sample)

    def analyze_error_table(self, analysis_params= None, error=None):
        if self.save_error_table and (error is None or error is True):
            self.error_analysis = self.error_table.analyze(analysis_params)

            if 'k_closest' in self.error_analysis:
                self.error_analysis.k_closest_samples = \
                    [self.samples[i] for i in self.error_analysis.k_closest]
            if 'random' in self.error_analysis:
                self.error_analysis.random_samples = \
                    [self.samples[i] for i in self.error_analysis.random]
        if self.save_good_samples and (error is None or error is False):
            self.safe_analysis = self.safe_table.analyze(analysis_params)

            if 'k_closest' in self.safe_analysis:
                self.safe_analysis.k_closest_samples = \
                    [self.samples[i] for i in self.safe_analysis.k_closest]
            if 'random' in self.safe_analysis:
                self.safe_analysis.random_samples = \
                    [self.samples[i] for i in self.safe_analysis.random]

    def run_falsifier(self):
        i = 0
        while True:
            if i == self.n_iters:
                break
            sample, rho = self.server.run_server()
            print("Sample no: ", i, "\nSample: ", sample, "\nRho: ", rho)
            self.samples[i] = sample
            if rho <= self.fal_thres and self.save_error_table:
                self.populate_error_table(sample)
            elif self.save_good_samples:
                self.populate_error_table(sample, error=False)
            i += 1

class generic_falsifier(falsifier):
    def __init__(self,  monitor=None, sampler_type= None, sample_space=None, sampler=None,
                 falsifier_params=None, server_options = {}):
        if monitor is None:
            class monitor(specification_monitor):
                def __init__(self):
                    def specification(traj):
                        return np.inf
                    super().__init__(specification)
            monitor = monitor()

        super().__init__(sample_space=sample_space, sampler_type=sampler_type,
                         monitor=monitor, falsifier_params=falsifier_params, sampler=sampler,
                         server_options=server_options)

class mtl_falsifier(generic_falsifier):
    def __init__(self, specification, sampler_type = None, sample_space=None, sampler=None,
                 falsifier_params=None, server_options = {}):
        monitor = mtl_specification(specification=specification)
        super().__init__(sample_space=sample_space, sampler_type=sampler_type,
                         monitor=monitor, falsifier_params=falsifier_params, sampler=sampler,
                         server_options=server_options)
