
import math
import os.path
import sys

from dotmap import DotMap

from verifai import ScenicSampler, Falsifier, Monitor

# Load the Scenic scenario and create a sampler from it
if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = os.path.join(os.path.dirname(__file__), 'newtonian/carlaChallenge2.scenic')
sampler = ScenicSampler.fromScenario(path, mode2D=True)

# Define the specification (i.e. evaluation metric) as an MTL formula.
# Our example spec will say that the ego object stays at least 5 meters away
# from all other objects. See the Scenic file for the defintion of the
# signal "safe".
monitor = Monitor.fromMTL("G safe")

# Alternatively, we can define the specification manually as a function
# taking the Scenic Simulation object as an argument.
def specification(simulation):
    # Get trajectories of objects from the result of the simulation
    traj = simulation.result.trajectory

    # Compute sequence of values for 'safe' atomic proposition;
    # we'll define safe = "distance from ego to all other objects > 5"
    safe_values = []
    for positions in traj:
        ego = positions[0]
        dist = min((ego.distanceTo(other) for other in positions[1:]),
                   default=math.inf)
        safe_values.append(dist - 5)

    # Minimize over time steps, so value will be negative if the ego ever gets
    # closer than 5 meters to another object
    return min(safe_values)

# Set up the falsifier
falsifier_params = DotMap(
    n_iters=5,
    verbosity=1,
    save_error_table=True,
    save_safe_table=True,
    # uncomment to save these tables to files; we'll print them out below
    # error_table_path='error_table.csv',
    # safe_table_path='safe_table.csv'
)
server_options = DotMap(maxSteps=100, verbosity=0)
falsifier = Falsifier(sampler=sampler,
                      monitor=monitor,  # could also put `specification` here
                      falsifier_params=falsifier_params,
                      server_options=server_options)

# Perform falsification and print the results
falsifier.run_falsifier()
print('Error table:')
print(falsifier.error_table.table)
print('Safe table:')
print(falsifier.safe_table.table)
