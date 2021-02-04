#!/usr/bin/env python
# coding: utf-8

# In[9]:

import time
import numpy as np
from dotmap import DotMap

from verifai.samplers.scenic_sampler import ScenicSampler
from verifai.scenic_server import ScenicServer
from verifai.falsifier import generic_falsifier, generic_parallel_falsifier
from verifai.monitor import multi_objective_monitor, specification_monitor
from verifai.falsifier import generic_falsifier
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt


# In[10]:


# The specification must assume multi_objective_monitor class
class confidence_spec(specification_monitor):
    def __init__(self):
        def specification(traj):
            min_dist = np.inf
            for i, val in enumerate(traj):
                obj1, obj2 = val
                min_dist = min(min_dist, obj1.distanceTo(obj2))
            for i, val in enumerate(traj[1:]):
                obj1, _ = val
                obj1_prev, _ = traj[i - 1]
                heading = obj1_prev - obj1
                print(f'heading = {heading}')
            # print(min_dist)
            return min_dist - 5
        
        super().__init__(specification)


# In[11]:


def test_driving_dynamic():

    path = 'scenic_driving.scenic'
    sampler = ScenicSampler.fromScenario(path)
    falsifier_params = DotMap(
        n_iters=100,
        save_error_table=True,
        save_safe_table=True,
    )
    server_options = DotMap(maxSteps=2, verbosity=0)
    monitor = confidence_spec()
    
    falsifier = generic_falsifier(sampler=sampler,
                                  falsifier_params=falsifier_params,
                                  server_class=ScenicServer,
                                  server_options=server_options,
                                  monitor=monitor)
    t0 = time.time()
    falsifier.run_falsifier()
    t = time.time() - t0
    print(f'Generated {len(falsifier.samples)} samples in {t} seconds with 1 worker')
    print(f'Number of counterexamples: {len(falsifier.error_table.table)}')
    return falsifier


# In[12]:


falsifier = test_driving_dynamic()
