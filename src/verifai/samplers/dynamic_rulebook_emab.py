import numpy as np
import networkx as nx

from verifai.samplers.domain_sampler import BoxSampler, DomainSampler
from verifai.samplers.multi_objective import MultiObjectiveSampler


class DynamicRulebookExtendedMultiArmedBanditSampler(DomainSampler):
    verbosity = 1

    def __init__(self, domain, demab_params):
        super().__init__(domain)
        rb = getattr(demab_params, "rulebook", None)
        if rb is None:
            raise ValueError("demab_params.rulebook must be set to a Rulebook instance")
        self.alpha = demab_params.alpha
        self.thres = demab_params.thres
        self.cont_buckets = demab_params.cont.buckets
        self.cont_dist = demab_params.cont.dist
        self.cont_ce = lambda domain, priority_graph: ContinuousDynamicEMABSampler(
            domain=domain,
            buckets=self.cont_buckets,
            dist=self.cont_dist,
            alpha=self.alpha,
            thres=self.thres,
            exploration_ratio=rb.exploration_ratio,
            priority_graph=priority_graph,
            rulebook_instance=rb,
        )
        self.split_samplers = {}
        for id, priority_graph in rb.priority_graphs.items():
            self.split_samplers[id] = self.cont_ce(domain, priority_graph)
        if not sorted(list(self.split_samplers.keys())) == list(
            range(len(rb.priority_graphs))
        ):
            raise ValueError("Priority graph IDs should be in order and start from 0")
        self.num_segs = len(self.split_samplers)
        self.sampler_idx = 0
        self.using_sampler = rb.using_sampler  # -1: round-robin
        assert self.using_sampler < self.num_segs

    def getSample(self):
        if self.using_sampler == -1:
            # Sample from each segment in a round-robin fashion
            idx = self.sampler_idx % self.num_segs
        else:
            idx = self.using_sampler
        return self.split_samplers[idx].getSample()

    def update(self, sample, info, rhos):
        # Update each sampler based on the corresponding segment
        try:
            iter(rhos)
        except Exception as e:
            for i in range(len(self.split_samplers)):
                self.split_samplers[i].update(sample, info, rhos)
            return
        if self.using_sampler == -1:
            if self.verbosity >= 2:
                print(
                    "(dynamic_emab.py) Getting feedback from segment",
                    self.sampler_idx % self.num_segs,
                )
            for i in range(len(rhos)):
                self.split_samplers[i].update(sample, info, rhos[i])
        else:
            if self.verbosity >= 2:
                print(
                    "(dynamic_emab.py) Getting feedback from segment",
                    self.using_sampler,
                )
            self.split_samplers[self.using_sampler].update(
                sample, info, rhos[self.using_sampler]
            )
        self.sampler_idx += 1


class ContinuousDynamicEMABSampler(BoxSampler, MultiObjectiveSampler):
    verbosity = 1

    def __init__(
        self,
        domain,
        alpha,
        thres,
        buckets=10,
        dist=None,
        restart_every=100,
        exploration_ratio=2.0,
        priority_graph=None,
        rulebook_instance=None,
    ):
        super().__init__(domain)
        if isinstance(buckets, int):
            buckets = np.ones(self.dimension) * buckets
        elif len(buckets) > 1:
            assert len(buckets) == self.dimension
        else:
            buckets = np.ones(self.dimension) * buckets[0]
        if dist is not None:
            assert len(dist) == len(buckets)
        if dist is None:
            dist = np.array([np.ones(int(b)) / b for b in buckets])
        self.buckets = buckets  # 1*d, each element specifies the number of buckets in that dimension
        self.dist = dist  # N*d, ???
        self.alpha = alpha
        self.thres = thres
        self.current_sample = None
        self.counts = np.array(
            [np.ones(int(b)) for b in buckets]
        )  # N*d, T (visit times)
        self.errors = np.array(
            [np.zeros(int(b)) for b in buckets]
        )  # N*d, total times resulting in maximal counterexample
        self.t = 1  # time, used in Q
        self.counterexamples = dict()
        self.is_multi = True  # False
        self.invalid = np.array([np.zeros(int(b)) for b in buckets])  # N*d, ???
        self.monitor = None
        self.rho_values = []
        self.restart_every = restart_every
        self.exploration_ratio = exploration_ratio
        self.rulebook_instance = rulebook_instance
        if priority_graph is not None:
            self.set_graph(priority_graph)
            self.compute_error_weight()

    def getVector(self):
        proportions = self.errors / self.counts
        Q = proportions + np.sqrt(self.exploration_ratio / self.counts * np.log(self.t))
        # choose the bucket with the highest "goodness" value, breaking ties randomly.
        bucket_samples = np.array(
            [
                np.random.choice(np.flatnonzero(np.isclose(Q[i], Q[i].max())))
                for i in range(len(self.buckets))
            ]
        )
        self.current_sample = bucket_samples
        ret = tuple(
            np.random.uniform(bs, bs + 1.0) / b
            for b, bs in zip(self.buckets, bucket_samples)
        )  # uniform randomly sample from the range of the bucket
        return ret, bucket_samples

    def updateVector(self, vector, info, rho):
        assert rho is not None
        # "random restarts" to generate a new topological sort of the priority graph
        # every restart_every samples.
        if self.is_multi:
            if (
                self.monitor is not None
                and self.monitor.linearize
                and self.t % self.restart_every == 0
            ):
                self.monitor._linearize()
            self.update_dist_from_multi(vector, info, rho)
            return
        self.t += 1
        for i, b in enumerate(info):
            self.counts[i][b] += 1.0
            if rho < self.thres:
                self.errors[i][b] += 1.0

    def is_better_counterexample(self, ce1, ce2):
        if ce2 is None:
            return True
        return self._compute_error_value(ce1) > self._compute_error_value(ce2)

    def _get_total_counterexamples(self):
        return sum(self.counterexamples.values())

    def _update_counterexample(
        self, ce, to_delete=False
    ):  # update counterexamples, may or may not delete non-maximal counterexamples
        if ce in self.counterexamples:
            return True
        if to_delete:
            to_remove = set()
            if len(self.counterexamples) > 0:
                for other_ce in self.counterexamples:
                    if self.is_better_counterexample(other_ce, ce):
                        return False
            for other_ce in self.counterexamples:
                if self.is_better_counterexample(ce, other_ce):
                    to_remove.add(other_ce)
            for other_ce in to_remove:
                del self.counterexamples[other_ce]
        self.counterexamples[ce] = np.array([np.zeros(int(b)) for b in self.buckets])
        return True

    def update_dist_from_multi(self, sample, info, rho):
        try:
            iter(rho)
        except:
            for i, b in enumerate(info):
                self.invalid[i][b] += 1.0
            return
        if len(rho) != self.num_properties:
            for i, b in enumerate(info):
                self.invalid[i][b] += 1.0
            return
        counter_ex_dict = {}
        idx = 0
        for node in sorted(self.priority_graph.nodes):
            counter_ex_dict[node] = rho[idx] < self.thres[idx]
            idx += 1
        counter_ex = tuple(rho[i] < self.thres[i] for i in range(len(rho)))
        error_value = self._compute_error_value(counter_ex_dict)
        if (
            self.rulebook_instance is not None
            and self.rulebook_instance.using_continuous
        ):
            error_value = self._compute_error_value_continuous(rho)
            print("(dynamic_emab.py) error_value =", error_value)
        self._update_counterexample(counter_ex)
        for i, b in enumerate(info):
            self.counts[i][b] += self.sum_error_weight
            self.counterexamples[counter_ex][i][b] += error_value
        self.errors = self._get_total_counterexamples()
        self.t += 1
        if self.verbosity >= 2:
            print("counterexamples =", self.counterexamples)
        if self.verbosity >= 2:
            for ce in self.counterexamples:
                if self._compute_error_value(ce) > 0:
                    print(
                        "counterexamples =",
                        ce,
                        ", times =",
                        int(
                            np.sum(self.counterexamples[ce], axis=1)[0]
                            / self._compute_error_value(ce)
                        ),
                    )
        if self.verbosity >= 2:
            proportions = self.errors / self.counts
            print("self.errors[0] =", self.errors[0])
            print("self.counts[0] =", self.counts[0])
            Q = proportions + np.sqrt(
                self.exploration_ratio / self.counts * np.log(self.t)
            )
            print(
                "Q[0] =",
                Q[0],
                "\nfirst_term[0] =",
                proportions[0],
                "\nsecond_term[0] =",
                np.sqrt(self.exploration_ratio / self.counts * np.log(self.t))[0],
                "\nratio[0] =",
                proportions[0]
                / (
                    proportions
                    + np.sqrt(self.exploration_ratio / self.counts * np.log(self.t))
                )[0],
            )

    def _compute_error_value(self, counter_ex):
        error_value = 0
        for key in counter_ex:
            if counter_ex[key]:
                error_value += 2 ** (self.error_weight[key])
        return error_value

    def _compute_error_value_continuous(self, rho):
        error_value = 0
        for i in range(len(rho)):
            error_value += 2 ** (self.error_weight[i]) * -1 * rho[i]
        return error_value

    def compute_error_weight(self):
        level = {}
        for node in nx.topological_sort(self.priority_graph):
            if self.priority_graph.in_degree(node) == 0:
                level[node] = 0
            else:
                level[node] = (
                    max([level[p] for p in self.priority_graph.predecessors(node)]) + 1
                )

        ranking_map = {}
        ranking_count = {}
        for rank in sorted(level.values()):
            if rank not in ranking_count:
                ranking_count[rank] = 1
            else:
                ranking_count[rank] += 1
        count = 0
        for key, value in reversed(ranking_count.items()):
            ranking_map[key] = count
            count += value

        self.error_weight = {}  # node_id -> weight
        self.sum_error_weight = 0
        for node in level:
            self.error_weight[node] = ranking_map[level[node]]
            self.sum_error_weight += 2 ** self.error_weight[node]
        for key, value in sorted(self.error_weight.items()):
            if self.verbosity >= 2:
                print(f"Node {key}: {value}")
