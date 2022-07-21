#################################
Running Falsification in Parallel
#################################

VerifAI now supports running falsification in parallel, with worker processes simultaneously running dynamic simulations of samples. This API uses the package `RAY <https://ray.io/>`_ from UC Berkeley's RiSE lab, which provides encapsulation for process-level parallelism in Python.

To enable parallel falsification, use the option ``-E parallel`` when running ``poetry install``; if you installed VerifAI using ``pip``, then just run ``pip install ray``.

Setting up the Falsifier
========================

This is as simple as changing any line instantiating a ``generic_falsifier`` to ``generic_parallel_falsifier``. An additional parameter accepted by the ``generic_parallel_falsifier`` class is ``num_workers`` which determines the number of parallel worker processes that run simulations. By default there are 5 parallel workers.

For an example of using parallelized falsification, see the :file:`examples/multi_objective` folder.
