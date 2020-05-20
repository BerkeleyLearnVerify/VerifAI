################
Basic Usage 
################

************************
Setting up the Falsifier
************************

Defining a Sample Space and Choosing a Sampler
===============================================
There are two ways of defining a feature space.

Method 1: Using :ref:`Feature APIs`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

	# Examples of Instantiating Some of VerifAI's Supported Samplers
	random_sampler                = FeatureSampler.randomSamplerFor(sample_space)
	halton_sampler                = FeatureSampler.haltonSamplerFor(sample_space)
	cross_entropy_sampler         = FeatureSampler.crossEntropySamplerFor(sample_space)
	simulated_annealing_sampler   = FeatureSampler.simulatedAnnealingSamplerFor(sample_space)
	bayesian_optimization_sampler = FeatureSampler.bayesianOptimizationSamplerFor(sample_space)


Method 2: Using Scenic
^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

	from verifai.samplers.scenic_sampler import ScenicSampler
	from verifai.falsifier import generic_falsifier

	path_to_scenic_script = 'lane_cones.sc'
	scenic_sampler = ScenicSampler.fromScenario(path_to_scenic_script)

Scenic sampler, by default, does random sampling. However, users can refer to this `link <https://scenic-lang.readthedocs.io/en/1.1.0/_autosummary/_autosummary/scenic.core.external_params.html>`_ to configure scenic script with other samplers. 

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


Writing a Formal Specification with Metric Temporal Logic
====================================================================
Instead of a customized monitor, users can provide a specification using `metric temporal logic <https://github.com/mvcisback/py-metric-temporal-logic>`_. In such case, users need to use mtl_falsifier instead of generic_falsifier.

.. code:: python
	
	from verifai.falsifier import mtl_falsifier

	specification = ["G(collisioncone0 & collisioncone1 & collisioncone2)"]


Defining Falsifier Parameters
====================================================================

.. code:: 
	
	falsifier_params                   = DotMap()
	falsifier_params.n_iters           = 1000   # Number of simulations to run
	falsifier_params.save_error_table  = True   # Option to record samples that violated the monitor/specification
	falsifier_params.save_good_samples = False  # Option to record samples that satisfied the monitor/specification
	falsifier_params.fal_thres         = 0.5    # Real-valued threshold of monitor/specification
	falsifier_params.sampler_params    = None   # DotMap dictionary of parameters specific to samplers


Setting up Client/Server Communication
====================================================================

.. code:: python

	PORT = 8888
	BUFSIZE = 4096
	MAXREQS = 5

	server_options = DotMap(port = PORT, bufsize = BUFSIZE, maxreqs = MAXREQS)


Instantiating a Falsifier
====================================================================

.. code:: python

	from verifai.samplers.feature_sampler import *
	from verifai.falsifier import generic_falsifier

	# When using VerifAI Features to define feature space : 
	falsifier = generic_falsifier(sampler = random_sampler, monitor = confidence_spec(), falsifier_params = falsifier_params, server_options = server_options)

	# When using Scenic to define feature space : 
	falsifier = generic_falsifier(sampler = scenic_sampler, sampler_type = 'scenic', monitor = confidence_spec(), falsifier_params = falsifier_params, server_options = server_options)

	# When using an metric temporal logic specification:
	falsifier = mtl_falsifier(sampler = random_sampler, specification = specification, falsifier_params = falsifier_params, server_options = server_options)
	falsifier = mtl_falsifier(sampler = scenic_sampler, sampler_type = 'scenic', specification = specification, falsifier_params = falsifier_params, server_options = server_options)

	# Run the simulations
	# falsifier.run_falsifier()
