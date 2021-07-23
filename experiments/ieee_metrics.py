from __future__ import print_function
import numpy as np
from verifai.monitor import specification_monitor
from sympy import *
import sympy.calculus.util
import sys
import threading
import pickle
import os
from time import sleep
try:
    import thread
except ImportError:
    import _thread as thread

def quit_function(fn_name):
    # print to stderr, unbuffered in Python 2.
    print('{0} took too long'.format(fn_name), file=sys.stderr)
    sys.stderr.flush() # Python 3 stderr is likely buffered.
    thread.interrupt_main() # raises KeyboardInterrupt

def exit_after(s):
    '''
    use as decorator to exit process if 
    function takes longer than s seconds
    '''
    def outer(fn):
        def inner(*args, **kwargs):
            timer = threading.Timer(s, quit_function, args=[fn.__name__])
            timer.start()
            try:
                result = fn(*args, **kwargs)
            finally:
                timer.cancel()
            return result
        return inner
    return outer

class time_to_collision(specification_monitor):

    DISTANCE_THRESHOLD = 5
    TTC_THRESHOLD = 2
    
    @exit_after(30)
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
            positions = np.array(simulation.result.trajectory[1:])
            if positions.shape[1] < 2:
                return np.inf
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
            if ttc.shape[0] == 0:
                return np.inf
            return np.min(ttc) - self.TTC_THRESHOLD
        
        super().__init__(specification)

class braking_projection(specification_monitor):

    DISTANCE_THRESHOLD = 5
    MAX_ACCELERATION = -4.5
    
    @exit_after(30)
    def __init__(self):
        v1x, v1y, v2x, v2y = symbols('v_{1x} v_{1y} v_{2x} v_{2y}')
        x10, y10, x20, y20 = symbols('x_{10} y_{10} x_{20} y_{20}')
        a1x, a1y, a2x, a2y = symbols('a_{1x} a_{1y} a_{2x} a_{2y}')
        t, t1, t2 = symbols('t t_1 t_2')
        self.t = t
        # first segment: before first car stops
        x1 = v1x*t + x10 + 0.5*a1x*t**2
        y1 = v1y*t + y10 + 0.5*a1y*t**2
        x2 = v2x*t + x20 + 0.5*a2x*t**2
        y2 = v2y*t + y20 + 0.5*a2y*t**2
        dist_1 = (y2 - y1)**2 + (x2 - x1)**2
        # second segment: after first car stops
        xB1 = v1x*t1 + x10 + 0.5*a1x*t1**2
        yB1 = v1y*t1 + y10 + 0.5*a1y*t1**2
        xB2 = v2x*t + x20 + 0.5*a2x*t**2 
        yB2 = v2y*t + y20 + 0.5*a2y*t**2 
        xD1 = v1x*t + x10 + 0.5*a1x*t**2 
        yD1 = v1y*t + y10 + 0.5*a1y*t**2 
        xD2 = v2x*t2 + x20 + 0.5*a2x*t2**2
        yD2 = v2y*t2 + y20 + 0.5*a2y*t2**2
        dist_2B = (yB2 - yB1)**2 + (xB2 - xB1)**2
        dist_2D = (yD2 - yD1)**2 + (xD2 - xD1)**2
        dist_1f = lambdify((
                v1x, v1y, v2x, v2y,
                x10, y10, x20, y20,
                a1x, a1y, a2x, a2y
        ), dist_1)
        dist_2Bf = lambdify((
                v1x, v1y, v2x, v2y,
                x10, y10, x20, y20,
                a1x, a1y, a2x, a2y,
                t1
        ), dist_2B)
        dist_2Df = lambdify((
                v1x, v1y, v2x, v2y,
                x10, y10, x20, y20,
                a1x, a1y, a2x, a2y,
                t2
        ), dist_2D)
        def specification(simulation):
            positions = np.array(simulation.result.trajectory)
            if positions.shape[1] < 2:
                return np.inf
            velocities = np.diff(positions, axis=0) / simulation.timestep
            accelerations = np.diff(velocities, axis=0) / simulation.timestep
            ego_x, ego_v = positions[2:, 0, :], velocities[1:, 0, :]
            other_x, other_v = positions[2:, 1, :], velocities[1:, 1, :]
            mask_ego = (np.linalg.norm(ego_v, axis=1) != 0.0)
            mask_other = (np.linalg.norm(other_v, axis=1) != 0.0)
            ego_x = ego_x[mask_ego & mask_other]
            ego_v = ego_v[mask_ego & mask_other]
            other_x = other_x[mask_ego & mask_other]
            other_v = other_v[mask_ego & mask_other]
            ego_heading = ego_v / np.linalg.norm(ego_v, axis=1)[:, np.newaxis]
            other_heading = other_v / np.linalg.norm(other_v, axis=1)[:, np.newaxis]
            ego_a = self.MAX_ACCELERATION * ego_heading
            other_a = self.MAX_ACCELERATION * other_heading
            dist1_function = dist_1f(
                ego_v[:, 0],
                ego_v[:, 1],
                other_v[:, 0],
                other_v[:, 1],
                ego_x[:, 0],
                ego_x[:, 1],
                other_x[:, 0],
                other_x[:, 1],
                ego_a[:, 0],
                ego_a[:, 1],
                other_a[:, 0],
                other_a[:, 1],
            )

            t1_vals_x = -ego_v[:, 0]/ego_a[:, 0]
            t1_vals_y = -ego_v[:, 1]/ego_a[:, 1]
            t2_vals_x = -ego_v[:, 0]/ego_a[:, 0]
            t2_vals_y = -ego_v[:, 1]/ego_a[:, 1]

            t1_vals = np.maximum(np.nan_to_num(t1_vals_x), np.nan_to_num(t1_vals_y))
            t2_vals = np.maximum(np.nan_to_num(t2_vals_x), np.nan_to_num(t2_vals_y))

            dist2B_function = dist_2Bf(
                ego_v[:, 0],
                ego_v[:, 1],
                other_v[:, 0],
                other_v[:, 1],
                ego_x[:, 0],
                ego_x[:, 1],
                other_x[:, 0],
                other_x[:, 1],
                ego_a[:, 0],
                ego_a[:, 1],
                other_a[:, 0],
                other_a[:, 1],
                t1_vals,
            )
            dist2D_function = dist_2Df(
                ego_v[:, 0],
                ego_v[:, 1],
                other_v[:, 0],
                other_v[:, 1],
                ego_x[:, 0],
                ego_x[:, 1],
                other_x[:, 0],
                other_x[:, 1],
                ego_a[:, 0],
                ego_a[:, 1],
                other_a[:, 0],
                other_a[:, 1],
                t2_vals,
            )



            # min_dist_vals = []
            # breakpoint()
            def helper (args):
                f1, f2b, f2d, t1_val, t2_val =args
                if t1_val < t2_val:
                    seg1 = sympy.calculus.util.minimum(f1, self.t, sympy.calculus.util.Interval(0, t1_val))
                    seg2 = sympy.calculus.util.minimum(f2b, self.t, sympy.calculus.util.Interval(t1_val , t2_val))
                else: 
                    seg1 = sympy.calculus.util.minimum(f1, self.t, sympy.calculus.util.Interval(0, t2_val))
                    seg2 = sympy.calculus.util.minimum(f2d, self.t, sympy.calculus.util.Interval(t2_val , t1_val))
                return min(seg1, seg2)

            
            arguments = zip(dist1_function, dist2B_function, dist2D_function, t1_vals, t2_vals)
            min_dist_vals = np.array([helper(args) for args in arguments])

            if min_dist_vals.shape[0] == 0:
                return np.inf
            return np.min(min_dist_vals) - self.DISTANCE_THRESHOLD
        
        super().__init__(specification)

class staying_in_lane(specification_monitor):

    def __init__(self):
        def specification(simulation):
            return 0.5 - np.mean(np.abs(simulation.scene.params['distToLaneCenter']))
        super().__init__(specification)

class reached_destination(specification_monitor):

    def __init__(self):
        def specification(simulation):
            start = simulation.result.trajectory[0][0]
            end = simulation.result.trajectory[-1][0]
            return start.distanceTo(end) - 5
        super().__init__(specification)
