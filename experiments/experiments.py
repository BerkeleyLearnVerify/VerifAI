import time
import os
import numpy as np
import math
from dotmap import DotMap
import sys
import traceback
from itertools import product
import argparse

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
        self.num_objectives = 2
        def specification(traj):
            min_dist = np.inf
            N = len(traj)
            for i, val in enumerate(traj):
                print(len(val))
                obj1, obj2 = val[:2]
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
        def specification(simulation):
            positions = np.array(simulation.result.trajectory)
            # simulation.objects[0].carlaObject
            # print(positions)
            distances = positions[:, [0], :] - positions[:, 1:, :]
            distances = np.linalg.norm(distances, axis=2)
            if distances.shape[1] == 1:
                return np.min(distances) - 5
            else:
                return np.min(distances, axis=0) - 5
        
        super().__init__(specification)

def announce(message):
    lines = message.split('\n')
    size = max([len(p) for p in lines]) + 4
    def pad(line):
        ret = '* ' + line
        ret += ' ' * (size - len(ret) - 1) + '*'
        return ret
    lines = list(map(pad, lines))
    m = '\n'.join(lines)
    border = '*' * size
    print(border)
    print(m)
    print(border)

def run_experiments(path, parallel=False, multi_objective=False, use_newtonian=False,
                   sampler_type=None, headless=False, num_workers=5, output_dir='outputs'):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    paths = []
    if os.path.isdir(path):
        for root, _, files in os.walk(path):
            for name in files:
                fname = os.path.join(root, name)
                if os.path.splitext(fname)[1] == '.scenic':
                    paths.append(fname)
    else:
        paths = [path]
    for p in paths:
        try:
            falsifier = run_experiment(p, parallel=parallel, multi_objective=multi_objective,
            use_newtonian=use_newtonian, sampler_type=sampler_type, headless=headless,
            num_workers=num_workers)
        except:
            announce(f'ERROR FOR SCRIPT {p}:\n\n{traceback.format_exc()}')
            continue
        df = pd.concat([falsifier.error_table.table, falsifier.safe_table.table])
        root, _ = os.path.splitext(p)
        outfile = root.split('/')[-1]
        if parallel:
            outfile += '_parallel'
        if multi_objective:
            outfile += '_multi'
        if use_newtonian:
            outfile += '_newton'
        if sampler_type:
            outfile += f'_{sampler_type}'
        outfile += '.csv'
        outpath = os.path.join(output_dir, outfile)
        announce(f'SAVING OUTPUT TO {outpath}')
        df.to_csv(outpath)

def run_experiment(path, parallel=False, multi_objective=False, use_newtonian=False,
                   sampler_type=None, headless=False, num_workers=5):
    announce(f'RUNNING SCENIC SCRIPT {path}')
    model = 'scenic.simulators.newtonian.model' if use_newtonian else None
    params = {'verifaiSamplerType': sampler_type} if sampler_type else {}
    params['render'] = not headless
    if use_newtonian:
        params['model'] = model
    sampler = ScenicSampler.fromScenario(path, **params)
    falsifier_params = DotMap(
        n_iters=None,
        save_error_table=True,
        save_safe_table=True,
        max_time=1800,
    )
    server_options = DotMap(maxSteps=300, verbosity=0)
    monitor = distance_and_steering() if multi_objective else distance()

    falsifier_cls = generic_parallel_falsifier if parallel else generic_falsifier
    
    falsifier = falsifier_cls(sampler=sampler, falsifier_params=falsifier_params,
                                  server_class=ScenicServer,
                                  server_options=server_options,
                                  monitor=monitor, scenic_path=path, scenario_params=params)
    t0 = time.time()
    print('Running falsifier')
    falsifier.run_falsifier()
    t = time.time() - t0
    print()
    print(f'Generated {len(falsifier.samples)} samples in {t} seconds with {falsifier.num_workers} workers')
    print(f'Number of counterexamples: {len(falsifier.error_table.table)}')
    if not parallel:
        print(f'Sampling time: {falsifier.total_sample_time}')
        print(f'Simulation time: {falsifier.total_simulate_time}')
    print(f'Confidence interval: {falsifier.get_confidence_interval()}')
    return falsifier

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', '-p', type=str, default='uberCrashNewton.scenic',
    help='Path to Scenic script')
    parser.add_argument('--parallel', action='store_true')
    parser.add_argument('--num-workers', type=int, default=5, help='Number of parallel workers')
    parser.add_argument('--sampler-type', '-s', type=str, default=None,
    help='verifaiSamplerType to use')
    parser.add_argument('--multi-objective', action='store_true')
    parser.add_argument('--newtonian', '-n', action='store_true')
    parser.add_argument('--headless', action='store_true')
    args = parser.parse_args()
    run_experiments(args.path, args.parallel, args.multi_objective,
    use_newtonian=args.newtonian, sampler_type=args.sampler_type, headless=args.headless,
    num_workers=args.num_workers)
