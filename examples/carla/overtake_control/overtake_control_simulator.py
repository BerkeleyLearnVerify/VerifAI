from verifai.simulators.carla.client_carla import *
from verifai.simulators.carla.carla_world import *
from verifai.simulators.carla.carla_task import *

import numpy as np
from dotmap import DotMap
import carla

from verifai.simulators.carla.agents.pid_agent import *
from verifai.simulators.carla.agents.overtake_agent import *

# Falsifier (not CARLA) params
PORT = 8888
BUFSIZE = 4096


def norm(vec):
    return np.sqrt(vec.x ** 2 + vec.y ** 2 + vec.z ** 2)


class overtake_control_task(carla_task):
    def __init__(self,
                 n_sim_steps=500,
                 display_dim=(1280,720),
                 carla_host='127.0.0.1',
                 carla_port=2000,
                 carla_timeout=4.0,
                 world_map='Town03'):
        super().__init__(
            n_sim_steps=n_sim_steps,
            display_dim=display_dim,
            carla_host=carla_host,
            carla_port=carla_port,
            carla_timeout=carla_timeout,
            world_map=world_map
        )


    def use_sample(self, sample):
        print('Sample:', sample)

        init_conds = sample.init_conditions
        self.ego_target_speed = init_conds.ego_target_speed[0]
        self.other_target_speed = init_conds.other_target_speed[0]

        # PID controller parameters
        pid_opt_dict = {
            'target_speed': self.ego_target_speed,
        }

        follow_opt_dict = {
            'target_speed': self.other_target_speed,
            'clear_dist': init_conds.clear_dist[0]
        }

        # Deterministic blueprint, spawnpoint.
        other_blueprint = self.world.world.get_blueprint_library().find('vehicle.ford.mustang')
        other_spawn = self.world.map.get_spawn_points()[1]
        other_location = other_spawn.location
        other_heading = other_spawn.get_forward_vector()

        ego_blueprint = self.world.world.get_blueprint_library().find('vehicle.audi.tt')
        ego_location = other_location + init_conds.initial_dist[0] * other_heading
        ego_spawn = carla.Transform(ego_location, other_spawn.rotation)
        self.ego_vehicle = self.world.add_vehicle(PIDAgent,
                                                  control_params=pid_opt_dict,
                                                  blueprint=ego_blueprint,
                                                  spawn=ego_spawn,
                                                  has_collision_sensor=True,
                                                  has_lane_sensor=False,
                                                  ego=True)

        self.other_vehicle = self.world.add_vehicle(OvertakeAgent,
                                                    control_params=follow_opt_dict,
                                                    blueprint=other_blueprint,
                                                    spawn=other_spawn,
                                                    has_collision_sensor=True,
                                                    has_lane_sensor=False,
                                                    ego=False)


    def trajectory_definition(self):
        # Get speed of collision as proportion of target speed.
        ego_collision = [(c[0], c[1] / self.ego_target_speed)
                         for c in self.ego_vehicle.collision_sensor.get_collision_speeds()]
        other_collision = [(c[0], c[1] / self.other_target_speed)
                           for c in self.other_vehicle.collision_sensor.get_collision_speeds()]

        # MTL doesn't like empty lists.
        if not ego_collision:
            ego_collision = [(0,0)]
        if not other_collision:
            other_collision = [(0,0)]

        traj = {
            'egocollision': ego_collision,
            'othercollision': other_collision
        }
        return traj

simulation_data = DotMap()
simulation_data.port = PORT
simulation_data.bufsize = BUFSIZE
simulation_data.task = overtake_control_task()

client_task = ClientCarla(simulation_data)
while client_task.run_client():
    pass
print('End of all simulations.')
