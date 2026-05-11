import numpy as np

from rule_helpers import (
    non_empty_indices,
    pairwise_distance_margin,
    record_margin,
    require_terminal_step,
)


@non_empty_indices()
def rule0(simulation, indices):  # A, 1: safe distance to ped
    return pairwise_distance_margin(
        simulation, indices, other_actor_idx=5, margin=8, reducer=np.min
    )


@non_empty_indices()
def rule1(simulation, indices):  # B, 1: safe distance to adv1
    return pairwise_distance_margin(
        simulation, indices, other_actor_idx=1, margin=8, reducer=np.min
    )


@non_empty_indices()
def rule2(simulation, indices):  # B, 2: safe distance to adv2
    return pairwise_distance_margin(
        simulation, indices, other_actor_idx=2, margin=8, reducer=np.min
    )


@non_empty_indices()
def rule3(simulation, indices):  # B, 3: safe distance to adv3
    return pairwise_distance_margin(
        simulation, indices, other_actor_idx=3, margin=8, reducer=np.min
    )


@non_empty_indices()
def rule4(simulation, indices):  # B, 4: safe distance to adv4
    return pairwise_distance_margin(
        simulation, indices, other_actor_idx=4, margin=8, reducer=np.min
    )


@non_empty_indices()
def rule5(simulation, indices):  # C: stay in drivable area
    return record_margin(
        simulation, indices, record_key="egoDistToDrivableRegion", reducer=np.max
    )


@non_empty_indices()
def rule6(
    simulation, indices
):  # D, 1: stay in the correct side of the road, before intersection
    return record_margin(
        simulation, indices, record_key="egoDistToEgoInitLane", reducer=np.max
    )


@non_empty_indices()
def rule7(
    simulation, indices
):  # D, 2: stay in the correct side of the road, after intersection
    return record_margin(
        simulation, indices, record_key="egoDistToEgoEndLane", reducer=np.max
    )


@non_empty_indices()
def rule8(simulation, indices):  # F: lane keeping
    return record_margin(
        simulation,
        indices,
        record_key="egoDistToEgoLaneCenterline",
        reducer=np.max,
        offset=0.4,
    )


@non_empty_indices()
@require_terminal_step()
def rule9(simulation, indices):  # H, 1: reach intersection
    return record_margin(
        simulation, indices, record_key="egoDistToIntersection", reducer=np.min
    )


@non_empty_indices()
@require_terminal_step()
def rule10(simulation, indices):  # H, 2: finish right-turn
    return record_margin(
        simulation, indices, record_key="egoDistToEgoEndLane", reducer=np.min
    )
