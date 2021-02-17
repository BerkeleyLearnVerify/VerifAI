#!/usr/bin/env python
# coding: utf-8

import time
import numpy as np
import math
from dotmap import DotMap
import sys

from verifai.samplers.scenic_sampler import ScenicSampler
from verifai.scenic_server import ScenicServer
from verifai.falsifier import generic_falsifier, generic_parallel_falsifier
from verifai.monitor import multi_objective_monitor, specification_monitor
from verifai.falsifier import generic_falsifier
import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt


class distance_and_steering(multi_objective_monitor):
    def __init__(self):
        priority_graph = None
        def specification(traj):
            min_dist = np.inf
            N = len(traj)
            for i, val in enumerate(traj):
                obj1, obj2 = val
                min_dist = min(min_dist, obj1.distanceTo(obj2))
            angles = np.zeros((N - 1,))
            for i in range(1, N):
                t1, t2 = traj[i - 1], traj[i]
                ego_pos1, _ = t1
                ego_pos2, _ = t2
                v_ego = (ego_pos2 - ego_pos1) * 10
                angle = math.atan2(v_ego.y, v_ego.x)
                angles[i - 1] = angle
            rho = (min_dist - 5, (10 * math.pi / 180) - np.ptp(angles))
            return rho
        
        super().__init__(specification, priority_graph)

class distance(specification_monitor):
    def __init__(self):
        def specification(traj):
            min_dist = np.inf
            N = len(traj)
            for i, val in enumerate(traj):
                obj1, obj2 = val
                min_dist = min(min_dist, obj1.distanceTo(obj2))
            rho = min_dist - 5
            return rho
        
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
    monitor = distance()
    
    falsifier = generic_falsifier(sampler=sampler, falsifier_params=falsifier_params,
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