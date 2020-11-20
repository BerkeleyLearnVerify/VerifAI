import time
import numpy as np
from dotmap import DotMap

from verifai.samplers.scenic_sampler import ScenicSampler
from verifai.scenic_server import ScenicServer
from verifai.falsifier import generic_falsifier, generic_parallel_falsifier
from verifai.monitor import specification_monitor
from verifai.falsifier import mtl_falsifier

def specification(traj):
    min_dist = np.inf
    for timestep in traj:
        obj1, obj2 = timestep
        dist = obj1.distanceTo(obj2)
        min_dist = min(min_dist, dist)
    print(f'min_dist = {min_dist}')
    return min_dist

def main():

    path = 'uberCrash.scenic'
    sampler = ScenicSampler.fromScenario(path)
    falsifier_params = DotMap(
        n_iters=10,
        save_error_table=True,
        save_safe_table=True,
    )
    falsifier_params.fal_thres = 5.2
    server_options = DotMap(maxSteps=200, verbosity=0)
    falsifier = generic_falsifier(sampler=sampler,
                                  falsifier_params=falsifier_params,
                                  server_class=ScenicServer,
                                  server_options=server_options,
                                  monitor=specification_monitor(specification))
    t0 = time.time()
    falsifier.run_falsifier()
    t = time.time() - t0
    print(f'Generated {len(falsifier.samples)} samples in {t} seconds with 1 worker')
    print(f'Number of counterexamples: {len(falsifier.error_table.table)}')

if __name__ == '__main__':
    main()