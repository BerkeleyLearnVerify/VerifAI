import pytest
import numpy as np
import pandas as pd

from verifai.compositional_analysis import ScenarioBase, CompositionalAnalysisEngine


def test_scenario_base_basic_stats():
    # Create a simple dataset with 3 traces
    # Final labels: trace1 -> 1, trace2 -> 0, trace3 -> 1 → mean = 2/3
    df = pd.DataFrame({
        "trace_id": ["t1", "t1", "t2", "t2", "t3"],
        "step":     [0,    1,    0,    1,    0],
        "label":    [0,    1,    1,    0,    1],
    })

    sb = ScenarioBase({"test_scenario": df}, delta=0.05)

    rho = sb.get_success_prob("test_scenario")
    uncertainty = sb.get_success_prob_uncertainty("test_scenario")

    # Check mean
    assert np.isclose(rho, 2/3)

    # Check Hoeffding bound
    n = 3  # number of traces
    expected_eps = np.sqrt(np.log(2 / 0.05) / (2 * n))
    assert np.isclose(uncertainty, expected_eps)


def test_empty_dataframe():
    df = pd.DataFrame(columns=["trace_id", "step", "label"])
    sb = ScenarioBase({"empty": df})

    assert sb.get_success_prob("empty") == 0.0
    assert sb.get_success_prob_uncertainty("empty") == 0.0


def test_missing_columns_raises():
    df = pd.DataFrame({
        "trace_id": ["t1"],
        "step": [0],
        # missing "label"
    })

    with pytest.raises(Exception):
        ScenarioBase({"bad": df})


def make_df(trace_ids, steps, labels, x_vals):
    return pd.DataFrame({
        "trace_id": trace_ids,
        "step": steps,
        "label": labels,
        "x": x_vals,
    })


def test_check_single_scenario():
    df = make_df(
        ["t1", "t1", "t2", "t2"],
        [0, 1, 0, 1],
        [0, 1, 1, 0],
        [0.0, 1.0, 0.5, 0.2],
    )

    sb = ScenarioBase({"A": df})
    engine = CompositionalAnalysisEngine(sb)

    rho, eps = engine.check(["A"], features=["x"])

    assert np.isclose(rho, sb.get_success_prob("A"))
    assert np.isclose(eps, sb.get_success_prob_uncertainty("A"))


def test_check_empty_scenario_raises():
    sb = ScenarioBase({"A": pd.DataFrame(columns=["trace_id", "step", "label"])})
    engine = CompositionalAnalysisEngine(sb)

    with pytest.raises(ValueError):
        engine.check([], features=["x"])


def test_check_missing_features_raises():
    sb = ScenarioBase({"A": pd.DataFrame(columns=["trace_id", "step", "label"])})
    engine = CompositionalAnalysisEngine(sb)

    with pytest.raises(ValueError):
        engine.check(["A"], features=None)


def test_check_insufficient_samples_returns_zero():
    # Only 1 successful endpoint → KDE should early return (0,0)
    df_s = make_df(
        ["t1"], [0], [1], [0.0]
    )
    df_t = make_df(
        ["t2"], [0], [1], [0.1]
    )

    sb = ScenarioBase({"A": df_s, "B": df_t})
    engine = CompositionalAnalysisEngine(sb)

    rho, eps = engine.check(["A", "B"], features=["x"])

    assert rho == 0.0
    assert eps == 0.0


def test_falsify_single_scenario_returns_failure_trace():
    df = pd.DataFrame({
        "trace_id": ["t1", "t1", "t2", "t2"],
        "step": [0, 1, 0, 1],
        "label": [1, 1, 0, 0],  # t2 fails
        "x": [0.0, 0.1, 1.0, 1.1],
    })

    sb = ScenarioBase({"A": df})
    engine = CompositionalAnalysisEngine(sb)

    trace = engine.falsify(["A"], features=["x"])

    assert trace is not None
    assert (trace["label"].iloc[-1] == 0)  # ends in failure


def test_falsify_no_failure_returns_none():
    df = pd.DataFrame({
        "trace_id": ["t1", "t1"],
        "step": [0, 1],
        "label": [1, 1],  # no failures
        "x": [0.0, 0.1],
    })

    sb = ScenarioBase({"A": df})
    engine = CompositionalAnalysisEngine(sb)

    trace = engine.falsify(["A"], features=["x"])

    assert trace is None


def test_falsify_empty_scenario_raises():
    sb = ScenarioBase({"A": pd.DataFrame(columns=["trace_id", "step", "label"])})
    engine = CompositionalAnalysisEngine(sb)

    with pytest.raises(ValueError):
        engine.falsify([], features=["x"])


def test_falsify_missing_features_raises():
    sb = ScenarioBase({"A": pd.DataFrame(columns=["trace_id", "step", "label"])})
    engine = CompositionalAnalysisEngine(sb)

    with pytest.raises(ValueError):
        engine.falsify(["A"], features=None)

