import pandas as pd
from verifai.compositional_analysis import CompositionalAnalysisEngine, ScenarioBase


if __name__ == "__main__":
    logs = {
        "S": "storage/traces/S/traces.csv",
        "X": "storage/traces/X/traces.csv",
        "O": "storage/traces/O/traces.csv",
        "C": "storage/traces/C/traces.csv",
        "SX": "storage/traces/SX/traces.csv",
        "SO": "storage/traces/SO/traces.csv",
        "SC": "storage/traces/SC/traces.csv",
        "SXS": "storage/traces/SXS/traces.csv",
        "SOS": "storage/traces/SOS/traces.csv",
        "SCS": "storage/traces/SCS/traces.csv",
    }
    scenario_base = ScenarioBase(logs)

    print("SMC")
    for s in logs:
        print(f"{s}: rho = {scenario_base.get_success_rate(s):.4f} ± {scenario_base.get_success_rate_uncertainty(s):.4f}")

    engine = CompositionalAnalysisEngine(scenario_base)

    pd.set_option('display.max_rows', None)  # Display all rows
    pd.set_option('display.max_columns', None) # Display all columns
    pd.set_option('display.width', 1000) # Ensure enough width to prevent wrapping

    print("Compositional SMC")
    for s in logs:
        rho, uncertainty = engine.check(
            s,
            features=["x", "y", "heading", "speed"],
            norm_feat_idx=[0, 1],
        )
        print(f"Estimated {s}: rho = {rho:.4f} ± {uncertainty:.4f}")
        cex = engine.falsify(
            s,
            features=["x", "y", "heading", "speed"],
            norm_feat_idx=[0, 1],
            align_feat_idx=[0, 1],
        )
        print(f"Counterexample = {cex}")

