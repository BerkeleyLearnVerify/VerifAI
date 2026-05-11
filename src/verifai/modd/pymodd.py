from dotmap import DotMap

from verifai.modd.odd_evaluator import GenericEvaluator
from verifai.modd.odd_data_generator import GenericDataGenerator
from verifai.modd.odd_trainer import GenericTrainer
from verifai.modd.odd_monitor import Monitor

class MODD():
    def __init__(self, 
                    datagen_params=DotMap(), 
                    trainer_params=DotMap(), 
                    eval_params=DotMap(), 
                    sampling_params=DotMap(),
                    global_params=DotMap(),
                    data_generator=None,
                    trainer=None,
                    evaluator=None):
        self.datagen_params = datagen_params
        self.trainer_params = trainer_params
        self.eval_params = eval_params
        self.sampling_params = sampling_params
        self.global_params = global_params

        self.data_generator=data_generator
        self.trainer=trainer
        self.evaluator=evaluator
        
        if self.data_generator is None:
            self.data_generator = GenericDataGenerator(datagen_params=datagen_params, sampling_params=sampling_params, global_params=global_params)
        if self.trainer is None:
            self.trainer = GenericTrainer(trainer_params=trainer_params)
        if self.evaluator is None:
            self.evaluator = GenericEvaluator(eval_params=eval_params, sampling_params=sampling_params, global_params=global_params)

   

    def generate_monitor(self):
        refinement_iters = 0
        if self.global_params.has_key("refinement_iters"):
            refinement_iters = self.global_params.refinement_iters
          
        
        training_data = self.data_generator.generate(self.global_params.initial_num_simulations, self.global_params.initial_num_steps) # type: ignore
        print("-- Finished training")
        self.monitor, self.training_results = self.trainer.train(training_data)
        print("-- Finished learning")
        self.evaluation_results = self.evaluator.evaluate(self.monitor) 
        print("-- Finished evaluation")

        while refinement_iters > 0 and not self.evaluator.terminate: 
            # The parameters sampling_params of the data_generator, learner, and evaluator 
            # can be modified here to change the simulations generated during the refinement iterations.

            training_data = self.data_generator.generate(self.global_params.refinement_num_simulations, self.global_params.refinement_num_steps) # type: ignore
            self.monitor, self.training_results  = self.learner.learn(training_data)
            self.evaluation_results = self.evaluator.evaluate(self.monitor) 
            
            refinement_iters -= 1

        return self.monitor, self.training_results, self.evaluation_results
