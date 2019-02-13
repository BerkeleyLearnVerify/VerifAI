class webots_task():
    def __init__(self, N_SIM_STEPS, supervisor):
        self.N_SIM_STEPS = N_SIM_STEPS
        self.supervisor = supervisor

    def use_sample(self, sample):
        print("Define in child class")
        pass

    def run_task(self, sample):
        print("Define in child class")
        pass

    def close(self):
        self.supervisor.simulationReset()