from verifai.simulators.carla.client_carla import *
from verifai.simulators.carla.carla_world import *
from verifai.simulators.carla.carla_task import *

import numpy as np
from dotmap import DotMap
import carla

from verifai.simulators.carla.agents.pid_agent import *

# Falsifier (not CARLA) params
PORT = 8888
BUFSIZE = 4096

# Acceptable deviation from target speed in km/h
SPEED_MARGIN = 10.0

def norm(vec):
    return np.sqrt(vec.x ** 2 + vec.y ** 2 + vec.z ** 2)


class pid_control_task(carla_task):
    def __init__(self,
                 speed_margin,
                 n_sim_steps=500,
                 display_dim=(1280,720),
                 carla_host='127.0.0.1',
                 carla_port=2000,
                 carla_timeout=4.0):
        super().__init__(
            n_sim_steps=n_sim_steps,
            display_dim=display_dim,
            carla_host=carla_host,
            carla_port=carla_port,
            carla_timeout=carla_timeout
        )
        self.speed_margin = speed_margin
        self.dspeed = []


    def step_world(self):
        super().step_world()

        # Update dspeed
        speed = 3.6 * norm(self.world.ego.actor.get_velocity())     # 3.6 km/h is 1 m/s
        dspeed = np.abs(speed - self.target_speed) - SPEED_MARGIN
        dspeed /= SPEED_MARGIN
        self.dspeed.append((self.timestep, dspeed))


    def use_sample(self, sample):
        print('Sample:', sample)

        init_conds = sample.init_conditions
        self.target_speed = init_conds.target_speed[0]

        # Ego vehicle physics parameters
        com = carla.Vector3D(
            init_conds.center_of_mass[0],
            init_conds.center_of_mass[1],
            init_conds.center_of_mass[2],
        )
        wheels = [
            carla.WheelPhysicsControl(tire_friction=init_conds.tire_friction[0])
            for _ in range(4)
        ]
        self.vehicle_mass = init_conds.mass[0]
        physics = carla.VehiclePhysicsControl(
            mass=self.vehicle_mass,
            max_rpm=init_conds.max_rpm[0],
            center_of_mass=com,
            drag_coefficient=init_conds.drag_coefficient[0],
            wheels=wheels
        )

        # PID controller parameters
        opt_dict = {
            'target_speed': self.target_speed
        }

        # Deterministic blueprint, spawnpoint.
        blueprint = self.world.world.get_blueprint_library().find('vehicle.tesla.model3')
        spawn = self.world.map.get_spawn_points()[0]

        self.world.add_vehicle(PIDAgent, control_params=opt_dict,
                               blueprint=blueprint, spawn=spawn,
                               physics=physics, has_collision_sensor=True,
                               has_lane_sensor=True, ego=True)


    def trajectory_definition(self):
        # Get speed of collision as proportion of target speed
        collision = [(c[0], c[1] / self.target_speed)
                     for c in self.world.ego.collision_sensor.get_collision_speeds()]
        traj = {
            'dspeed': self.dspeed,
            'collision': collision,
            'laneinvade': self.world.ego.lane_sensor._history
        }
        return traj

simulation_data = DotMap()
simulation_data.port = PORT
simulation_data.bufsize = BUFSIZE
simulation_data.task = pid_control_task(SPEED_MARGIN)

client_task = ClientCarla(simulation_data)
while client_task.run_client():
    pass
print('End of all simulations.')
