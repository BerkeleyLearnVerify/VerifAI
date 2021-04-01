"""Example aircraft controller.

This controller simply applies a constant throttle, and uses a proportional
controller for the rudder based on the ground truth cross-track and heading
errors.
"""

throttle = 0.4  # constant throttle of plane
cte_gain = 0.1  # gain for cross-track error
he_gain = 0.05  # gain for heading error
from verifai.simulators.xplane.utils.geometry import (euclidean_dist, quaternion_for,
    initial_bearing, cross_track_distance, compute_heading_error)

#def control(server, lat, lon, psi, cte, heading_err):
def control(server, cache):
    # Get current plane state
    # Use modified getPOSI to get lat/lon in double precision
    lat, lon, _, _, _, psi, _ = self.xpcserver.getPOSI()
    # Compute cross-track and heading errors
    #ctes.append(cte); hes.append(heading_err)
    cte = cross_track_distance(start_lat, start_lon, end_lat, end_lon, lat, lon)
    heading_err = compute_heading_error(self.desired_heading, psi)
    var_label_map = {'lat': lat, 'lon': lon, 'psi': psi, 'cte': cte, 'he': heading_err}
    rudder = (cte_gain * cte) + (he_gain * heading_err)
    server.sendCTRL([0.0, 0.0, rudder, throttle])
    return var_label_map
