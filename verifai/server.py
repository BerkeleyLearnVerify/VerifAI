from abc import ABC, abstractmethod
import socket
import dill
from dotmap import DotMap

from verifai.features.features import *
from verifai.samplers.feature_sampler import *
import functools

def default_sampler_params(sampler_type, param_name=None):
    if sampler_type == 'random':
        return
    if sampler_type == 'halton':
        sampler_params = DotMap()
        sampler_params.sample_index = 0
        sampler_params.bases_skipped = 0
        return sampler_params if param_name is None else sampler_params[param_name]
    if sampler_type == 'ce':
        sampler_params = DotMap()
        sampler_params.alpha = 0.9
        sampler_params.thres = 0.2
        sampler_params.cont.buckets = np.array([5])
        sampler_params.cont.dist = None
        sampler_params.disc.dist = None
        if param_name is None:
            return sampler_params
        else:
            if type(param_name) is list:
                return sampler_params[param_name[0]][param_name[1]]
            else:
                return sampler_params[param_name]
    if sampler_type == 'bo':
        sampler_params = DotMap()
        sampler_params.init_num = 5
        return sampler_params if param_name is None else sampler_params[param_name]



def choose_sampler(sample_space, sampler_type, sampler_params=None, sampler_func=None):
    if sampler_type == 'random':
        return 'random', FeatureSampler.samplerFor(sample_space)

    if sampler_type == 'halton':
        if sampler_params is None:
            sampler_params = default_sampler_params('halton')
        else:
            if 'sample_index' not in sampler_params:
                sampler_params.sample_index = default_sampler_params('halton', 'sample_index')
            if 'bases_skipped' not in sampler_params:
                sampler_params.bases_skipped = default_sampler_params('halton', 'bases_skipped')

        return 'halton', FeatureSampler.haltonSamplerFor(sample_space,
                                                         halton_params=sampler_params)
    if sampler_type == 'ce':
        assert sampler_func is not None
        if sampler_params is None:
            sampler_params = default_sampler_params('ce')
        else:
            if 'alpha' not in sampler_params:
                sampler_params.alpha = default_sampler_params('ce', 'alpha')
            if 'thres' not in sampler_params:
                sampler_params.thres = default_sampler_params('ce', 'thres')
            if 'cont' not in sampler_params or 'buckets' not in sampler_params.cont:
                sampler_params.cont.buckets = default_sampler_params('ce', ['cont', 'buckets'])
            if 'cont' not in sampler_params or 'dist' not in sampler_params.cont:
                sampler_params.cont.dist = default_sampler_params('ce', ['cont', 'dist'])
            if 'disc' not in sampler_params:
                sampler_params.disc.dist = default_sampler_params('ce', ['disc', 'dist'])
        sampler_params.f = sampler_func
        return 'ce', FeatureSampler.crossEntropySamplerFor(sample_space,
                                                        ce_params=sampler_params)

    if sampler_type == 'bo':
        assert sampler_func is not None
        if sampler_params is None:
            sampler_params = default_sampler_params('bo')
        else:
            if 'init_num' not in sampler_params:
                sampler_params.init_num = default_sampler_params('bo', 'init_num')
        sampler_params.f = sampler_func
        return 'bo', FeatureSampler.bayesianOptimizationSamplerFor(sample_space,
                                                                    BO_params=sampler_params)


class Server(ABC):

    def __init__(self, sampling_data):

        self.port = sampling_data.port
        self.bufsize = sampling_data.bufsize
        self.maxreqs = sampling_data.maxreqs
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = socket._LOCALHOST
        self.socket.bind((self.host, self.port))
        self.socket.listen(sampling_data.maxreqs)


        if sampling_data.sampler is not None:
            self.sampler_type = 'random' \
                if sampling_data.sampler_type is None else sampling_data.sampler_type
            self.sampler = sampling_data.sampler
            self.sample_space = self.sampler.space \
                if sampling_data.sample_space is None else sampling_data.sample_space

        elif sampling_data.sampler_type is None:
            feature_space = {}
            for space_name in sampling_data.sample_space:
                space = sampling_data.sample_space[space_name]
                feature_space[space_name] = Feature(space)
            self.sample_space = FeatureSpace(feature_space)
            self.sampler_type = 'random'
            self.sampler = FeatureSampler.samplerFor(self.sample_space)
            self.sample_space = self.sampler.space
        else:
            feature_space = {}
            for space_name in sampling_data.sample_space:
                space = sampling_data.sample_space[space_name]
                feature_space[space_name] = Feature(space)
            self.sample_space = FeatureSpace(feature_space)
            self.sampler_type, self.sampler = choose_sampler(sample_space = self.sample_space,
                                                             sampler_type=sampling_data.sampler_type,
                                                             sampler_params=None if 'sampler_params' not in
                                                             sampling_data else sampling_data.sampler_params,
                                                             sampler_func=sampling_data.sampler_func
                                                             if 'sampler_func' in sampling_data else None)

        print("Initialized sampler")



    def listen(self):
        client_socket, addr = self.socket.accept()
        self.client_socket = client_socket

    def receive(self):
        data = []
        while True:
            msg = self.client_socket.recv(self.bufsize)
            if not msg:
                break
            data.append(msg)
        simulation_data = dill.loads(b"".join(data))
        return simulation_data

    def send(self, sample):
        msg = dill.dumps(sample)
        self.client_socket.send(msg)

    def close_connection(self):
        self.client_socket.close()

    def get_sample(self):
        return self.sampler.nextSample()

    def flatten_sample(self, sample):
        return self.sampler.space.flatten(sample)


    @abstractmethod
    def run_server(self):
        print("Implement in child class")
        pass

class SamplingServer(Server):
    def __init__(self, sampling_data, monitor):
        super().__init__(sampling_data)
        self.monitor = monitor

    def run_server(self):
        sample = self.get_sample()
        self.listen()
        self.send(sample)
        simulation_data = self.receive()
        self.close_connection()
        if self.monitor is None:
            return sample, 0
        return sample, self.monitor.evaluate(simulation_data)



class ActiveServer(Server):
    def __init__(self, sampling_data, monitor, sampler_func=None):
        self.monitor = monitor
        if sampler_func is None:
            self.sampler_func = self.build_active_sampling_func(self.monitor)
        else:
            self.sampler_func = sampler_func
        sampling_data.sampler_func = self.sampler_func
        super().__init__(sampling_data)

    def build_active_sampling_func(self, monitor):
        @functools.lru_cache(maxsize=1)
        def sampling_func(sample):
            self.listen()
            self.send(sample)
            simulation_data = self.receive()
            self.close_connection()
            return monitor.evaluate(simulation_data)
        return sampling_func

    def run_server(self):
        sample = self.get_sample()
        return sample, self.sampler_func(sample)


