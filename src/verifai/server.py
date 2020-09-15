import socket
import dill
from dotmap import DotMap

from verifai.features.features import *
from verifai.samplers.feature_sampler import *
import functools

def default_sampler_params(sampler_type):
    if sampler_type == 'random':
        return
    if sampler_type == 'halton':
        return DotMap(sample_index =0, bases_skipped=0)
    if sampler_type == 'ce':
        cont = DotMap(buckets=5, dist=None)
        disc = DotMap(dist=None)
        return DotMap(alpha=0.9, thres=0.0, cont=cont, disc=disc)
    if sampler_type == 'bo':
        return DotMap(init_num=5)

def choose_sampler(sample_space, sampler_type,
                   sampler_params=None):
    if sampler_type == 'random':
        return 'random', FeatureSampler.randomSamplerFor(sample_space)

    if sampler_type == 'halton':
        if sampler_params is None:
            halton_params = default_sampler_params('halton')
        else:
            halton_params = default_sampler_params('halton')
            halton_params.update(sampler_params)

        sampler = FeatureSampler.haltonSamplerFor(sample_space,
                                                  halton_params=halton_params)
        return 'halton', sampler
    if sampler_type == 'ce':
        if sampler_params is None:
            ce_params = default_sampler_params('ce')
        else:
            ce_params = default_sampler_params('ce')
            if 'cont' in sampler_params:
                if 'buckets' in sampler_params.cont:
                    ce_params.cont.buckets = sampler_params.cont.buckets
                if 'dist' in sampler_params.cont:
                    ce_params.cont.dist = sampler_params.cont.dist
            if 'dist' in sampler_params.disc:
                ce_params.disc.dist = sampler_params.disc.dist
            if 'alpha' in sampler_params:
                ce_params.alpha = sampler_params.alpha
            if 'thres' in sampler_params:
                ce_params.thres = sampler_params.thres
        sampler = FeatureSampler.crossEntropySamplerFor(
            sample_space, ce_params=ce_params)
        return 'ce', sampler

    if sampler_type == 'bo':
        if sampler_params is None:
            bo_params = default_sampler_params('bo')
        else:
            bo_params = default_sampler_params('bo')
            bo_params.update(sampler_params)
        sampler = FeatureSampler.bayesianOptimizationSamplerFor(
            sample_space, BO_params=bo_params)
        return 'bo', sampler

class Server:
    def __init__(self, sampling_data, monitor, options={}):
        defaults = DotMap(port=8888, bufsize=4096, maxreqs=5)
        defaults.update(options)
        self.monitor = monitor
        self.lastValue = None
        self.port = defaults.port
        self.bufsize = defaults.bufsize
        self.maxreqs = defaults.maxreqs
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = '127.0.0.1'
        self.socket.bind((self.host, self.port))
        self.socket.listen(self.maxreqs)

        if sampling_data.sampler is not None:
            self.sampler_type = ('random' if sampling_data.sampler_type is None
                                 else sampling_data.sampler_type)
            self.sampler = sampling_data.sampler
            self.sample_space = (self.sampler.space
                                 if sampling_data.sample_space is None
                                 else sampling_data.sample_space)

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
            params = (None if 'sampler_params' not in sampling_data
                      else sampling_data.sampler_params)
            self.sampler_type, self.sampler = choose_sampler(
                sample_space=self.sample_space,
                sampler_type=sampling_data.sampler_type,
                sampler_params=params
            )

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
        simulation_data = self.decode(b"".join(data))
        return simulation_data

    def send(self, sample):
        msg = self.encode(sample)
        self.client_socket.send(msg)
        self.client_socket.shutdown(socket.SHUT_WR)

    def encode(self, sample):
        return dill.dumps(sample)

    def decode(self, data):
        return dill.loads(data)

    def terminate(self):
        self.socket.close()
        
    def close_connection(self):
        self.client_socket.close()

    def get_sample(self, feedback):
        return self.sampler.nextSample(feedback)

    def flatten_sample(self, sample):
        return self.sampler.space.flatten(sample)

    def evaluate_sample(self, sample):
        self.listen()
        self.send(sample)
        simulation_data = self.receive()
        self.close_connection()
        value = (0 if self.monitor is None
                 else self.monitor.evaluate(simulation_data))
        return value

    def run_server(self):
        sample = self.get_sample(self.lastValue)
        self.lastValue = self.evaluate_sample(sample)
        return sample, self.lastValue
