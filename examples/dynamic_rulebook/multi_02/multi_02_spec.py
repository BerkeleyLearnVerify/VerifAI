import numpy as np

from rule_helpers import non_empty_indices, pairwise_distance_margin


@non_empty_indices()
def rule0(simulation, indices):  # safe distance to adv1
    return pairwise_distance_margin(
        simulation, indices, other_actor_idx=1, margin=8, reducer=np.min
    )


@non_empty_indices()
def rule1(simulation, indices):  # reach overtaking distance to adv2
    positions = np.array(simulation.result.trajectory)
    distances_to_adv2 = positions[indices, [0], :] - positions[indices, [2], :]
    distances_to_adv2 = np.linalg.norm(distances_to_adv2, axis=1)
    rho = np.max(distances_to_adv2, axis=0) - 10
    if rho < 0:
        return rho
    elif (
        np.max(indices) == len(simulation.result.trajectory) - 1
    ):  # lane change is not actually completed
        return -0.1
    return rho


@non_empty_indices()
def rule2(simulation, indices):  # safe distance to adv2 after lane change
    return pairwise_distance_margin(
        simulation, indices, other_actor_idx=2, margin=8, reducer=np.min
    )


@non_empty_indices()
def rule3(simulation, indices):  # safe distance to adv3
    return pairwise_distance_margin(
        simulation, indices, other_actor_idx=3, margin=8, reducer=np.min
    )
