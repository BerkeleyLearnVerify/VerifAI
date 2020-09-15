from abc import ABC
from verifai.server import Server
from verifai.samplers import TerminationException
from dotmap import DotMap
from verifai.monitor import mtl_specification, specification_monitor
from verifai.error_table import error_table
import numpy as np

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
            sampler_params=None, verbosity=2,
        )
        if falsifier_params is not None:
            params.update(falsifier_params)
        if params.sampler_params is None:
            params.sampler_params = DotMap(thres=params.fal_thres)
        self.save_error_table = params.save_error_table
        self.save_safe_table = params.save_safe_table
        self.error_table_path = params.error_table_path
        self.safe_table_path = params.safe_table_path
        self.n_iters, self.ce_num_max = params.n_iters, params.ce_num_max
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

    def run_falsifier(self):
        i = 0
        ce_num = 0
        while True:
            if i == self.n_iters:
                break
            try:
                sample, rho = self.server.run_server()
            except TerminationException:
                if self.verbosity >= 1:
                    print("Sampler has generated all possible samples")
                break
            if self.verbosity >= 1:
                print("Sample no: ", i, "\nSample: ", sample, "\nRho: ", rho)
            self.samples[i] = sample
            if isinstance(rho, (list, tuple)):
                check_var = rho[-1]
            else:
                check_var = rho
            if check_var <= self.fal_thres:
                if self.save_error_table:
                    self.populate_error_table(sample, rho)
                ce_num = ce_num + 1
                if ce_num >= self.ce_num_max:
                    break
            elif self.save_safe_table:
                self.populate_error_table(sample, rho, error=False)
            i += 1
        self.server.terminate()


class generic_falsifier(falsifier):
    def __init__(self,  monitor=None, sampler_type= None, sample_space=None, sampler=None,
                 falsifier_params=None, server_options={}, server_class=Server):
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
