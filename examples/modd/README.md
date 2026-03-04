# MODD

The MODD class receives a set of labeled traces and outputs a ODD Monitor.

The MODD implements the boxes on the right side of the following diagram:

![alt text](MODD_diagram.png)


## VerifAI Interface 

Given a specification $\varphi$, VerifAI uses the sampler, analyzer and simulator to generate a set of traces $\{\sigma_i, \ell_i\}_i$.

The MODD receives the set of evaluated simulation traces  $\{\sigma_i\}_i$, where each point $\sigma_i$ is defined by a features vector and a special feature namely the correctness of the specification, and generates a training dataset $\{\tau_i, \ell_i\}_i$, where $\tau_i$ is a vector and $\ell_i$ is a single value (Data Generation box in the diagram).

The MODD uses then the training dataset $\{\tau_i, \ell_i'\}_i$ to train a monitor $M$ (Learner box).

The MODD evaluates the monitor $M$ over some new simulations (Evaluation box). If the optimality objective is not met, the MODD will trigger the generation of new simulations to expand the training dataset and restart the training process.  

### Run instructions
- Create environment with python=3.9.
- Clone the repository and install VerifAI as usual:
        `python -m pip install -e .`
- Change directory to examples/modd/
- Run the example: `python ./modd_learner_follow.py`.




### Implementation details

The MODD receives the following inputs:
- datagen_params: Parameters required to generate the training dataset:
    - preprocessing function 
    - labeling function
    - saving directory
- trainer_params: Parameters required to train the ODD Monitor:
    - model to be trained (sklearn, pytorch, etc.)
    - training results saving directory
    - trained model saving path
- eval_params: Parameters required to evaluate the ODD Monitor:
    - evaluation method
    - specification
    - number of simulations to run
    - number of steps per simulation
    - evaluation results saving directory
    - evaluation results of running the monitor on simulations
    - evaluation results of running the system without the monitor on the same simulations
    - scenes saving path
- sampling_params: Parameters required to specify how to make calls to a sampler to generate more data:
    - sampler 
    - server_class
    - server_options
    - path to controller to be monitored
- global_params: Parameters to specify how many simulations to run per loop of the MODD generation process:
    - initial number of simulations
    - initial number of simulation steps
    - number of simulations per refinement loop
    - number of steps per refinement simulation
    - iterations of the refinement loop

    


