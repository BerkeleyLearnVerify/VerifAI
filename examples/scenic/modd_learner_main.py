
import math
import os.path
import sys
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from verifai.odd_sampler import ODDSampler
from verifai.monitor import specification_monitor, mtl_specification
from verifai.oddlearner import MODDLearner
from dotmap import DotMap

from verifai.samplers import ScenicSampler
from verifai.scenic_server import ScenicServer


def preprocessing(traces):
    res = []
    for i in range(len(traces.keys())):
        t = traces[i]
        dist = t[0]["dist"][0][1]
        spec = int(t[1] > 0)
        res.append([dist, spec])
    return np.array(res)

def labeler(train_data_samples):
        
    
        return train_data_samples

# Set up the parameters for the data generation. 
datagen_params = DotMap(
    preprocessing=preprocessing,
    labeler=labeler,
    simulations_save_dir="",
    datagen_save_dir="",
    verbosity=2,
)

base_model = DecisionTreeClassifier(max_depth=10)

learner_params = DotMap(
    model=base_model,
    training_results_path="",
    save_model_path="./out/model.pkl",
    verbosity=2,
)

    
def specification(trace):
        verdict = 0
    
        return verdict

eval_params = DotMap(
    method="conformance_testing",
    specification=specification,
    eval_num_simulations=5, # To indicate how many samples are required as a minimum
    eval_num_steps=50, 
    evaluation_results_path="", # Save the evaluation_results if not empty
    verbosity=2,
)


class SpecMonitor(specification_monitor):
    def __init__(self):
        self.specification = mtl_specification(['G safe'])
        super().__init__(self.specification)

    def evaluate(self, simulation):
        # Get trajectories of objects from the result of the simulation
        traj = simulation.result.trajectory

        # Compute time-stamped sequence of values for 'safe' atomic proposition;
        # we'll define safe = "distance from ego to all other objects > 5"
        safe_values = []
        for positions in traj:
            ego = positions[0]
            dist = min((ego.distanceTo(other) for other in positions[1:]),
                       default=math.inf)
            safe_values.append(dist - 5)
        eval_dictionary = {'safe' : list(enumerate(safe_values)) }

        # Evaluate MTL formula given values for its atomic propositions
        return self.specification.evaluate(eval_dictionary)

# Load the Scenic scenario and create a sampler from it
path = os.path.join(os.path.dirname(__file__), 'newtonian/carlaChallenge2.scenic')
sampler = ScenicSampler.fromScenario(path, mode2D=True, params={"monitor": ""})
sampler_eval = ScenicSampler.fromScenario(path, mode2D=True, params={"monitor": learner_params.save_model_path})

server_options = DotMap(maxSteps=100, verbosity=2)

sampling_params = DotMap(
    sampler=sampler,
    sampler_eval=sampler_eval,
    spec_monitor=SpecMonitor(), 
    server_type="scenic",
    server_class=ScenicServer,
    server_options=server_options,
    verbosity=2,
)

sampler = ODDSampler(sampling_params=sampling_params)
sampling_params = sampler.sampling_params

global_params = DotMap(
    initial_num_simulations=15,
    initial_num_steps=50, 
    refinement_num_simulations=5, 
    refinement_num_steps=50, 
    refinement_iters=0, 
)

if not os.path.isdir("./out/"):
    os.mkdir("./out/")
    
modd = MODDLearner(datagen_params=datagen_params,
            learner_params=learner_params,
            eval_params=eval_params,
            sampling_params=sampling_params,
            global_params=global_params)

# Train ODD monitor and print the results
oddMonitor = modd.run()
print('ODD monitor trained:')
print(oddMonitor)
print('Training results:')
print(modd.training_results)
print('Evaluation results:')
print(modd.evaluation_results)


# trace = np.random.rand(100, 14)
# label = np.random.randint(100)
# traces = [(trace, label)]
