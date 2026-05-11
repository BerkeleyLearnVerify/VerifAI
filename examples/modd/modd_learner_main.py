import os.path
import sys
sys.path.append("./carla")

from dotmap import DotMap
import numpy as np
import torch.nn as nn
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from modd_torch import MLP
from verifai.monitor import specification_monitor, mtl_specification
from verifai.modd.odd_learner import MODDLearner
from verifai.scenic_server import ScenicServer


VERBOSITY = 1
MODEL = "LR"

#####################################################################
#################### Datagen parameters #############################
#####################################################################

def preprocessing(traces):
    res = []
    for i in range(len(traces.keys())):
        print(f"Simulation {i}")
        t = traces[i]
        # Features
        color = t[0]["colorObstacle"]
        r,g,b = color.r, color.g, color.b
        weather = t[0]["weather_props"]
        distLeaderRecord = t[0]["distLeader"]
        distIntersectionRecord = t[0]["distIntersection"]
        distObstacleRecord = t[0]["distObstacle"]
        visibleObstacleRecord = t[0]["visibleObstacle"]
        visibleLeaderRecord = t[0]["visibleLeader"]
        for step in range(0, len(distLeaderRecord)-100):
            # Output
            distLeaderEnd = distLeaderRecord[step+100][1]
            # Input
            distIntersection = distIntersectionRecord[step][1]
            distObstacle = distObstacleRecord[step][1]
            visibleObstacle = visibleObstacleRecord[step][1]
            visibleLeader = visibleLeaderRecord[step][1]
            features = np.concatenate((weather, np.array([r,g,b, distIntersection, distObstacle, visibleObstacle, visibleLeader, distLeaderEnd])))
            res.append([features])
    return np.squeeze(np.array(res), axis=1)



def labeler(train_data_samples):
    res = train_data_samples.copy()
    res[:,-1] = (train_data_samples[:,-1] < 20).astype(int)

    return res

# Set up the parameters for the data generation. 
datagen_params = DotMap(
    preprocessing=preprocessing,
    labeler=labeler,
    datagen_save_dir=os.path.join(os.path.dirname(__file__), "out/samples_timeseries"),
    verbosity=VERBOSITY,
)


#####################################################################
#################### Trainer parameters #############################
#####################################################################

if MODEL == "DT":
    base_model = DecisionTreeClassifier(max_depth=10)

if MODEL == "NN":
    nn = MLPClassifier(solver='adam', alpha=1e-5,
                    hidden_layer_sizes=(100,100), max_iter=100, random_state=42, verbose=1)
    base_model = Pipeline([('scaler', StandardScaler()), ('nn', nn)])

if MODEL == "LR":   
    base_model = LogisticRegression(verbose=1)

if MODEL == "NN_TORCH":
    base_model = MLP()

trainer_params = DotMap(
    model=base_model,
    training_results_path="",
    save_model_path=os.path.join(os.path.dirname(__file__), "out/lr_timeseries.pkl"),
    verbosity=VERBOSITY,
)


#####################################################################
#################### Eval parameters ################################
#####################################################################
    
def specification(trace):
        verdict = 0
    
        return verdict

eval_params = DotMap(
    method="conformance_testing",
    specification=specification, # Safety specification
    eval_num_simulations=10, # Number of simulations to evaluate the monitor
    eval_num_steps=300, # Timesteps per simulation
    evaluation_results_path="", # Save the evaluation_results if not empty
    datagen_save_dir=os.path.join(os.path.dirname(__file__), "out/eval_samples_timeseries"),
    scenes_save_dir=os.path.join(os.path.dirname(__file__), "out/scene_timeseries"),
    datagen_nomon_save_dir=os.path.join(os.path.dirname(__file__), "out/eval_samples_timeseries_nomonitor"),
    save_model_path=trainer_params.save_model_path,
    verbosity=VERBOSITY,
)




#####################################################################
#################### Sampling parameters ############################
#####################################################################

class SpecMonitor(specification_monitor):
    def __init__(self):
        self.specification = mtl_specification(['G safe'])
        super().__init__(self.specification)

    def evaluate(self, simulation):
        # Get trajectories of objects from the result of the simulation
        records = simulation.result.records
        distLeader = records["distLeader"]

        # Compute time-stamped sequence of values for 'safe' atomic proposition;
        # we'll define safe = "distance from ego to leader < 20"
        safe_values = []
        for (_,dist) in distLeader:
            safe_values.append(20 - dist)
        eval_dictionary = {'safe' : list(enumerate(safe_values)) }

        # Evaluate MTL formula given values for its atomic propositions
        return self.specification.evaluate(eval_dictionary)

# Load the Scenic scenario and create a sampler from it
path = os.path.join(os.path.dirname(__file__), 'carla/followLeader_extracar.scenic')

server_options = DotMap(maxSteps=300, 
                        mode2D=True, 
                        train_params={"monitor": "", 
                                      "seed":"", 
                                      "render" : 0, 
                                      "verbosity": 3, 
                                      "timeBound": 300, 
                                      "controller": os.path.join(os.path.dirname(__file__), 'carla/models/controller_cte_dist_130.pth')},
                        eval_params={"seed": 42, 
                                     "render" : 0, 
                                     "verbosity": 3, 
                                     "timeBound": 300, 
                                     "controller": os.path.join(os.path.dirname(__file__), 'carla/models/controller_cte_dist_130.pth')},
                        eval_nomonitor_params={"monitor": "", 
                                               "seed": 42, 
                                               "render" : 0, 
                                               "verbosity": 3, 
                                               "timeBound": 300, 
                                               "controller": os.path.join(os.path.dirname(__file__), 'carla/models/controller_cte_dist_130.pth')},
                        verbosity=VERBOSITY)

sampling_params = DotMap(
    path=path,
    controller_path= os.path.join(os.path.dirname(__file__), 'carla/models/controller_cte_dist_130.pth'),
    spec_monitor=SpecMonitor(), 
    server_type="scenic",
    server_class=ScenicServer,
    server_options=server_options,
    monitor = eval_params.save_model_path,
    maxSteps = 300,
    mode2D = True,
    verbosity=VERBOSITY,
)


#####################################################################
#################### Global parameters ##############################
#####################################################################

global_params = DotMap(
    initial_num_simulations=10,
    initial_num_steps=300, 
    refinement_num_simulations=1, 
    refinement_num_steps=250, 
    refinement_iters=0, 
)



#####################################################################
############################## MODD #################################
#####################################################################

modd = MODDLearner(datagen_params=datagen_params,
            trainer_params=trainer_params,
            eval_params=eval_params,
            sampling_params=sampling_params,
            global_params=global_params)

# Train ODD monitor and print the results
oddMonitor = modd.generate_monitor()
print('ODD monitor trained:')
print(oddMonitor)
print('Training results:')
print(modd.training_results)
print('Evaluation results:')
print(modd.evaluation_results)



