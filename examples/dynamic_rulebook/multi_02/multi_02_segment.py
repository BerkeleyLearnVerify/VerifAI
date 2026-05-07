import numpy as np


def segment_function(simulation):
    # Extract trajectory information
    ego_is_in_init_lane = np.array(simulation.result.records["egoIsInInitLane"])
    adv2_is_in_init_lane = np.array(simulation.result.records["adv2IsInInitLane"])
    adv3_is_in_init_lane = np.array(simulation.result.records["adv3IsInInitLane"])

    # Find starting point, i.e., adv2 and adv3 have reached the new lane
    start_idx = -1
    for i in range(len(adv2_is_in_init_lane)):
        if adv2_is_in_init_lane[i][1] == 0 and adv3_is_in_init_lane[i][1] == 0:
            start_idx = i
            break
    assert start_idx != -1, "Starting point not found"

    # Find switching point, i.e., ego has reached the new lane
    switch_idx = len(simulation.result.trajectory)
    for i in range(start_idx, len(ego_is_in_init_lane)):
        if ego_is_in_init_lane[i][1] == 0:
            switch_idx = i
            break
    assert (
        switch_idx > start_idx
    ), "Switching point should be larger than starting point"

    # Evaluation
    indices_0 = np.arange(start_idx, switch_idx)
    indices_1 = np.arange(switch_idx, len(simulation.result.trajectory))

    return [indices_0, indices_1]
