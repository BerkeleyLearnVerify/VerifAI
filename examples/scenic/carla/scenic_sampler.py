
from dotmap import DotMap

from verifai.samplers.scenic_sampler import ScenicSampler
from verifai.scenic_server import ScenicServer
from verifai.falsifier import generic_falsifier
import os
from scenic.core.vectors import Vector
import math
from verifai.monitor import specification_monitor, mtl_specification

## Dynamic scenarios
path = os.path.join(os.getcwd(), 'carlaChallenge1.scenic')
sampler = ScenicSampler.fromScenario(path)

class MyMonitor(specification_monitor):
    ''' This class defines the specification (i.e. evaluation metric) '''
    def __init__(self):
        self.specification = mtl_specification(['G safe'])
        super().__init__(self.specification)

    def evaluate(self, simulation):
        traj = simulation.trajectory
        eval_dictionary = {'safe' : [[index, self.compute_dist(traj[index])-5] for index in range(len(traj))]}
        return self.specification.evaluate(eval_dictionary)

    def compute_dist(self, coords):
        vector0 = coords[0]
        vector1 = coords[1]

        x0, y0 = vector0.x, vector0.y
        x1, y1 = vector1.x, vector1.y
        return math.sqrt(math.pow(x0-x1,2) +  math.pow(y0-y1,2))

falsifier_params = DotMap(
    n_iters=5,
    save_error_table=True,
    save_safe_table=True,
    error_table_path='error_table.csv',
    safe_table_path='safe_table.csv'
)
server_options = DotMap(maxSteps=60, verbosity=0)
falsifier = generic_falsifier(sampler=sampler,
                              monitor = MyMonitor(),
                              falsifier_params=falsifier_params,
                              server_class=ScenicServer,
                              server_options=server_options)
falsifier.run_falsifier()
print('end of test')
print("error_table: ", falsifier.error_table.table)
print("safe_table: ", falsifier.safe_table.table)