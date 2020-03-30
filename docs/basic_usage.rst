###########
Basic Usage
###########

***********************
How to Execute VerifAI
***********************
.. code:: python

	from verifai.falsifier import generic_falsifier

	# Setup the falsifier using sampler of your choice
	falsifier = generic_falsifier(monitor, sampler_type, sample_space, sampler, 
					falsifier_params, server_options)

	# Execute the falsifier
	falsifier.run_falsifier()

************************
Setting up the Falsifier
************************

Defining a Sample Space and Choosing a Sampler
===============================================
There are two ways of defining a feature space.

Method 1: Using VerifAI's Feature APIs [CREATE LINK]
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Currently, there are five different samplers [CREATE A LINK HERE] supported in VerifAI. 

.. code:: python

	from verifai.features.features import *
	from verifai.samplers.feature_sampler import *
	from verifai.falsifier import generic_falsifier

	control_params = Struct({
        'x_init': Box([-0.05, 0.05]),
        'cruising_speed': Box([10.0, 20.0]),
        'reaction_time': Box([0.7, 1.00])
    })

	env_params = Struct({
	        'broken_car_color': Box([0.5, 1], [0.25, 0.75], [0, 0.5]),
	        'broken_car_rotation': Box([5.70, 6.28])
	    })

	cones_config = Struct({
	        'traffic_cones_pos_noise': Box([-0.25, 0.25], [-0.25, 0.25], [-0.25, 0.25]),
	        'traffic_cones_down_0': Categorical(*np.arange(5)),
	        'traffic_cones_down_1': Categorical(*np.arange(5)),
	        'traffic_cones_down_2': Categorical(*np.arange(5))
	    })

	sample_space = {'control_params':control_params, 'env_params':env_params,
	                'cones_config':cones_config}

	# Five Supported Samplers
	random_sampler                = FeatureSampler.randomSamplerFor(sample_space)
	halton_sampler                = FeatureSampler.haltonSamplerFor(sample_space)
	cross_entropy_sampler         = FeatureSampler.crossEntropySamplerFor(sample_space)
	simulated_annealing_sampler   = FeatureSampler.simulatedAnnealingSamplerFor(sample_space)
	bayesian_optimization_sampler = FeatureSampler.bayesianOptimizationSamplerFor(sample_space)

	falsifier = generic_falsifier(sampler = sampler_of_your_choice, ...)


Method 2: Using Scenic
^^^^^^^^^^^^^^^^^^^^^^
QUESTION: HOW TO HAVE VERIFAI CHOOSE ANOTHER SAMPLER WHEN USING SCENIC??????????????

.. code:: python

	from verifai.samplers.scenic_sampler import ScenicSampler
	from verifai.falsifier import generic_falsifier

	path_to_scenic_script = 'lane_cones.sc'
	sampler = ScenicSampler.fromScenario(path_to_scenic_script)

	falsifier = generic_falsifier(sampler = sampler, sampler_type = 'scenic', ...)


Constructing a Monitor 
====================================================================
Active samplers sample for the next point in the feature space by accounting for the history of
the performance of a system being tested in previous simulations. To use active samplers,
a user need to provide a monitor (i.e. objective function).
For passive samplers, monitor is optional, but it can be used to populate the error table with 
the how a system of interest performed in each simulation.

.. code:: python

	from verifai.monitor import specification_monitor
	from verifai.falsifier import generic_falsifier

	# The specification must assume specification_monitor class
	class confidence_spec(specification_monitor):
	    def __init__(self):
	        def specification(traj):
	            return traj['yTrue'] == traj['yPred']
	        super().__init__(specification)

	falsifier = generic_falsifier(monitor = confidence_spec(), ...)


Writing a Formal Specification with Metric Temporal Logic
====================================================================
Instead of a customized monitor, users can provide a specification using metric temporal logic [LINK TO ITS SYNTAX/SEMANTICS]. In such case, users need to use mtl_falsifier instead of generic_falsifier.

.. code:: python
	
	from verifai.falsifier import mtl_falsifier

	specification = ["G(collisioncone0 & collisioncone1 & collisioncone2)"]
	falsifier = mtl_falsifier(specification = specification, ...)


Defining Falsifier Parameters
====================================================================

.. code:: 
	
	falsifier_params                   = DotMap()
	falsifier_params.n_iters           = number of simulations to run
	falsifier_params.save_error_table  = boolean value
	falsifier_params.save_good_samples = boolean value
	falsifier_params.fal_thres         = Real-valued threshold of monitor/specification
	falsifier_params.sampler_params    = DotMap dictionary of parameters specific to samplers

	falsifier = generic_falsifier(falsifier_params = falsifier_params, ...)

Setting up Client/Server Communication
====================================================================

.. code:: python

	server_options = DotMap(port, bufsize, maxreqs)
	falsifier = generic_falsifier(server_options = server_options, ...)



