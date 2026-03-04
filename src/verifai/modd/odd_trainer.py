from abc import ABC
from verifai.modd.odd_monitor import GenericMonitor, TorchMonitor
from sklearn import tree
from matplotlib import pyplot as plt
import pickle
import os
import torch


class Trainer(ABC):
    def __init__(self, trainer_params):
        self.trainer_params = trainer_params
        self.monitor = None
        self.training_results = None

    def train(self, training_data):
        pass
    

class GenericTrainer(Trainer):
    def __init__(self, trainer_params):
        super().__init__(trainer_params)
        self.monitor = GenericMonitor(trainer_params.model)


    def train(self, training_data):
        self.monitor.train(training_set=training_data)
        self.training_results = {"score": self.monitor.score(training_data)}
        print(self.training_results)
        self.save(self.monitor)
        return self.monitor, self.training_results
    
    def save(self, monitor):
        os.makedirs(os.path.dirname(self.trainer_params.save_model_path), exist_ok=True)
        with open(self.trainer_params.save_model_path, "wb") as f:
            pickle.dump(monitor.model, f)

    def save_torch(self, monitor):
        torch.save(monitor.model.state_dict(), self.trainer_params.save_model_path)