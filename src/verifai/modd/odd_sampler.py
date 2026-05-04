from dotmap import DotMap

from verifai.samplers import ScenicSampler

class ODDSampler():
    def __init__(self, sampling_params):
        self.sampling_params = sampling_params

        try:
            server_params = DotMap()
            server_params.update(self.sampling_params.server_options)
            self.init_server(server_params, self.sampling_params.server_class)
            self.sampling_params.server = self.server
        except Exception:
            print("ODDSampler initialization failed. Is the server a Scenic server?")


    def init_server(self, server_options, server_class):
        if self.sampling_params.verbosity >= 1:
            print("Initializing server")
        sampling_data = DotMap()
        if not self.sampling_params.has_key("sampler_type"):
            self.sampler_type = 'random'
        sampling_data.sampler_type = self.sampler_type
        sampling_data.sample_space = None
        sampling_data.sampler_params = None
        if self.sampling_params.mode == "train":
            sampling_data.sampler = ScenicSampler.fromScenario(self.sampling_params.path, mode2D=server_options.mode2D, maxSteps=server_options.maxSteps, params=server_options.train_params)
            
        elif self.sampling_params.mode == "eval":
            sampling_data.sampler = ScenicSampler.fromScenario(self.sampling_params.path, mode2D=server_options.mode2D, maxSteps=server_options.maxSteps, params=server_options.eval_params)
            
        elif self.sampling_params.mode == "eval_nomonitor":
            sampling_data.sampler = ScenicSampler.fromScenario(self.sampling_params.path, mode2D=server_options.mode2D, maxSteps=server_options.maxSteps, params=server_options.eval_nomonitor_params)
        else:
            raise Exception("Sampling mode not correct. Options are ['train', 'eval', 'eval_nomonitor']")
        self.server = server_class(sampling_data, monitor=self.sampling_params.spec_monitor, options=server_options)
        if self.sampling_params.verbosity >= 1:
            print("Server ready")
