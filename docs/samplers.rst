###########
Samplers
###########

There are three active samplers (i.e. cross entropy, simulated annealing, and bayesian optimization samplers) and two passive samplers (i.e. random and halton samplers) supported in VerifAI toolkit. The details of their implementation can be found in verfai/samplers directory. 


How to add a new sampler?
=========================
First, add your python script of your sampler in verfai/samplers directory along with other sampler scripts. 
Second, add an API to call your sampler in verfai/samplers/feature_sampler.py