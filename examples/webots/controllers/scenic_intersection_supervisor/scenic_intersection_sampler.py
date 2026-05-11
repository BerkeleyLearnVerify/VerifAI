from dotmap import DotMap

from verifai import Falsifier, ScenicSampler


path_to_scenic_file = 'intersection_crash.scenic'
sampler = ScenicSampler.fromScenario(path_to_scenic_file)

MAX_ITERS = 20
PORT = 8888
MAXREQS = 5
BUFSIZE = 4096

falsifier_params = DotMap()
falsifier_params.n_iters = MAX_ITERS
falsifier_params.save_error_table = False
falsifier_params.save_safe_table = False

server_options = DotMap(port=PORT, bufsize=BUFSIZE, maxreqs=MAXREQS)

falsifier = Falsifier(sampler=sampler,
                      falsifier_params=falsifier_params,
                      server_options=server_options)

falsifier.run_falsifier()

print("Scenic Samples")
for i in falsifier.samples.keys():
    print("Sample: ", i)
    print(falsifier.samples[i])


# To save all samples: uncomment this
# pickle.dump(falsifier.samples, open("generated_samples.pickle", "wb"))
