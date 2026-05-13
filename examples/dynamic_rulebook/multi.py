"""
Framework for experimentation of multi-objective and dynamic falsification.

Author: Kai-Chun Chang. Based on Kesav Viswanadha's code.
"""

import time
import os
import glob
import traceback
import argparse
import importlib
import random

import networkx as nx
import pandas as pd
import numpy as np
from dotmap import DotMap

from verifai import (
    Falsifier, ParallelFalsifier, Monitor, Rulebook, ScenicSampler
)


def announce(message):
    lines = message.split("\n")
    size = max([len(p) for p in lines]) + 4

    def pad(line):
        ret = "* " + line
        ret += " " * (size - len(ret) - 1) + "*"
        return ret

    lines = list(map(pad, lines))
    m = "\n".join(lines)
    border = "*" * size
    print(border)
    print(m)
    print(border)


"""
Runs all experiments in a directory.
"""


def run_experiments(
    path,
    rulebook=None,
    parallel=False,
    model=None,
    sampler_type=None,
    headless=False,
    num_workers=5,
    output_dir="outputs",
    experiment_name=None,
    max_time=None,
    n_iters=None,
    max_steps=300,
):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    paths = []
    if os.path.isdir(path):
        paths = glob.glob(f"{path}/**/*.scenic", recursive=True)
    else:
        paths = [path]
    for p in paths:
        falsifier = run_experiment(
            p,
            rulebook=rulebook,
            parallel=parallel,
            model=model,
            sampler_type=sampler_type,
            headless=headless,
            num_workers=num_workers,
            max_time=max_time,
            n_iters=n_iters,
            max_steps=max_steps,
        )
        df = pd.concat([falsifier.error_table.table, falsifier.safe_table.table])
        if experiment_name is not None:
            outfile = experiment_name
        else:
            root, _ = os.path.splitext(p)
            outfile = root.split("/")[-1]
            if parallel:
                outfile += "_parallel"
            if model:
                outfile += f"_{model}"
            if sampler_type:
                outfile += f"_{sampler_type}"
        outfile += ".csv"
        outpath = os.path.join(output_dir, outfile)
        print(f"(multi.py) Saving output to {outpath}")
        df.to_csv(outpath)


"""
Runs a single falsification experiment.
"""


def run_experiment(
    scenic_path,
    rulebook=None,
    parallel=False,
    model=None,
    sampler_type=None,
    headless=False,
    num_workers=5,
    max_time=None,
    n_iters=5,
    max_steps=300,
):
    # Construct rulebook
    rb = rulebook

    # Construct sampler (scenic_sampler.py)
    print(f"(multi.py) Running Scenic script {scenic_path}")
    params = {"verifaiSamplerType": sampler_type} if sampler_type else {}
    params["render"] = not headless
    params["seed"] = 0
    params["use2DMap"] = True
    if rb is not None:
        params["verifaiSamplerParams"] = DotMap(rulebook=rb)
    sampler = ScenicSampler.fromScenario(
        scenic_path, maxIterations=40000, params=params, model=model
    )
    s_type = sampler.scenario.params.get("verifaiSamplerType", None)

    # Construct falsifier (falsifier.py)
    falsifier_params = DotMap(
        n_iters=n_iters,
        save_error_table=True,
        save_safe_table=True,
        max_time=max_time,
        verbosity=1,
    )
    server_options = DotMap(
        maxSteps=max_steps,
        verbosity=1,
        scenic_path=scenic_path,
        scenario_params=params,
        scenario_model=model,
        num_workers=num_workers,
    )
    falsifier_class = ParallelFalsifier if parallel else Falsifier
    falsifier = falsifier_class(
        monitor=rb,  ## modified
        sampler_type=s_type,
        sampler=sampler,
        falsifier_params=falsifier_params,
        server_options=server_options,
    )
    print(f"(multi.py) Sampler type: {falsifier.sampler_type}")

    # Run falsification
    t0 = time.monotonic()
    print("(multi.py) Running falsifier...")
    falsifier.run_falsifier()
    t = time.monotonic() - t0
    print()
    print(
        f"(multi.py) Generated {len(falsifier.samples)} samples in {t} seconds with {falsifier.num_workers} workers"
    )
    print(f"(multi.py) Number of counterexamples: {len(falsifier.error_table.table)}")
    if not parallel:
        print(f"(multi.py) Sampling time: {falsifier.total_sample_time}")
        print(f"(multi.py) Simulation time: {falsifier.total_simulate_time}")
    print(f"(multi.py) Confidence interval: {falsifier.get_confidence_interval()}")
    return falsifier


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenic-path",
        "-sp",
        type=str,
        default="multi_inter_left/multi_inter_left.scenic",
        help="Path to Scenic script",
    )
    parser.add_argument(
        "--graph-path", "-gp", type=str, default=None, help="Path to graph file"
    )
    parser.add_argument(
        "--rule-path", "-rp", type=str, default=None, help="Path to rule file"
    )
    parser.add_argument(
        "--segment-func-path",
        "-sfp",
        type=str,
        default=None,
        help="Path to segment function file",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default=None,
        help="Directory to save output trajectories",
    )
    parser.add_argument(
        "--output-csv-dir",
        "-co",
        type=str,
        default=None,
        help="Directory to save output error tables (csv files)",
    )
    parser.add_argument("--parallel", action="store_true")
    parser.add_argument(
        "--num-workers", type=int, default=5, help="Number of parallel workers"
    )
    parser.add_argument(
        "--sampler-type", "-s", type=str, default=None, help="verifaiSamplerType to use"
    )
    parser.add_argument(
        "--experiment-name",
        "-e",
        type=str,
        default=None,
        help="verifaiSamplerType to use",
    )
    parser.add_argument(
        "--model", "-m", type=str, default="scenic.simulators.newtonian.driving_model"
    )
    parser.add_argument("--headless", action="store_true")
    parser.add_argument(
        "--n-iters", "-n", type=int, default=None, help="Number of simulations to run"
    )
    parser.add_argument(
        "--max-time",
        type=int,
        default=None,
        help="Maximum amount of time to run simulations",
    )
    parser.add_argument(
        "--single-graph", action="store_true", help="Only a unified priority graph"
    )
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    parser.add_argument(
        "--using-sampler", type=int, default=-1, help="Assigning sampler to use"
    )
    parser.add_argument(
        "--max-simulation-steps",
        type=int,
        default=300,
        help="Maximum number of simulation steps",
    )
    parser.add_argument(
        "--exploration-ratio", type=float, default=2.0, help="Exploration ratio"
    )
    args = parser.parse_args()
    if args.n_iters is None and args.max_time is None:
        raise ValueError("At least one of --n-iters or --max-time must be set")

    random.seed(args.seed)
    np.random.seed(args.seed)

    rb = Rulebook(
        args.graph_path,
        args.rule_path,
        args.segment_func_path,
        save_path=args.output_dir,
        single_graph=args.single_graph,
        using_sampler=args.using_sampler,
        exploration_ratio=args.exploration_ratio,
    )
    run_experiments(
        args.scenic_path,
        rulebook=rb,
        parallel=args.parallel,
        model=args.model,
        sampler_type=args.sampler_type,
        headless=args.headless,
        num_workers=args.num_workers,
        output_dir=args.output_csv_dir,
        experiment_name=args.experiment_name,
        max_time=args.max_time,
        n_iters=args.n_iters,
        max_steps=args.max_simulation_steps,
    )
