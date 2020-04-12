############################################
Getting Started with VerifAI
############################################

To install VerifAI as a python package from PyPi, execute

.. code:: python
	
	pip install verifai

or as a developer:

.. code:: python
	
	pip install --pre verifai

You need to ensure that your your pip version is >= 18.1

Some features of VerifAI require additional packages (the tool will prompt you if they are needed but not installed):

Note that the package for GPy on PyPI currently does not work with Python 3.7. If necessary, you can build it from source as follows:

.. code:: python

	git clone https://github.com/SheffieldML/GPy
	find Gpy -name '*.pyx' -exec cython {} \
	pip install Gpy/