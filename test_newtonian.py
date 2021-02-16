#!/usr/bin/env python
# coding: utf-8

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


class confidence_spec(specification_monitor):
    def __init__(self):
        def specification(traj):
            min_dist = np.inf
            for i, val in enumerate(traj):
                obj1, obj2 = val
                min_dist = min(min_dist, obj1.distanceTo(obj2))
            # print(min_dist)
            return min_dist - 5
        
        super().__init__(specification)

def test_driving_dynamic():

    path = 'uberCrashNewton.scenic'
    sampler = ScenicSampler.fromScenario(path)
    falsifier_params = DotMap(
        n_iters=1000,
        save_error_table=True,
        save_safe_table=True,
    )
    server_options = DotMap(maxSteps=100, verbosity=0)
    monitor = confidence_spec()
    
    falsifier = generic_parallel_falsifier(sampler=sampler, falsifier_params=falsifier_params,
                                  server_class=ScenicServer,
                                  server_options=server_options,
                                  monitor=monitor, scenic_path=path)
    t0 = time.time()
    falsifier.run_falsifier()
    t = time.time() - t0
    print(f'Generated {len(falsifier.samples)} samples in {t} seconds with 1 worker')
    print(f'Number of counterexamples: {len(falsifier.error_table.table)}')
    return falsifier

if __name__ == '__main__':
    falsifier = test_driving_dynamic()