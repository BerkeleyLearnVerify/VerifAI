from abc import ABC
import mtl
import ast
import os

import networkx as nx
import numpy as np

from verifai.monitor import specification_monitor


class Rulebook(ABC):

    def __init__(
        self,
        graph_path,
        rule_file,
        segment_func_path,
        save_path=None,
        single_graph=False,
        using_sampler=-1,
        exploration_ratio=2.0,
        verbosity=1,
        using_continuous=False,
    ):
        self.priority_graphs = {}
        self.using_sampler = using_sampler
        self.exploration_ratio = exploration_ratio
        self.verbosity = verbosity
        self.using_continuous = using_continuous
        if verbosity >= 1:
            print("(rulebook.py) Parsing rules...")
        self._parse_rules(rule_file)
        if verbosity >= 1:
            print("(rulebook.py) Parsing rulebooks...")
        if single_graph:
            self._parse_rulebook(graph_path)
        else:
            self._parse_rulebooks(graph_path)
        self.single_graph = single_graph
        if sorted(self.priority_graphs.keys()) != list(range(len(self.priority_graphs))):
            raise ValueError("Priority graph IDs should be in order and start from 0")
        if verbosity >= 1:
            print("(rulebook.py) Parsing the segment function...")
        self._parse_segment_function(segment_func_path)
        self.save_path = save_path

    def _parse_rules(self, file_path):
        with open(file_path, "r") as file:
            file_contents = file.read()

        tree = ast.parse(file_contents)
        module_code = compile(tree, file_path, "exec")

        namespace = {}
        exec(module_code, namespace)

        self.functions = {}
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) and node.name.startswith("rule"):
                function = namespace.get(node.name)
                if not callable(function):
                    raise ValueError(
                        f"Rule function {node.name} is not callable in {file_path}"
                    )
                self.functions[node.name] = function

        if self.verbosity >= 1:
            print(f"(rulebook.py) Parsed functions: {self.functions}")

    def _parse_rulebooks(self, dir):
        if os.path.isdir(dir):
            for root, _, files in os.walk(dir):
                for name in files:
                    fname = os.path.join(root, name)
                    if os.path.splitext(fname)[1] == ".graph":
                        self._parse_rulebook(fname)
        else:
            raise ValueError(
                f"Rulebook graph path must be an existing directory."
            )

    def _parse_rulebook(self, file):
        priority_graph = nx.DiGraph()
        graph_id = -1
        with open(file, "r") as f:
            lines = f.readlines()
            node_section = False
            edge_section = False
            for line in lines:
                line = line.strip()
                if line.startswith("# ID"):
                    graph_id = int(line.split(" ")[-1])
                    if self.verbosity >= 1:
                        print(f"(rulebook.py) Parsing graph {graph_id}")
                if line == "# Node list":
                    node_section = True
                    continue
                elif line == "# Edge list":
                    node_section = False
                    edge_section = True
                    continue

                # Node
                if node_section:
                    node_info = line.split(" ")
                    node_id = int(node_info[0])
                    rule_name = node_info[1]
                    ru = rule(node_id, self.functions[rule_name])
                    priority_graph.add_node(node_id, rule=ru, name=rule_name)
                    if self.verbosity >= 2:
                        print(f"Add node {node_id} with rule {rule_name}")

                # Edge
                if edge_section:
                    edge_info = line.split(" ")
                    src = int(edge_info[0])
                    dst = int(edge_info[1])
                    if not priority_graph.has_node(src) or not priority_graph.has_node(
                        dst
                    ):
                        raise ValueError(
                            f"Edge refers to non-existent node: {src} -> {dst}"
                        )
                    priority_graph.add_edge(src, dst)
                    if self.verbosity >= 2:
                        print(f"Add edge from {src} to {dst}")

        self.priority_graphs[graph_id] = priority_graph

    def _parse_segment_function(self, file_path):
        # Parse the function that outputs the indices for different segments
        with open(file_path, "r") as file:
            file_contents = file.read()

        tree = ast.parse(file_contents)
        module_code = compile(tree, file_path, "exec")

        namespace = {}
        exec(module_code, namespace)

        segment_defs = [
            node for node in tree.body if isinstance(node, ast.FunctionDef)
        ]
        if len(segment_defs) == 0:
            raise ValueError("No function found in segment function file")
        if len(segment_defs) > 1:
            raise ValueError("Multiple functions found in segment function file")

        function_node = segment_defs[0]
        self.segment_function = namespace.get(function_node.name)
        if not callable(self.segment_function):
            raise ValueError(
                f"Segment function {function_node.name} is not callable in {file_path}"
            )

    def evaluate_segment(self, traj, graph_idx=0, indices=None):
        # Evaluate the result of each rule on the segment traj[indices] of the trajectory
        priority_graph = self.priority_graphs[graph_idx]
        rho = np.ones(len(priority_graph.nodes))
        idx = 0
        for id in sorted(priority_graph.nodes):
            rule = priority_graph.nodes[id]["rule"]
            rho[idx] = rule.evaluate(traj, indices)
            idx += 1
        return rho

    def evaluate_rule(self, traj, rule_id, graph_idx=0, indices=None):
        # Evaluate the result of a rule on the trajectory
        priority_graph = self.priority_graphs[graph_idx]
        rule = priority_graph.nodes[rule_id]["rule"]
        rho = 1
        if priority_graph.nodes[rule_id]["active"]:
            if self.verbosity >= 2:
                print("Evaluating rule", rule_id)
            rho = rule.evaluate(traj, indices)
        return rho

    def evaluate(self, simulation):
        # Use the segment function to get different segments
        segments = self.segment_function(simulation)

        # Use evaluate_segment to evaluate each segment
        if self.single_graph:
            if self.verbosity >= 1:
                print("Dynamic Rulebook Rhos:")
            for i in range(len(segments)):
                rho = self.evaluate_segment(simulation, 0, segments[i])
                if self.verbosity >= 1:
                    for r in rho:
                        print(r, end=" ")
                    print()
            rho = self.evaluate_segment(
                simulation, 0, np.arange(0, len(simulation.result.trajectory))
            )
            return np.array([rho])
        else:
            assert len(segments) == len(
                self.priority_graphs
            ), "Number of segments does not match number of graphs"
            rhos = []
            for i in range(len(segments)):
                rho = self.evaluate_segment(simulation, i, segments[i])
                rhos.append(rho)
            if self.verbosity >= 1:
                print("Dynamic Rulebook Rhos:")
                for rho in rhos:
                    for r in rho:
                        print(r, end=" ")
                    print()
            return np.array(rhos, dtype=object)

    def update_graph(self):
        pass


class rule(specification_monitor):
    def __init__(self, node_id, spec):
        self.node_id = node_id
        super().__init__(spec)

    def evaluate(self, traj, indices=None):
        return self.specification(traj, indices)
