from functools import wraps

import numpy as np


def non_empty_indices(default=1):
    """Return default value when no time indices are active."""

    def decorator(func):
        @wraps(func)
        def wrapper(simulation, indices):
            if indices.size == 0:
                return default
            return func(simulation, indices)

        return wrapper

    return decorator


def require_terminal_step(default=1):
    """Evaluate only when the active interval reaches the final trajectory step."""

    def decorator(func):
        @wraps(func)
        def wrapper(simulation, indices):
            if np.max(indices) < len(simulation.result.trajectory) - 1:
                return default
            return func(simulation, indices)

        return wrapper

    return decorator


def pairwise_distance_margin(simulation, indices, other_actor_idx, margin, reducer=np.min):
    """Robustness margin based on ego-other actor Euclidean distance."""
    positions = np.array(simulation.result.trajectory)
    distances = positions[indices, [0], :] - positions[indices, [other_actor_idx], :]
    distances = np.linalg.norm(distances, axis=1)
    return reducer(distances, axis=0) - margin


def record_margin(
    simulation,
    indices,
    record_key,
    reducer=np.max,
    sign=-1.0,
    offset=0.0,
    component=1,
):
    """Generic margin computed from a scalar record timeseries."""
    values = np.array(simulation.result.records[record_key])
    summary = reducer(values[indices], axis=0)[component]
    return offset + sign * summary
