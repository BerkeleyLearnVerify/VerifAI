import argparse
import math
import multiprocessing as mp
import os
import shutil
import time

from verifai.compositional_analysis import ScenarioBase, CompositionalAnalysisEngine
from utils import generate_traces


def compute_hoeffding_samples(confidence_level, error_bound):
    """
    Compute the number of samples needed using Hoeffding's inequality.
    
    Hoeffding's inequality: P(|rho_hat - rho| >= epsilon) <= 2 * exp(-2 * n * epsilon^2)
    
    Setting 2 * exp(-2 * n * epsilon^2) = 1 - confidence_level (delta)
    Solving for n: n = ln(2/delta) / (2 * epsilon^2)
    
    Args:
        confidence_level: Desired confidence level (e.g., 0.95 for 95%)
        error_bound: Maximum error epsilon (e.g., 0.01 for 1%)
    
    Returns:
        Number of samples needed
    """
    delta = 1 - confidence_level
    n = math.log(2 / delta) / (2 * error_bound ** 2)
    return math.ceil(n)


def _worker_generate_traces(save_dir, scenario, n):
    print(f"[PID={os.getpid()}] Starting scenario {scenario}")
    # If n is None or inf, use a very large number that generate_traces can handle
    if n is None or n == float('inf'):
        traces_to_generate = 10**9  # 1 billion (effectively infinite for practical purposes)
    else:
        traces_to_generate = n
    generate_traces(
        n=traces_to_generate,
        save_dir=save_dir,
        scenario=scenario,
    )
    print(f"[PID={os.getpid()}] Finished scenario {scenario}")


def get_n_traces_from_csv(csv_path):
    if os.path.exists(csv_path):
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            if len(lines) <= 1:
                return 0
            else:
                trace_ids = set()
                for line in lines[1:]:
                    parts = line.split(',')
                    if parts:
                        trace_ids.add(parts[0])
                return len(trace_ids)
    else:
        return 0


def generate_traces_parallel(n, save_dir, scenarios, time_budget):
    """
    Generate traces in parallel using multiprocessing with HARD STOP.
    Terminates all processes when time budget is reached, discarding only the current partial trace.
    Completed traces are kept.
    """
    # Clear old trace directories
    for s in scenarios:
        scenario_dir = os.path.join(save_dir, s)
        if os.path.exists(scenario_dir):
            shutil.rmtree(scenario_dir)
    
    print("=== Generating Traces (Parallel - HARD STOP) ===")
    
    # Launch all processes
    processes = []
    start_time = time.monotonic()
    
    for s in scenarios:
        print(f"Launching scenario {s}")
        p = mp.Process(
            target=_worker_generate_traces,
            args=(save_dir, s, n)
        )
        p.start()
        processes.append((s, p))
    
    # Monitor time budget and terminate if exceeded
    trace_counts_before_termination = {}
    while True:
        elapsed = time.monotonic() - start_time
        
        # Check if time budget exceeded (skip check if time_budget is inf)
        if time_budget != float('inf') and elapsed >= time_budget:
            print(f"\n[HARD STOP] Time budget ({time_budget}s) reached at {elapsed:.2f}s")
            
            # Record trace counts RIGHT BEFORE termination
            for s in scenarios:
                csv_path = os.path.join(save_dir, s, "traces.csv")
                trace_counts_before_termination[s] = get_n_traces_from_csv(csv_path)
            
            print("Terminating all running processes...")
            
            for scenario_name, proc in processes:
                if proc.is_alive():
                    print(f"Terminating scenario {scenario_name} (PID={proc.pid})")
                    proc.terminate()
                    proc.join(timeout=5)  # Wait up to 5 seconds for graceful termination
                    if proc.is_alive():
                        print(f"Force killing scenario {scenario_name}")
                        proc.kill()
                        proc.join()
            break
        
        # Check if all processes finished naturally
        all_done = all(not proc.is_alive() for _, proc in processes)
        if all_done:
            print(f"All processes finished naturally (elapsed: {elapsed:.2f}s)")
            break
        
        time.sleep(0.1)  # Check every 100ms
    
    # Build logs dict for scenarios with valid traces
    logs = {}
    for s, proc in processes:
        csv_path = os.path.join(save_dir, s, "traces.csv")
        trace_count = get_n_traces_from_csv(csv_path)

        if os.path.exists(csv_path):
            if proc.exitcode != 0 and s in trace_counts_before_termination:
                expected_count = trace_counts_before_termination[s]
                if trace_count > expected_count:
                    # There's a partial trace - keep only the completed traces
                    print(f"[INFO] Scenario {s}: Removing partial episode (had {trace_count} episodes, keeping {expected_count})")
                    
                    # Keep only rows with trace_id < expected_count
                    with open(csv_path, 'w') as f:
                        f.write(lines[0])  # Write header
                        for line in lines[1:]:
                            parts = line.split(',')
                            if parts:
                                trace_id = int(parts[0])
                                if trace_id < expected_count:
                                    f.write(line)
                
                # Only add to logs if there are any complete traces
                if expected_count > 0:
                    logs[s] = csv_path
                    print(f"[INFO] Scenario {s} has {expected_count} completed episodes.")
                else:
                    print(f"[INFO] Scenario {s} had no completed episodes.")

            else:
                logs[s] = csv_path
                print(f"[INFO] Scenario {s} completed successfully with {trace_count} episodes.")

        else:
            print(f"[INFO] Scenario {s} produced no traces.")
    
    if not logs:
        print("No traces generated.")
    
    return logs


def run_monolithic_smc(scenario_base):
    """
    Run monolithic SMC analysis on generated traces.
    """
    if not scenario_base.logbase:
        print("No traces to analyze.")

    results = {}
    
    print("\n=== Monolithic SMC Results ===")
    for s in scenario_base.logbase:
        rho = scenario_base.get_success_prob(s)
        unc = scenario_base.get_success_prob_uncertainty(s)
        print(f"{s}: rho = {rho:.4f} ± {unc:.4f}")
        results[s] = {"rho": rho, "uncertainty": unc}
    
    return results


def run_SMC_compositional(scenarios, time_budget, scenario_base):
    print("\n=== Running Compositional SMC ===")
    start_time = time.monotonic()
    results = {}

    engine = CompositionalAnalysisEngine(scenario_base)

    for s in scenarios:
        elapsed = time.monotonic() - start_time
        remaining_time = time_budget - elapsed
        if time_budget != float('inf') and remaining_time <= 0:
            print(f"Time budget exhausted before scenario {s}")
            break

        rho, uncertainty = engine.check(
            s,
            features=["x", "y", "heading", "speed"],
            center_feat_idx=[0, 1],
        )

        print(f"Estimated {s}: rho = {rho:.4f} ± {uncertainty:.4f}")

        results[s] = {"rho": rho, "uncertainty": uncertainty}

    return results


def testScenario(input_scenario, isCompositional, time_budget, n, save_dir, confidence_level=None, error_bound=None, reuse_traces=False):
    """
    Test scenario with hard time budget enforcement.
    Terminates all processes when time budget is reached.
    
    Args:
        confidence_level: Confidence level for ground truth (e.g., 0.95)
        error_bound: Error bound for ground truth (e.g., 0.01)
        reuse_traces: If True, use existing traces from save_dir without generating new ones
    """
    
    # monolithic trace generation
    if not isCompositional:
        print("Running MONOLITHIC SMC")
        scenarios = [input_scenario]
        
        if not reuse_traces:
            logs = generate_traces_parallel(n=n, save_dir=save_dir, scenarios=scenarios, time_budget=time_budget)
        else:
            # Build logs from existing traces
            logs = {}
            for s in scenarios:
                csv_path = os.path.join(save_dir, s, "traces.csv")
                if os.path.exists(csv_path):
                    logs[s] = csv_path
                    print(f"[INFO] Using existing traces for scenario {s}")
                else:
                    print(f"[ERROR] No existing traces found for scenario {s} at {csv_path}")
        
        scenario_base = ScenarioBase(logs, delta=1-confidence_level)
        run_monolithic_smc(scenario_base)
        
    # compositional trace generation
    else:
        print("Running COMPOSITIONAL SMC on primitive cases (what compositional will use)")
        scenarios_set = set(input_scenario)
        scenarios = list(scenarios_set)
        
        if not reuse_traces:
            logs = generate_traces_parallel(n=n, save_dir=save_dir, scenarios=scenarios, time_budget=time_budget)
        else:
            # Build logs from existing traces
            logs = {}
            for s in scenarios:
                csv_path = os.path.join(save_dir, s, "traces.csv")
                if os.path.exists(csv_path):
                    logs[s] = csv_path
                    print(f"[INFO] Using existing traces for scenario {s}")
                else:
                    print(f"[ERROR] No existing traces found for scenario {s} at {csv_path}")
        
        scenario_base = ScenarioBase(logs, delta=1-confidence_level)
        
        # compositional rho
        run_SMC_compositional(scenarios=[input_scenario], time_budget=time_budget, scenario_base=scenario_base)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run SMC tests with compositional or monolithic approaches")
    parser.add_argument("--scenario", type=str, default="SXC", help="Input scenario string (default: SXC)")
    parser.add_argument("--compositional", action="store_true", help="Use compositional approach (default: False)")
    parser.add_argument("--time_budget", type=int, default=None, help="Time budget in seconds (default: None)")
    parser.add_argument("--save_dir", type=str, default="storage/traces", help="Directory to save traces (default: storage/traces)")
    parser.add_argument("--confidence_level", type=float, required=True, help="Confidence level for ground truth (required)")
    parser.add_argument("--error_bound", type=float, default=None, help="Error bound (epsilon) for ground truth (default: None)")
    parser.add_argument("--reuse_traces", action="store_true", help="Use existing traces from save_dir without generating new ones (default: False)")

    args = parser.parse_args()

    mp.set_start_method("spawn")

    # Validate arguments
    if args.error_bound is None and args.time_budget is None:
        raise ValueError("You must provide either --error_bound or --time_budget.")

    n = None
    time_budget = float('inf')
    if args.error_bound is not None:
        n = compute_hoeffding_samples(args.confidence_level, args.error_bound)
    elif args.time_budget is not None:
        time_budget = args.time_budget

    testScenario(
        input_scenario=args.scenario,
        isCompositional=args.compositional,
        time_budget=time_budget,
        n=n,
        save_dir=args.save_dir,
        confidence_level=args.confidence_level,
        error_bound=args.error_bound,
        reuse_traces=args.reuse_traces
    )

