import pandas as pd
from verifai.compositional_analysis import CompositionalAnalysisEngine, ScenarioBase


if __name__ == "__main__":
    logs = {
        "S": "storage/example/S/traces.csv",
        "X": "storage/example/X/traces.csv",
        "SX": "storage/example/SX/traces.csv",
    }
    scenario_base = ScenarioBase(logs, delta=0.01)

    print("SMC")
    for s in logs:
        print(f"{s}: rho = {scenario_base.get_success_prob(s):.4f} ± {scenario_base.get_success_prob_uncertainty(s):.4f}")

    engine = CompositionalAnalysisEngine(scenario_base)

    pd.set_option('display.max_rows', None)  # Display all rows
    pd.set_option('display.max_columns', None) # Display all columns
    pd.set_option('display.width', 1000) # Ensure enough width to prevent wrapping

    for s in logs:
        print("\n" + "="*60)
        print(f"Scenario: {s}")
        print("-"*60)
        print("SMC:")
        print(f"  Estimated success probability (rho): {scenario_base.get_success_prob(s):.4f}")
        print(f"  Uncertainty: ±{scenario_base.get_success_prob_uncertainty(s):.4f}")
        print()
        print("Compositional SMC:")
        rho, uncertainty = engine.check(
            s,
            features=["x", "y", "heading", "speed"],
            center_feat_idx=[0, 1],
        )
        print(f"  Estimated success probability (rho): {rho:.4f}")
        print(f"  Uncertainty: ±{uncertainty:.4f}")
        print()
        print("Compositional Falsification (Experimental):")
        cex = engine.falsify(
            s,
            features=["x", "y", "heading", "speed"],
            center_feat_idx=[0, 1],
            align_feat_idx=[0, 1],
        )
        print(f"  Counterexample: {cex}")
        print("="*60)

