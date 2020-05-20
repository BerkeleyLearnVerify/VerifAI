from verifai.simulators.carla.client_carla import *
from verifai.simulators.carla.carla_world import *
from verifai.simulators.carla.carla_task import *
from verifai.simulators.carla.carla_scenic_task import *

import numpy as np
from dotmap import DotMap
import carla

# Falsifier (not CARLA) params
PORT = 8888
BUFSIZE = 4096

simulation_data = DotMap()
simulation_data.port = PORT
simulation_data.bufsize = BUFSIZE
# Note: The world_map param below should correspond to the MapPath 
# specified in the scenic file. E.g., if world_map is 'Town01',
# the MapPath in the scenic file should be the path to Town01.xodr.
simulation_data.task = scenic_sampler_task(world_map='Town01')

client_task = ClientCarla(simulation_data)
while client_task.run_client():
    pass
print('End of all simulations.')
