from abc import ABC
import networkx as nx
import mtl

class specification_monitor(ABC):
    def __init__(self, specification):
        self.specification = specification

    def evaluate(self, traj):
        return self.specification(traj)


class mtl_specification(specification_monitor):
    def __init__(self, specification):
        mtl_specs = [mtl.parse(spec) for spec in specification]
        mtl_spec = mtl_specs[0]
        if len(mtl_specs) > 1:
            for spec in mtl_specs[1:]:
                mtl_spec = (mtl_spec & spec)
        super().__init__(mtl_spec)

    def evaluate(self, traj):
        return self.specification(traj)

class multi_objective_monitor(specification_monitor):
    def __init__(self, specification, priority_graph=None):
        super().__init__(specification)
        if priority_graph is None:
            self.graph = nx.DiGraph()
            self.graph.add_nodes_from(range(self.num_objectives))
        else:
            self.graph = priority_graph

def generate_monitor_and_sampler(objective_function, priority_graph):
    return multi_objective_monitor(objective_function, priority_graph), \
        None # need to instantiate sampler correctly here