###########
Search Techniques
###########

VerifAI provides several techniques for exploring the semantic search space for verification, testing, and synthesis.
These are largely based on sampling and optimization methods. In the tool, we refer to all of these as "samplers".

There are three active samplers (i.e. cross entropy, simulated annealing, and bayesian optimization samplers) and two passive samplers (i.e. random and halton samplers) supported. The details of their implementation can be found in verifai/samplers directory. 


How to add a new sampler?
=========================
First, add your python script of your sampler in verifai/samplers directory along with other sampler scripts. 
Second, add an API to call your sampler in verifai/samplers/feature_sampler.py
