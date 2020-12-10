import time
import numpy as np
from dotmap import DotMap

from verifai.samplers.scenic_sampler import ScenicSampler
from verifai.scenic_server import ScenicServer
from verifai.falsifier import generic_falsifier, generic_parallel_falsifier
from verifai.monitor import specification_monitor
from verifai.falsifier import generic_falsifier

# The specification must assume specification_monitor class
class distance_monitor(specification_monitor):
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

    path = 'scenic_driving.scenic'
    sampler = ScenicSampler.fromScenario(path)
    falsifier_params = DotMap(
        n_iters=1000,
        save_error_table=True,
        save_safe_table=True,
    )
    server_options = DotMap(maxSteps=2, verbosity=0)
    monitor = distance_monitor()
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

def test_driving_dynamic_parallel(num_workers=5, n_iters=None):

    path = 'scenic_driving.scenic'
    falsifier_params = DotMap(
        n_iters=1000 if n_iters is None else n_iters,
        save_error_table=True,
        save_safe_table=True,
    )
    server_options = DotMap(maxSteps=2, verbosity=0)
    monitor = distance_monitor()
    falsifier = generic_parallel_falsifier(falsifier_params=falsifier_params,
                                  server_class=ScenicServer,
                                  server_options=server_options,
                                  scenic_path=path, num_workers=num_workers,
                                  monitor=monitor)
    t0 = time.time()
    falsifier.run_falsifier()
    t = time.time() - t0
    print(f'Generated {len(falsifier.samples)} samples in {t} seconds with {falsifier.num_workers} workers')
    # msg = 'SAMPLES ARE:'
    # print('*' * (len(msg) + 4))
    # print(f'* {msg} *')
    # print('*' * (len(msg) + 4))
    # for i in falsifier.samples:
    #     print(falsifier.samples[i])
    print(f'Number of counterexamples: {len(falsifier.error_table.table)}')
    return falsifier

if __name__ == '__main__':
    test_driving_dynamic()
    test_driving_dynamic_parallel(num_workers=2)
