from abc import ABC, abstractmethod
import functools
import inspect
import operator

import networkx as nx
import numpy as np
import mtl

class Monitor(ABC):
    """A (multi-objective) specification which can be evaluated over a simulation.

    A Monitor can be created in several ways:

        * From a Metric Temporal Logic formula using `Monitor.fromMTL`.
        * From a (list of) objective functions using `Monitor.fromFunction`.
        * By defining your own subclass implementing the `evaluate` method.
    """

    @abstractmethod
    def evaluate(self, result):
        """Evaluate the specification given the result of a simulation.

        Args:
            result: The simulation result, either as a `Simulation` object (if
              using Scenic) or a dict of time series.

        Returns:
            A number representing to what extent the specification was satisfied
            (positive satisfied, negative violated), or a sequence of such numbers
            if using multiple specifications.
        """
        raise NotImplementedError

    @classmethod
    def fromMTL(cls, formulas):
        """Build a Monitor from one or more MTL formulas.

        See the `py-metric-temporal-logic <https://github.com/mvcisback/py-metric-temporal-logic#string-based-api>`_
        documentation for the supported syntax.
        """
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

    @classmethod
    def fromFunctions(cls, functions):
        """Build a Monitor from one or more objective functions to minimize.

        If multiple functions are provided, this method returns a
        `MultiObjectiveMonitor` with all objectives having equal priority.
        Instantiate that class directly if you want to specify a priority graph.

        Args:
            functions: A function or iterable of functions to use.
        """
        if inspect.isfunction(functions):
            return SimpleMonitor(functions)
        functions = tuple(functions)
        return MultiObjectiveMonitor(functions)


class SimpleMonitor(Monitor):
    def __init__(self, specification):
        self.specification = specification

    def evaluate(self, result):
        return self.specification(result)


def to_monitor(spec):
    if isinstance(spec, Monitor):
        return spec
    if spec is None:
        spec = lambda result: np.inf
    return Monitor.fromFunctions(spec)


class MultiObjectiveMonitor(SimpleMonitor):
    def __init__(
        self,
        objectives,
        priority_graph=None,
        linearize=False,
        num_objectives=None,
    ):
        if not inspect.isfunction(objectives):
            specs = tuple(objectives)
            if num_objectives is None:
                num_objectives = len(specs)
            elif num_objectives != len(specs):
                raise ValueError("num_objectives does not match provided objectives")
            specification = lambda result: tuple(spec(result) for spec in specs)
        else:
            if num_objectives is None:
                if priority_graph is None:
                    raise ValueError("must specify either priority_graph or num_objectives")
                num_objectives = len(priority_graph)
            elif priority_graph is not None and num_objectives != len(priority_graph):
                raise ValueError("number of nodes in priority graph does not match num_objectives")
            specification = objectives
        self.num_objectives = num_objectives
        super().__init__(specification)

        self.linearize = linearize
        if priority_graph is None:
            self.graph = nx.DiGraph()
            self.graph.add_nodes_from(range(num_objectives))
        else:
            self.graph = priority_graph
        if linearize: # "linearize" the priority graph by topologically sorting and connecting nodes
            self._linearize()
        assert len(self.graph) == self.num_objectives
    
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
