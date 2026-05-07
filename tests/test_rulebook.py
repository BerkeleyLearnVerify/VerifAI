import numpy as np
import pytest

from verifai.rulebook import Rulebook


class DummySimulation:
    class Result:
        def __init__(self, trajectory):
            self.trajectory = trajectory

    def __init__(self, values):
        self.values = np.array(values, dtype=float)
        self.result = DummySimulation.Result(list(values))


def test_rulebook_parses_rules_and_evaluates_segment(tmp_path):
    rule_file = tmp_path / "toy_spec.py"
    rule_file.write_text(
        "\n".join(
            [
                "import numpy as np",
                "",
                "def shift_by_one(fn):",
                "    def wrapped(simulation, indices):",
                "        return fn(simulation, indices) - 1.0",
                "    return wrapped",
                "",
                "@shift_by_one",
                "def rule0(simulation, indices):",
                "    return float(np.min(simulation.values[indices]))",
                "",
                "def helper(simulation, indices):",
                "    return 123.0",
                "",
                "def rule1(simulation, indices):",
                "    return float(np.max(simulation.values[indices]))",
            ]
        )
    )

    graph_file = tmp_path / "toy.graph"
    graph_file.write_text(
        "\n".join(
            [
                "# ID 0",
                "# Node list",
                "0 rule0",
                "1 rule1",
                "# Edge list",
                "0 1",
            ]
        )
    )

    segment_file = tmp_path / "toy_segment.py"
    segment_file.write_text(
        "\n".join(
            [
                "import numpy as np",
                "",
                "def segments(simulation):",
                "    return [np.array([0, 2])]",
            ]
        )
    )

    rb = Rulebook(
        str(graph_file),
        str(rule_file),
        str(segment_file),
        single_graph=True,
        verbosity=0,
    )

    # Ensure only rule* functions are parsed, in declaration order.
    assert list(rb.functions.keys()) == ["rule0", "rule1"]

    simulation = DummySimulation([5.0, 9.0, 7.0])
    rho = rb.evaluate_segment(simulation, graph_idx=0, indices=np.array([0, 2]))
    assert np.allclose(rho, np.array([4.0, 7.0]))


def test_rulebook_segment_file_requires_single_function(tmp_path):
    rule_file = tmp_path / "toy_spec.py"
    rule_file.write_text(
        "\n".join(
            [
                "def rule0(simulation, indices):",
                "    return 0.0",
            ]
        )
    )

    graph_file = tmp_path / "toy.graph"
    graph_file.write_text(
        "\n".join(
            [
                "# ID 0",
                "# Node list",
                "0 rule0",
                "# Edge list",
            ]
        )
    )

    bad_segment_file = tmp_path / "bad_segment.py"
    bad_segment_file.write_text(
        "\n".join(
            [
                "def seg0(simulation):",
                "    return []",
                "",
                "def seg1(simulation):",
                "    return []",
            ]
        )
    )

    with pytest.raises(ValueError, match="Multiple functions found in segment function file"):
        Rulebook(
            str(graph_file),
            str(rule_file),
            str(bad_segment_file),
            single_graph=True,
            verbosity=0,
        )


def test_rulebook_rejects_edge_with_missing_node(tmp_path):
    rule_file = tmp_path / "toy_spec.py"
    rule_file.write_text(
        "\n".join(
            [
                "def rule0(simulation, indices):",
                "    return 0.0",
                "",
                "def rule1(simulation, indices):",
                "    return 1.0",
            ]
        )
    )

    # Node 1 exists but node 2 does not, so 1 -> 2 should fail.
    graph_file = tmp_path / "bad.graph"
    graph_file.write_text(
        "\n".join(
            [
                "# ID 0",
                "# Node list",
                "0 rule0",
                "1 rule1",
                "# Edge list",
                "1 2",
            ]
        )
    )

    segment_file = tmp_path / "toy_segment.py"
    segment_file.write_text(
        "\n".join(
            [
                "def segments(simulation):",
                "    return [[]]",
            ]
        )
    )

    with pytest.raises(ValueError, match="Edge refers to non-existent node"):
        Rulebook(
            str(graph_file),
            str(rule_file),
            str(segment_file),
            single_graph=True,
            verbosity=0,
        )
