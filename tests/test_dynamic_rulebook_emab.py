import networkx as nx
import pytest
from dotmap import DotMap

from verifai.features import Box
from verifai.samplers.dynamic_rulebook_emab import (
    DynamicRulebookExtendedMultiArmedBanditSampler,
)


class RulebookStub:
    def __init__(self, priority_graphs, using_sampler=-1, exploration_ratio=2.0):
        self.priority_graphs = priority_graphs
        self.using_sampler = using_sampler
        self.exploration_ratio = exploration_ratio
        self.using_continuous = False


class SegmentSamplerSpy:
    def __init__(self, name):
        self.name = name
        self.update_calls = []

    def getSample(self):
        return f"{self.name}_sample", f"{self.name}_info"

    def update(self, sample, info, rho):
        self.update_calls.append((sample, info, rho))


def _make_graph(node_id=0):
    graph = nx.DiGraph()
    graph.add_node(node_id)
    return graph


def _make_params(rulebook):
    params = DotMap(alpha=0.9, thres=0.0)
    params.cont.buckets = 3
    params.cont.dist = None
    params.rulebook = rulebook
    return params


def test_demab_requires_rulebook():
    params = DotMap(alpha=0.9, thres=0.0, rulebook=None)
    params.cont.buckets = 3
    params.cont.dist = None

    with pytest.raises(ValueError, match="demab_params.rulebook must be set"):
        DynamicRulebookExtendedMultiArmedBanditSampler(Box((0, 1)), params)


def test_demab_rejects_nonconsecutive_priority_graph_ids():
    rb = RulebookStub(priority_graphs={0: _make_graph(), 2: _make_graph()})
    params = _make_params(rb)

    with pytest.raises(
        ValueError, match="Priority graph IDs should be in order and start from 0"
    ):
        DynamicRulebookExtendedMultiArmedBanditSampler(Box((0, 1)), params)


def test_demab_round_robin_and_fixed_sampler_routing():
    rb = RulebookStub(
        priority_graphs={0: _make_graph(), 1: _make_graph()}, using_sampler=-1
    )
    sampler = DynamicRulebookExtendedMultiArmedBanditSampler(
        Box((0, 1)), _make_params(rb)
    )

    spy0 = SegmentSamplerSpy("seg0")
    spy1 = SegmentSamplerSpy("seg1")
    sampler.split_samplers = {0: spy0, 1: spy1}
    sampler.num_segs = 2

    sample0, info0 = sampler.getSample()
    assert (sample0, info0) == ("seg0_sample", "seg0_info")
    sampler.update(sample0, info0, [0.1, -0.2])
    assert sampler.sampler_idx == 1
    assert spy0.update_calls[-1] == ("seg0_sample", "seg0_info", 0.1)
    assert spy1.update_calls[-1] == ("seg0_sample", "seg0_info", -0.2)

    sample1, info1 = sampler.getSample()
    assert (sample1, info1) == ("seg1_sample", "seg1_info")

    rb_fixed = RulebookStub(
        priority_graphs={0: _make_graph(), 1: _make_graph()}, using_sampler=1
    )
    fixed = DynamicRulebookExtendedMultiArmedBanditSampler(
        Box((0, 1)), _make_params(rb_fixed)
    )
    fixed0 = SegmentSamplerSpy("fixed0")
    fixed1 = SegmentSamplerSpy("fixed1")
    fixed.split_samplers = {0: fixed0, 1: fixed1}
    fixed.num_segs = 2

    fixed_sample, fixed_info = fixed.getSample()
    assert (fixed_sample, fixed_info) == ("fixed1_sample", "fixed1_info")
    fixed.update(fixed_sample, fixed_info, [5.0, 7.0])
    assert fixed0.update_calls == []
    assert fixed1.update_calls[-1] == ("fixed1_sample", "fixed1_info", 7.0)
