from abc import ABC, abstractmethod
import functools
import operator

import networkx as nx
import mtl

class Monitor(ABC):
    @abstractmethod
    def evaluate(self, result):
        raise NotImplementedError

    @classmethod
    def fromMTL(cls, formulas):
        """Build a Monitor from one or more MTL formulas."""
        if isinstance(formulas, str):
            formulas = [formulas]

        evaluators = [mtl.parse(formula) for formula in formulas]
        evaluator = functools.reduce(operator.and_, evaluators)

        def spec(result):
            if isinstance(result, dict):
                time_series = result
            else:  # Scenic Simulation object
                time_series = result.records

            return evaluator(time_series)

        return SimpleMonitor(spec)


class SimpleMonitor(Monitor):
    def __init__(self, specification):
        self.specification = specification

    def evaluate(self, result):
        return self.specification(result)


def to_monitor(spec):
    if isinstance(spec, Monitor):
        return spec
    return SimpleMonitor(spec)


class MultiObjectiveMonitor(SimpleMonitor):
    def __init__(self, specification, priority_graph=None, linearize=False):
        super().__init__(specification)
        self.linearize = linearize
        if priority_graph is None:
            self.graph = nx.DiGraph()
            # XXX num_objectives not defined here; accept a sequence of specifications instead?
            self.graph.add_nodes_from(range(self.num_objectives))
        else:
            self.graph = priority_graph
        if linearize: # "linearize" the prioritize graph by topologically sorting and connecting nodes
            self._linearize()
    
    def _linearize(self):
        new_graph = nx.DiGraph()
        S = set([node for node, degree in self.graph.in_degree() if degree == 0])
        nodes = []
        while len(S) > 0:
            n = random.choice(S)
            S.remove(n)
            nodes.append(n)
            neighbors = self.graph.neighbors(n)
            random.shuffle(neighbors)
            for m in neighbors:
                self.graph.remove_edge(n, m)
                if self.graph.in_degree(m) == 0:
                    S.add(m)
        new_graph.add_nodes_from(nodes)
        for i in range(1, len(nodes)):
            new_graph.add_edge(nodes[i - 1], nodes[i])
        self.graph = new_graph
