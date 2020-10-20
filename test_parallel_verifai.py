import time
from dotmap import DotMap

from verifai.samplers.scenic_sampler import ScenicSampler
from verifai.scenic_server import ScenicServer
from verifai.falsifier import generic_falsifier, generic_parallel_falsifier

def test_driving_dynamic():

    path = 'scenic_driving.scenic'
    sampler = ScenicSampler.fromScenario(path)
    falsifier_params = DotMap(
        n_iters=100,
        save_error_table=False,
        save_safe_table=False,
    )
    server_options = DotMap(maxSteps=2, verbosity=0)
    falsifier = generic_falsifier(sampler=sampler,
                                  falsifier_params=falsifier_params,
                                  server_class=ScenicServer,
                                  server_options=server_options)
    t0 = time.time()
    falsifier.run_falsifier()
    t = time.time() - t0
    print(f'Generated {len(falsifier.samples)} samples in {t} seconds with 1 worker')

def test_driving_dynamic_parallel(num_workers=5, n_iters=None):

    path = 'scenic_driving.scenic'
    falsifier_params = DotMap(
        n_iters=100 if n_iters is None else n_iters,
        save_error_table=False,
        save_safe_table=False,
    )
    server_options = DotMap(maxSteps=2, verbosity=0)
    falsifier = generic_parallel_falsifier(falsifier_params=falsifier_params,
                                  server_class=ScenicServer,
                                  server_options=server_options,
                                  scenic_path=path, num_workers=num_workers)
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

if __name__ == '__main__':
    test_driving_dynamic()
    test_driving_dynamic_parallel(num_workers=5)
