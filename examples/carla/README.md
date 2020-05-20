# Installation and Compatibility
In order to run this interface:
* Install Verifai and Scenic according to the instructions in their respective top-level README files.
* Install <a href="https://github.com/carla-simulator/carla/releases/tag/0.9.8"> CARLA 0.9.8</a>. Please note that at minimum, a NVIDIA GeForce 470 GTX or AMD Radeon 6870 HD series GPU is required.
* To install the CARLA Python API, run `easy_install PythonAPI/carla/dist/carla-0.9.8-py3.5-linux-x86_64.egg` from the CARLA simulator's install directory. This might output the following error message:
    ```c
    error: Could not find suitable distribution for Requirement.parse('carla==0.9.8')
    ```
    which can be ignored. The CARLA Python API has been correctly installed if the line
    ```
    import carla
    ```
    executes without errors in Python.

# Directory structure
Classes for interfacing Verifai/CARLA in general are in `verifai/simulators/carla`. Individual examples are found in `carla/`, with agents used for these examples in `carla/agents`.

# Examples

The following examples demonstrate various use-cases for interfacing Verifai and CARLA.
* The lane-keeping example monitors the speed, collisions, and lane invasions of the ego vehicle over time.
* The overtaking example does the same, with multiple vehicles.
* The Scenic sampler example samples scenes from Scenic code.

## Lane-keeping
**Task:** Falsify a PID lane-keeping controller.

**Sample space:** Target speed and physical parameters (mass, center of mass, maximum engine RPM, drag coefficient, tire friction** of vehicle.

**Relevant files:**
1. `carla/agents/pid_agent.py`: PID lane-keeping agent.
2. `carla/pid_control/pid_control_falsifier.py`: Defines sample space and falsifier.
3. `carla/pid_control/pid_control_simulator.py`: Interfaces with the CARLA simulator.

**Running the falsifier:** 
Start the CARLA simulator server with `./CarlaUE4.sh`. Then run `python carla/pid_control/pid_control_falsifier.py`. Once the sampler is initialized, run `python carla/pid_control/pid_control_simulator.py`.

## Overtaking
**Task:** Falsify the same PID lane-keeping controller, where the environment now contains a second vehicle (also PID) which approaches the ego from behind on the same lane and attempts to overtake.

**Sample space:** Target speed of both vehicles, initial distance between vehicles, and the distance at which the second vehicle will begin overtaking maneuvers.

**Relevant files:**
1. `carla/agents/pid_agent.py`: PID lane-keeping agent.
2. `carla/overtake_control/overtake_control_falsifier.py`: Defines sample space and falsifier.
3. `carla/overtake_control/overtake_control_simulator.py`: Interfaces with the CARLA simulator.

**Running the falsifier:** 
Start the CARLA simulator server with `./CarlaUE4.sh`. Then run `python carla/overtake_control/overtake_control_falsifier.py`. Once the sampler is initialized, run `python carla/overtake_control/overtake_control_simulator.py**.

## Scene Generation using Scenic
**Task:** Generate scenes using Scenic

**Sample Space:** Position of vehicles, pedestrians, and props.

**Relevant files:**
1. `carla/scenic/adjacentOpposingPair.sc`: Example Scenic code to generate scenes.
2. `carla/scenic/scenic_sampler.py`: Interface to Scenic.
3. `carla/scenic/scenic_simulator.py`: Interface to CARLA.
4. `carla/scenic/Town01.xodr`: OpenDRIVE file corresponding to CARLA map.

**Running the sampler:**
Start the CARLA simulator server with `./CarlaUE4.sh`. Then run `python carla/scenic_sampler.py`. Once the sampler is initialized (the message `Initialized sampler` will be output), run `python carla/scenic/scenic_simulator.py`. The Scenic file to be used is specified by the `path_to_scenic_file` variable in `carla/scenic/scenic_sampler.py`. 

Also, make sure that the MapPath specified in the scenic file corresponds to the `.xodr` file for the same map specified in the `world_map` parameter for the `scenic_sampler_task` object in `scenic_simulator.py`. Note that if the CARLA simulator was launched with a different map than specified here, the sampler may crash. Running the above two python files a second time (without restarting the CARLA simulator) will fix this.
