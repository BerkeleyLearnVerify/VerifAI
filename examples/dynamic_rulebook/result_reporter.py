"""Shared utilities for result reporting across multi-objective scenarios."""

import numpy as np


def print_result_summary(result_counts, counterexample_types, source_idx=0):
    """Print error weights and counterexample types summary.
    
    Args:
        result_counts: List of per-source result count arrays (one per segment).
        counterexample_types: List of per-source counterexample type dicts (one per segment).
        source_idx: Index of the source to report (default 0).
    """
    print('Error weights')
    for seg_idx, per_source_results in enumerate(result_counts):
        values = per_source_results[source_idx]
        avg = np.mean(values) if values else 0.0
        max_val = np.max(values) if values else 0
        pct = float(np.count_nonzero(values) / len(values)) if values else 0.0
        print(f'segment {seg_idx}:')
        print('average:', avg, 'max:', max_val, 'percentage:', pct, values)

    print('\nCounterexample types')
    for seg_idx, per_source_types in enumerate(counterexample_types):
        type_map = per_source_types[source_idx]
        print(f'segment {seg_idx}:')
        print('Types:', len(type_map))
        for key, value in reversed(sorted(type_map.items(), key=lambda x: x[0])):
            print("{} : {}".format(key, value))
    print()
