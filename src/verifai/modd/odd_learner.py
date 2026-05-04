from abc import ABC

from dotmap import DotMap

from verifai.modd import pymodd

class ODDLearner(ABC):
    def __init__(self, datagen_params=DotMap(), trainer_params=DotMap(), 
                 eval_params=DotMap(), sampling_params=DotMap(), 
                 global_params=DotMap()):
        self.monitor = None 
        self.training_results = None
        self.evaluation_results = None

        self.datagen_params = datagen_params
        self.trainer_params = trainer_params
        self.eval_params = eval_params
        self.sampling_params = sampling_params
        self.global_params = global_params      

    def run(self):
        pass


class MODDLearner(ODDLearner):
    def __init__(self, datagen_params, trainer_params, eval_params, sampling_params, global_params):
        self.modd = pymodd.MODD(datagen_params, 
                    trainer_params,
                    eval_params,
                    sampling_params,
                    global_params,
                    )
        
        super().__init__(datagen_params=datagen_params, 
                         trainer_params=trainer_params, 
                         eval_params=eval_params, 
                         sampling_params=sampling_params, 
                         global_params=global_params)
        
    def run(self):
        self.monitor, self.training_results, self.evaluation_results = self.modd.run()
        return self.monitor


