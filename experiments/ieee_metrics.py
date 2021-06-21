import numpy as np
from verifai.monitor import specification_monitor
from sympy import *

class time_to_collision(specification_monitor):

    DISTANCE_THRESHOLD = 5
    TTC_THRESHOLD = 2
    
    def __init__(self):
        v1x, v1y, v2x, v2y = symbols('v_{1x} v_{1y} v_{2x} v_{2y}')
        x10, y10, x20, y20 = symbols('x_{10} y_{10} x_{20} y_{20}')
        t = symbols('t')
        x1 = v1x*t + x10
        y1 = v1y*t + y10
        x2 = v2x*t + x20
        y2 = v2y*t + y20
        dist = (y2 - y1)**2 + (x2 - x1)**2
        sols = solve(dist - self.DISTANCE_THRESHOLD**2)
        t1, t2 = sols[0][t], sols[1][t]
        t1f = lambdify((
                v1x, v1y, v2x, v2y,
                x10, y10, x20, y20
        ), t1)
        t2f = lambdify((
                v1x, v1y, v2x, v2y,
                x10, y10, x20, y20
        ), t2)
        def specification(simulation):
            positions = np.array(simulation.result.trajectory)
            velocities = np.diff(positions, axis=0) / simulation.timestep
            accelerations = np.diff(velocities, axis=0) / simulation.timestep
            ego_x, ego_v, ego_a = positions[2:, 0, :], velocities[1:, 0, :], accelerations[:, 0, :]
            other_x, other_v, other_a = positions[2:, 1, :], velocities[1:, 1, :], accelerations[:, 1, :]
            t1_vals = t1f(
                ego_v[:, 0],
                ego_v[:, 1],
                other_v[:, 0],
                other_v[:, 1],
                ego_x[:, 0],
                ego_x[:, 1],
                other_x[:, 0],
                other_x[:, 1],
            )
            t2_vals = t2f(
                ego_v[:, 0],
                ego_v[:, 1],
                other_v[:, 0],
                other_v[:, 1],
                ego_x[:, 0],
                ego_x[:, 1],
                other_x[:, 0],
                other_x[:, 1],
            )
            mask = (t1_vals*t2_vals<0) | ((t1_vals > 0) & (t2_vals > 0))
            t1_vals, t2_vals = t1_vals[mask], t2_vals[mask]
            ttc = np.maximum(np.min([t1_vals, t2_vals], axis=0), 0)
            return np.min(ttc) - self.TTC_THRESHOLD
        
        super().__init__(specification)