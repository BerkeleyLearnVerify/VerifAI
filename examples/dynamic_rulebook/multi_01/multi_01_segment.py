import numpy as np


def segment_function(simulation):
    positions = np.array(simulation.result.trajectory)
    switch_idx_1 = len(simulation.result.trajectory)
    switch_idx_2 = len(simulation.result.trajectory)
    distances_to_obs = positions[:, 0, :] - positions[:, 1, :]
    distances_to_obs = np.linalg.norm(distances_to_obs, axis=1)
    for i in range(len(distances_to_obs)):
        if distances_to_obs[i] < 8.5 and switch_idx_1 == len(
            simulation.result.trajectory
        ):
            switch_idx_1 = i
            continue
        if (
            distances_to_obs[i] > 10
            and switch_idx_1 < len(simulation.result.trajectory)
            and switch_idx_2 == len(simulation.result.trajectory)
        ):
            switch_idx_2 = i
            break
    assert switch_idx_1 < len(
        simulation.result.trajectory
    ), "Switching point 1 cannot be found"

    indices_0 = np.arange(0, switch_idx_1)
    indices_1 = np.arange(switch_idx_1, switch_idx_2)
    indices_2 = np.arange(switch_idx_2, len(simulation.result.trajectory))

    return [indices_0, indices_1, indices_2]
