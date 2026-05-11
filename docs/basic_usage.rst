################
Basic Usage 
################

.. testsetup::

	import os
	os.chdir('..')

The core functionality of VerifAI allows you to:

	1. Define a feature space of parameters to search over;
	2. Sample from that space using a variety of techniques;
	3. Use those samples to configure and run simulations of a system of interest;
	4. Monitor whether the system satisfied its specification;
	5. Gather simulation results in a table for analysis.

This process is orchestrated by the top-level `Falsifier` class, which performs
*falsification*: automatic search for points in the space where the system violates its
specification.

Defining a Sample Space and Choosing a Sampler
===============================================
There are two ways of defining a feature space.

Method 1: Using :ref:`Feature APIs <Feature APIs>`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can use VerifAI's feature APIs to define domains for each feature. Primitive domains
such as boxes and finite sets can be combined into structures and arrays.

.. testcode::

	from verifai import *

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

	sample_space = FeatureSpace({
		'control_params': Feature(control_params),
		'env_params': Feature(env_params),
		'cones_config': Feature(cones_config)
	})

Once the feature space is defined, you can create a sampler which samples from the space
using one of VerifAI's many :doc:`search techniques <samplers>`. These range from passive
methods like Halton sampling which simply try to cover the space evenly, to active methods
like cross-entropy sampling and Bayesian optimization which try to drive the system under
test towards specification violations.

.. testcode::

	random_sampler                = FeatureSampler.randomSamplerFor(sample_space)
	halton_sampler                = FeatureSampler.haltonSamplerFor(sample_space)
	cross_entropy_sampler         = FeatureSampler.crossEntropySamplerFor(sample_space)
	simulated_annealing_sampler   = FeatureSampler.simulatedAnnealingSamplerFor(sample_space)


Method 2: Using Scenic
^^^^^^^^^^^^^^^^^^^^^^

Feature spaces consisting of configurations of physical objects can be defined using the
`Scenic scenario description language <https://scenic-lang.org/>`_ You can instantiate
VerifAI's `ScenicSampler` directly from a Scenic file:

.. testcode::

	from verifai import ScenicSampler

	path = 'examples/webots/controllers/scenic_cones_supervisor/lane_cones.scenic'
	scenic_sampler = ScenicSampler.fromScenario(path)

Scenic's sampler, by default, does random sampling (see :obj:`~verifai.samplers.ScenicSampler` for the available configuration options).
However, it is possible to invoke VerifAI's other samplers from within the scenario using Scenic's :term:`external parameters`.


Constructing a Monitor 
======================

To evaluate the output of a simulation and identify cases where the system being tested
violated its specification, you can define a `Monitor`. VerifAI will call the monitor
after each simulation to compute a value (or, for multi-objective falsification, a vector)
representing to what extent the specification was satisfied. The value can be a simple
Boolean, or it can be a number representing how close the system came to violating the
specification, with negative numbers meaning there was actually a violation. VerifAI will
save these values in a table, and active samplers will also use them to intelligently
drive the system towards violations.

There are several ways to construct a `Monitor`, described below.

Method 1: Objective Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These functions will be called with the result of the simulation and should
return a number (or Boolean), which VerifAI will try to minimize. The simulation
result is represented as a :obj:`~scenic.core.simulators.Simulation` object when
using Scenic; when instead using the legacy simulator interface, the representation
is up to the `Client` but is typically a dict of time-series features.

.. testcode::

	from verifai import Monitor

	def specification(result):
		# Evaluate the specification given the result of a simulation
		return result['yTrue'] == result['yPred']

	monitor = Monitor.fromFunctions(specification)


Method 2: Metric Temporal Logic Formulas
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can write a specification as a formula of Metric Temporal Logic (MTL) using
the syntax provided by `this package <https://github.com/mvcisback/py-metric-temporal-logic>`_.

.. testcode::

	monitor = Monitor.fromMTL("G(collisioncone0 & collisioncone1 & collisioncone2)")

The example above asserts that the 3 atomic propositions ``collisioncone0`` etc. must be
true at every time step. The names of propositions used in the formula should match the
names of time series defined in the Scenic scenario using the `record` statement (or, when
using the legacy `Client`, the names of time series it returns).


Method 3: Custom Monitors
~~~~~~~~~~~~~~~~~~~~~~~~~

For advanced use cases, you can write your own subclass of `Monitor`. This is typically
not necessary unless you are also defining your own custom sampling technique and need
information beyond the simple numerical value computed by the types of monitors above.


Setting up a Simulator
====================================================================

By default, VerifAI communicates with external simulators through Scenic (see the `simulators` section of the Scenic documentation for details on supported simulators and how to interface to new simulators).
Which simulator to use and how to configure it is typically specified in the Scenic program: for example, a Scenic program which selects the CARLA world model using a statement like ``model scenic.simulators.carla.model`` will automatically use the CARLA simulator.
The documentation of each simulator interface describes the configuration options it supports.
Generic options such as the number of time steps to simulate can be passed directly to VerifAI when creating a falsifier, as we will see below.

.. testcode::

	from dotmap import DotMap
	server_options = DotMap(maxSteps=100, verbosity=0)

.. note::

	VerifAI's original system for direct communication with simulators based on
	a client/server architecture and network sockets is still largely supported,
	but not recommended for new simulator interfaces. See the `Server` class for
	details.


Instantiating a Falsifier
====================================================================

Combining the pieces above, we can instantiate a `Falsifier` and run it to
perform falsification (search for cases which violate our specification).
Here is a complete example running 2 simulations:

.. testcode::

	sampler = ScenicSampler.fromScenicCode("""\
	model scenic.simulators.newtonian.model
	ego = Object with velocity (0, Range(5, 15))
	other = Object at (5, 0), with velocity (-10, 10)
	terminate after 2 seconds
	record final (distance to other) as dist
	""")

	def specification(simulation):
		return simulation.result.records['dist'] > 1

	falsifier = Falsifier(
		sampler=sampler,
		monitor=specification,
		falsifier_params=DotMap(n_iters=2),
	)
	falsifier.run_falsifier()

The `Falsifier` class provides many parameters to control falsification and
data output. Some of the most commonly-needed parameters are shown below:

.. testcode::

	falsifier_params = DotMap(
		n_iters=1000,   # Number of simulations to run (or None for no limit)
		max_time=None,	# Time limit in seconds, if any
		save_error_table=True,   # Record samples that violated the specification
		save_safe_table=False,  # Don't record samples that satisfied the specification
		fal_thres=0.0,    # Monitor return value below which a sample is considered a violation (0 is the default)
		sampler_params=None   # optional DotMap of sampler-specific parameters
	)
