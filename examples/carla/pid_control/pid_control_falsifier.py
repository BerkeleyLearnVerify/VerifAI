from verifai.features.features import *
from verifai.falsifier import mtl_falsifier
from dotmap import DotMap

init_conditions = Struct({
    'target_speed': Box([25.0, 35.0]),
    'mass': Box([500.0, 3000.0]),
    'max_rpm': Box([5000.0, 8000.0]),
    'center_of_mass': Box([-.3,.3], [-.05,.05], [-.3,.3]),
    'drag_coefficient': Box([0.1, 0.5]),
    'tire_friction': Box([0.8,1.0])
})

sample_space = {'init_conditions': init_conditions}

SAMPLERTYPE = 'ce'
MAX_ITERS = 20
PORT = 8888
MAXREQS = 5
BUFSIZE = 4096

specification = ['(G(~(collision | laneinvade)) & F[0,50](G(~dspeed)))']

falsifier_params = DotMap()
falsifier_params.n_iters = MAX_ITERS
falsifier_params.compute_error_table = True
falsifier_params.fal_thres = 0.0

server_options = DotMap(port=PORT, bufsize=BUFSIZE, maxreqs=MAXREQS)

sampler_params = DotMap()
sampler_params.init_num = 2
falsifier_params.sampler_params = sampler_params

falsifier = mtl_falsifier(sample_space=sample_space, sampler_type=SAMPLERTYPE,
                          specification=specification, falsifier_params=falsifier_params,
                          server_options=server_options)
falsifier.run_falsifier()

analysis_params = DotMap()
analysis_params.k_closest_params.k = 4
analysis_params.random_params.count = 4
falsifier.analyze_error_table(analysis_params=analysis_params)

print("Falsified Samples")
print(falsifier.error_table.table)

print("Safe Samples")
print(falsifier.safe_table.table)
