from verifai.falsifier import mtl_falsifier
from verifai.features.features import *
from dotmap import DotMap

control_params = Struct({
        'ROBOT1pos': Box([-0.7, 0.1], [-0.5, 0.3]),
        'ROBOT2pos': Box([-0.1, 0.7], [ 0.1, 0.9]),
        'ROBOT3pos': Box([-0.4, 0.4], [-0.4, 0.4])
    })

sample_space = {'control_params':control_params}

SAMPLERTYPE = 'ce'
MAX_ITERS = 10
PORT = 8888
MAXREQS = 5
BUFSIZE = 4096

specification = ["G(collision)"]

falsifier_params = DotMap()
falsifier_params.n_iters = MAX_ITERS
falsifier_params.compute_error_table = True

server_options = DotMap(port=PORT, bufsize=BUFSIZE, maxreqs=MAXREQS)

falsifier = mtl_falsifier(sample_space=sample_space, sampler_type=SAMPLERTYPE,
                          specification=specification, falsifier_params=falsifier_params,
                          server_options=server_options)
falsifier.run_falsifier()

print("Unsafe samples: Error table")
print(falsifier.error_table.table)

# To save all samples: uncomment this
# pickle.dump(falsifier.samples, open("generated_samples.pickle", "wb"))
