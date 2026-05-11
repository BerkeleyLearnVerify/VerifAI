import numpy as np


def segment_function(simulation):
    ego_dist_to_intersection = np.array(
        simulation.result.records["egoDistToIntersection"]
    )
    # Find switching points, i.e., ego has reached the intersection / ego has finished the left turn
    switch_idx_1 = len(simulation.result.trajectory)
    switch_idx_2 = len(simulation.result.trajectory)
    for i in range(len(ego_dist_to_intersection)):
        if ego_dist_to_intersection[i][1] == 0 and switch_idx_1 == len(
            simulation.result.trajectory
        ):
            switch_idx_1 = i
            break
    if switch_idx_1 < len(simulation.result.trajectory):
        for i in reversed(range(switch_idx_1, len(ego_dist_to_intersection))):
            if ego_dist_to_intersection[i][1] == 0:
                switch_idx_2 = i + 1
                break
    assert switch_idx_1 <= switch_idx_2
    indices_0 = np.arange(0, switch_idx_1)
    indices_1 = np.arange(switch_idx_1, switch_idx_2)
    indices_2 = np.arange(switch_idx_2, len(simulation.result.trajectory))

    return [indices_0, indices_1, indices_2]
