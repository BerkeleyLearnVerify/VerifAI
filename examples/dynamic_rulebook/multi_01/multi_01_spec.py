import numpy as np

from rule_helpers import non_empty_indices, pairwise_distance_margin


@non_empty_indices()
def rule0(simulation, indices):  # safe distance to obstacle
    return pairwise_distance_margin(
        simulation, indices, other_actor_idx=1, margin=3, reducer=np.min
    )


@non_empty_indices()
def rule1(simulation, indices):  # ego is in the left lane
    ego_is_in_left_lane = np.array(
        simulation.result.records["egoIsInLeftLane"], dtype=bool
    )
    for i in indices:
        if ego_is_in_left_lane[i][1]:
            return -1
    return 1
