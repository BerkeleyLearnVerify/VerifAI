# Installation and Compatibility
In order to run this interface:
* Install Verifai and Scenic according to the instructions in their respective top-level README files.
* Install <a href=https://carla.readthedocs.io/en/latest/start_quickstart/> CARLA verison greater than or equal to 0.9.8</a>. Please note that at minimum, a NVIDIA GeForce 470 GTX or AMD Radeon 6870 HD series GPU is required.
* To install the CARLA Python API, install the `.egg` file in the PythonAPI repo that you installed. For example, `easy_install PythonAPI/carla/dist/carla-0.9.8-py3.5-linux-x86_64.egg` from the CARLA simulator's install directory. This might output the following error message:
    ```c
    error: Could not find suitable distribution for Requirement.parse('carla==0.9.8')
    ```
    which can be ignored. The CARLA Python API has been correctly installed if the line
    ```
    import carla
    ```
    executes without errors in Python.
* Finally, set the PYTHONPATH to the `.egg` file by running `export PYTHONPATH="PythonAPI/carla/dist/carla-0.9.8-py3.5-linux-x86_64.egg:$PYTHONPATH"`

# Directory structure
Classes for interfacing Verifai with CARLA in general are in `src/verifai/simulators/carla`. Individual examples are found in `carla/`, with agents used for these examples in `carla/agents`.

# Examples
The following examples demonstrate various use-cases for interfacing Verifai and CARLA.
The two [carla challenge scenarios](https://carlachallenge.org/challenge/nhtsa/>) from the Scenic repo is included in this scenic folder.
These are pre-crash scenarios inspired by [National Highway Traffic Safety Administration (NHTSA) pre-crash typology](https://www.nhtsa.gov/sites/nhtsa.gov/files/pre-crash_scenario_typology-final_pdf_version_5-2-07.pdf/>). More `.scenic` examples can be found in the [Scenic repo](https://github.com/BerkeleyLearnVerify/Scenic/tree/master/examples/carla/Carla_Challenge).

# Running the Examples
Instantiate the CARLA simulator server with `./CarlaUE4.sh`. Then run `python scenic_sampler.py` from `examples/carala/scenic` folder. 
The `scenic_sampler.py` is defining the specification and the configuration parameters for running verifai. 
For more details, please refer to [our documentation](https://verifai.readthedocs.io/en/latest/basic_usage.html).

Also, make sure that the `param map = localPath('./Town01.xodr')` specified in the `.scenic` file corresponds to the `.xodr` file path. 