# Multi-Objective Falsification with Rulebooks

In this example, we show how to use VerifAI for multi-objective falsification with both *Static* and *Dynamic Rulebook* specifications. A [Static Rulebook](https://arxiv.org/abs/1902.09355) $B_S = (R_S, \preceq_{R_S})$ consists of a set of objectives $R_S$ and a preorder $\preceq_{R_S}$ over $R_S$ that encodes their priority relations. A [Dynamic Rulebook](https://link.springer.com/chapter/10.1007/978-3-031-74234-7_3) $B_D = (R_D, \preceq_{R_D}, \delta_D)$ extends this structure with a transition function $\delta_D$ that updates objectives and priorities over time. A Static Rulebook can be represented as a directed acyclic graph, where each node corresponds to an objective and each directed edge represents a priority relation between two objectives. For a Dynamic Rulebook, the graph structure can change over time based on the transition function $\delta_D$.

## Installation

First, follow the instructions in the [VerifAI documentation](https://verifai.readthedocs.io/en/latest/installation.html) to create a virtual environment and install VerifAI:

```bash
python3 -m venv venv_verifai
source venv_verifai/bin/activate

git clone https://github.com/BerkeleyLearnVerify/VerifAI
cd VerifAI
python -m pip install --upgrade pip
python -m pip install -e .
```

Then, for this example, we adopt the [Metadrive simulator](https://metadriverse.github.io/metadrive/) as the backend simulator. To install Metadrive, run the following command:

```bash
python -m pip install "metadrive-simulator @ git+https://github.com/metadriverse/metadrive.git@main"
python -m pip install "sumolib >= 1.21.0"
```

As there exists a dependency conflict on the `progressbar` package between VerifAI and Metadrive, we need to uninstall the `progressbar` package and reinstall the `progressbar2` package:

```bash
python -m pip uninstall progressbar
python -m pip install --force-reinstall progressbar2==3.55.0
```

## Running the Examples

We provide six different scenarios in the `examples/dynamic_rulebook` folder, and you can run any of them by modifying and executing the `run_multi_dynamic.sh` script.

```bash linenums="1"
#!/bin/bash
iteration=100
scenario='multi_inter_left'
use_dynamic_rulebook=true # true / false (false is for a monolithic rulebook)
sampler_idx=0
sampler_type=demab # demab / dmab / dce / random / halton
exploration_ratio=2.0
simulator=scenic.simulators.metadrive.model
simulation_steps=180
log_file="result_${scenario}_${sampler_type}_${sampler_idx}_${use_dynamic_rulebook}.log"
result_file="result_${scenario}_${sampler_type}_${sampler_idx}_${use_dynamic_rulebook}.txt"
csv_file="result_${scenario}_${sampler_type}_${sampler_idx}_${use_dynamic_rulebook}"

rm $scenario/outputs/$log_file
rm $scenario/outputs/$result_file
rm $scenario/outputs/$csv_file.*csv
rm $scenario/outputs/$csv_file\_scatter.png
if [ "$use_dynamic_rulebook" = true ]; then

    for seed in $(seq 0 1);
    do
        python multi.py -n $iteration --headless -e $csv_file.$seed -sp $scenario/$scenario.scenic -gp $scenario/ -rp $scenario/$scenario\_spec.py -sfp $scenario/$scenario\_segment.py -s $sampler_type --seed $seed --using-sampler $sampler_idx -m $simulator --max-simulation-steps $simulation_steps -co $scenario/outputs --exploration-ratio $exploration_ratio >> $scenario/outputs/$log_file
    done

    python $scenario/util/$scenario\_collect_result.py $scenario/outputs/$log_file multi $sampler_idx >> $scenario/outputs/$result_file
    python $scenario/util/$scenario\_analyze_diversity.py $scenario/outputs/ $csv_file multi >> $scenario/outputs/$result_file

else

    for seed in $(seq 0 0);
    do
        python multi.py -n $iteration --headless -e $csv_file.$seed -sp $scenario/$scenario.scenic --single-graph -gp $scenario/$scenario.sgraph -rp $scenario/$scenario\_spec.py -sfp $scenario/$scenario\_segment.py -s $sampler_type --seed $seed --using-sampler 0 -m $simulator --max-simulation-steps $simulation_steps -co $scenario/outputs --exploration-ratio $exploration_ratio >> $scenario/outputs/$log_file
    done

    python $scenario/util/$scenario\_collect_result.py $scenario/outputs/$log_file single 0 >> $scenario/outputs/$result_file
    python $scenario/util/$scenario\_analyze_diversity.py $scenario/outputs/ $csv_file single >> $scenario/outputs/$result_file
fi
```

You can modify the parameters in the script (first 12 lines) to run different scenarios with different configurations. The detailed descriptions of the parameters are as follows:
- `iteration`: The number of iterations for the falsification process, i.e., the number of samples to be generated.
- `scenario`: The name of the scenario to be tested. We provide six different scenarios in the `examples/dynamic_rulebook` folder, and you can change this parameter to run any of them.
- `use_dynamic_rulebook`: A boolean parameter that determines whether to use the dynamic rulebook or the static rulebook. If set to `true`, the dynamic rulebook will be used; otherwise, the static rulebook will be used.
- `sampler_idx`: The index of the sampler to be used. This parameter is used when `use_dynamic_rulebook` is set to `true`. For dynamic rulebooks, we create a dedicated sampler for each scenario segment. The `sampler_idx` parameter specifies which sampler to use for the falsification process. For example, if `sampler_idx` is set to `0`, the first sampler will be used; if it is set to `1`, the second sampler will be used, and so on. If `sampler_idx` is set to `-1`, each sampler will be used in a round-robin manner.
- `sampler_type`: The type of the sampling algorithm to be used. The options include `demab`, `dmab`, `dce`, `random`, and `halton`.
- `exploration_ratio`: The exploration ratio for the sampling algorithm. This parameter controls the balance between exploration and exploitation in the sampling process. A higher value encourages more exploration.
- `simulator`: The simulator to be used for the falsification process. In this example, we use the Metadrive simulator (`scenic.simulators.metadrive.model`).
- `simulation_steps`: The maximum number of simulation steps for each sample. This parameter controls how long each simulation will run before it is terminated.
- `log_file`: The name of the log file where the outputs of the falsification process will be stored.
- `result_file`: The name of the result file where the analyzed falsification results will be stored.
- `csv_file`: The prefix of the CSV files where the raw falsification results will be stored.

After modifying the parameters, you can run the script to start the falsification process:
```bash
sh run_multi_dynamic.sh
```

The results (`log_file`, `result_file`, `csv_file`) will be stored in the `outputs` folder of the corresponding scenario. The `result_file` contains the analyzed results of the falsification process. 
First, it shows the average/max error weights[^1] and the counterexample percentage of the generated samples for each scenario segment, which reflects the overall falsification performance.
Second, it shows the number of different combinations of violated rules in each segment. 
Finally, it shows the standard deviation of the sampled parameters of the generated samples, which reflects their diversity.

[^1]: The error weight is a metric that evaluate the degree of violation to a rulebook specification. A higher error weight indicates a more severe violation, i.e., more and higher-priority rules are violated.

## Creating Your Own Scenarios

You can create your own scenarios by following the structure of the existing scenarios in the `examples/dynamic_rulebook` folder. Each scenario should have the following structure:

```
scenario_name/
├── scenario_name.scenic
├── scenario_name_spec.py
├── scenario_name_segment.py
├── scenario_name_*.graph
├── scenario_name.sgraph
├── util/
│   ├── scenario_name_collect_result.py
│   └── scenario_name_analyze_diversity.py
└── outputs/
```

### `scenario_name.scenic`

It describes the scenario using the Scenic programming language. The detailed Scenic syntax can be found in the [Scenic documentation](https://docs.scenic-lang.org/en/latest/index.html). Note that you can use the `record` statement to record the needed variables for the evaluation process and the switching of rulebooks.

### `scenario_name_spec.py`

It defines all the objective functions (rules) in the rulebooks. Each rule is defined as a Python function with following inputs:
- `simulation`: The Scenic simulation results, which contains the trajectories of all the agents and the recorded variables.
- `indices`: The indices of the corresponding scenario segment. The function should only evaluate within the specified segment. The expected type of `indices` is a one-dimensional numpy array, where each element is the index of a simulation step that belongs to the corresponding segment. For example, if `indices` is `[0, 1, 2]`, the function should only evaluate the simulation results at steps 0, 1, and 2.

The function should return a scalar value that represents the degree of violation to the corresponding rule. The returned value is negative if and only if the rule is violated, and a smaller value indicates a more severe violation.

An example of a rule function is as follows: 

```python
def rule0(simulation, indices):
    if indices.size == 0:
        return 1
    positions = np.array(simulation.result.trajectory)
    distances_to_adv = positions[indices, [0], :] - positions[indices, [1], :]
    distances_to_adv = np.linalg.norm(distances_to_adv, axis=1)
    rho = np.min(distances_to_adv, axis=0) - 8
    return rho
```

This function evaluates the minimum distance between the ego vehicle (agent 0) and the adversarial vehicle (agent 1) within the specified segment, and returns the minimum distance minus a safety margin (8 in this case) as the degree of violation.

### `scenario_name_segment.py`

This file should contain a function that defines the scenario segments. The function should take the simulation results as input and return a list of segment indices. Each segment index is a one-dimensional numpy array that contains the indices of the simulation steps that belong to the corresponding segment. For example, if the function returns `[np.array([0, 1, 2]), np.array([3, 4, 5])]`, it means that there are two segments in the scenario, where the first segment consists of steps 0, 1, and 2, and the second segment consists of steps 3, 4, and 5.

An example of a segment function is as follows:

```python
def segment_function(simulation):
    ego_dist_to_intersection = np.array(simulation.result.records["egoDistToIntersection"])
    # Find switching points, i.e., ego has reached the intersection / ego has finished the right turn
    switch_idx_1 = len(simulation.result.trajectory)
    switch_idx_2 = len(simulation.result.trajectory)
    for i in range(len(ego_dist_to_intersection)):
        if ego_dist_to_intersection[i][1] == 0 and switch_idx_1 == len(simulation.result.trajectory):
            switch_idx_1 = i
            break
    if switch_idx_1 < len(simulation.result.trajectory):
        for i in reversed(range(switch_idx_1, len(ego_dist_to_intersection))):
            if ego_dist_to_intersection[i][1] == 0:
                switch_idx_2 = i + 1
                break
    assert switch_idx_1 <= switch_idx_2
    indices_0 = np.arange(0, switch_idx_1)
    indices_1 = np.arange(switch_idx_1, switch_idx_2)
    indices_2 = np.arange(switch_idx_2, len(simulation.result.trajectory))
    
    return [indices_0, indices_1, indices_2]
```

This function defines three segments based on the distance of the ego vehicle to the intersection. The first segment consists of the steps before the ego vehicle reaches the intersection, the second segment consists of the steps when the ego vehicle is at the intersection, and the third segment consists of the steps after the ego vehicle has passed the intersection.

### `scenario_name_*.graph`

These files define the rulebook structure for each scenario segment. Each file corresponds to one segment. The format of the file is as follows:

```
# ID <segment_idx>
# Node list
<node_id> <rule_func>
<node_id> <rule_func>
...
# Edge list
<node_id_1> <node_id_2>
<node_id_3> <node_id_4>
...
```

On the first line, `<segment_idx>` is the index of the corresponding scenario segment. For example, if the first line is `# ID 0`, it means that this file defines the rulebook structure for the first segment.

In the node list, each line defines a node in the rulebook. `<node_id>` is the unique identifier of the node, and `<rule_func>` is the name of the corresponding rule function defined in `scenario_name_spec.py`. For example, if a line is `0 rule0`, it means that there is a node with ID 0 that corresponds to the `rule0` function.

In the edge list, each line defines a directed edge between two nodes in the rulebook. For example, if a line is `0 1`, it means that there is a directed edge from the node with ID 0 to the node with ID 1, which indicates that the rule corresponding to node 0 has higher priority than the rule corresponding to node 1.

An example of a rulebook structure file with 5 rules is as follows:

```
# ID 0
# Node list
0 rule0
3 rule3
4 rule4
6 rule6
7 rule7
# Edge list
0 3
3 4
4 7
7 6
```

### `scenario_name.sgraph`

*If you only want to use a Dynamic Rulebook, you can skip this file.* 
This file defines the monolithic rulebook structure for the entire scenario (i.e., merging all the scenario segments). Its main purpose is for the comparison between Static and Dynamic Rulebooks. It follows the same format as the `scenario_name_*.graph` files.

### `util/scenario_name_collect_result.py`, `util/scenario_name_analyze_diversity.py`

*These files are only for processing and analyzing the falsification results. It's not necessary for running the falsification process.* You can modify the existing `scenario_name_collect_result.py` and `scenario_name_analyze_diversity.py` files to create your own result processing scripts.

### `outputs/`
This folder is for storing the outputs of the falsification process, including the log files, result files, and CSV files.

## VerifAI Internals

In this section, we provide an overview of the key implementations corresponding to multi-objective falsification in VerifAI.

### The `Rulebook` Class

The core data structure for representing rulebooks in VerifAI is the `rulebook` class, which is defined in `src/verifai/rulebook.py`. It handles the parsing of the rulebook structure files (`scenario_name_*.graph`) and rule function files (`scenario_name_spec.py`), as well as the evaluation of the rules. In `rulebook`, each rule is stored as a `rule` object (the definition of the `rule` class can be found in the same file). The priority structure of the rulebook is stored as a directed graph using `DiGraph` in the [`networkx` library](https://networkx.org/en/).

### Samplers

We provide five samplers that support multi-objective falsification with both Static and Dynamic Rulebooks, including `demab`, `dmab`, `dce`, `random`, and `halton`. The implementations of these samplers can be found in the `src/verifai/sampler/` folder.

- `dmab` (`dynamic_rulebook_mab.py`): The Dynamic Rulebook Multi-Armed Bandit sampler. It extends the traditional Multi-Armed Bandit (MAB) algorithm to support dynamic rulebook specifications. The MAB algorithm first divides the input parameter space into several subspaces (arms) and then iteratively selects an arm to sample based on the reward feedback from the previous samples. It keeps a balance between exploration (selecting an arm that has not been sampled much) and exploitation (selecting an arm that has generated many counterexamples) to efficiently find diverse counterexamples. For dynamic rulebook, a dedicated MAB sampler is created for each scenario segment, where the sampler focuses on the reward feedback from the corresponding segment and updates its sampling strategy accordingly. Currently, the `dmab` sampler only supports continuous input parameters.
- `demab` (`dynamic_rulebook_emab.py`): The Dynamic Rulebook Extended Multi-Armed Bandit sampler. It extends the `dmab` sampler with a more sophisticated reward mechanism that considers the degree of violation to the rules, rather than just whether a counterexample is generated or not. This allows it to better guide the sampling process towards more severe violations. Currently, the `demab` sampler only supports continuous input parameters.
- `dce` (`dynamic_rulebook_ce.py`): The Dynamic Rulebook Cross-Entropy sampler. It extends the traditional Cross-Entropy (CE) method to support dynamic rulebook specifications. Currently, the `dce` sampler only supports continuous input parameters.
- `random` (`random.py`): The Random sampler. It samples the input parameters uniformly at random from the parameter space, without considering any feedback from the previous samples.
- `halton` (`halton.py`): The Halton sampler. It uses the Halton sequence to generate low-discrepancy samples from the input parameter space, which can provide better coverage than random sampling.

### `multi.py`

The `multi.py` file is the main entry point for running multi-objective falsification with both Static and Dynamic Rulebooks. It handles the overall falsification process, including parsing the command-line arguments, setting up the scenario and rulebooks, running the falsification loop, and storing the results.
