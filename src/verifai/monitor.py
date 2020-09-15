from abc import ABC
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
