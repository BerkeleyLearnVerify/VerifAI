from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Sequence, Union

import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


@dataclass
class ScenarioStats:
    rho: float
    uncertainty: float


class ScenarioBase:
    """
    Handles loading and basic statistics of scenario trace data.
    Computes per-scenario success rates and Hoeffding uncertainty.
    """

    REQUIRED_COLUMNS = {"trace_id", "step", "label"}

    def __init__(self, logbase: Dict[str, str], delta: float = 0.05):
        """
        Args:
            logbase: Dict mapping scenario names to CSV file paths
            delta: Confidence level for Hoeffding bound (default 0.05 → 95% CI)
        """
        self.logbase = logbase
        self.delta = delta
        self.data: Dict[str, pd.DataFrame] = {}

        # Load CSVs
        for name, path in logbase.items():
            path_obj = Path(path)
            if not path_obj.exists():
                raise FileNotFoundError(f"CSV file for scenario '{name}' not found: {path}")
            df = pd.read_csv(path)
            missing = self.REQUIRED_COLUMNS - set(df.columns)
            if missing:
                raise ValueError(f"CSV for scenario '{name}' missing columns: {missing}")
            df["trace_id"] = df["trace_id"].astype(str)
            self.data[name] = df

        self.success_stats: Dict[str, ScenarioStats] = {}
        self._compute_success_stats()

    def _compute_success_stats(self):
        for name, df in self.data.items():
            last_steps = df.sort_values("step").groupby("trace_id").tail(1)
            labels = last_steps["label"].astype(float).to_numpy()
            rho = labels.mean() if len(labels) > 0 else 0.0
            epsilon = np.sqrt(np.log(2 / self.delta) / (2 * len(labels))) if len(labels) > 0 else 0.0
            self.success_stats[name] = ScenarioStats(rho=rho, uncertainty=epsilon)

    def get_success_rate(self, scenario: str) -> float:
        return self.success_stats[scenario].rho

    def get_success_rate_uncertainty(self, scenario: str) -> float:
        return self.success_stats[scenario].uncertainty


class CompositionalAnalysisEngine:
    """
    Computes importance-sampled success probabilities across sequential scenarios
    using Gaussian KDE and Hoeffding uncertainty propagation.
    """

    def __init__(self, scenario_base: ScenarioBase):
        self.scenario_base = scenario_base

    @staticmethod
    def _normalize_features(features: np.ndarray) -> np.ndarray:
        """Standardize features along each column (mean=0, std=1)."""
        mean = np.mean(features, axis=0)
        std = np.std(features, axis=0)
        std[std == 0] = 1.0  # Avoid division by zero
        return (features - mean) / std

    def check(
        self,
        scenario: List[str],
        features: Optional[List[str]] = None,
        norm_feat_idx: Optional[List[int]] = None,
    ) -> Tuple[float, float]:
        """
        Computes importance-sampled success probability and propagated uncertainty.

        Args:
            scenario: Ordered list of scenario names
            features: Optional list of features to include in KDE
            norm_feat_idx: Optional indices of features to normalize

        Returns:
            Tuple of (rho_estimate, uncertainty)
        """
        if len(scenario) == 0:
            raise ValueError("Scenario list must contain at least one scenario.")

        rho = 1.0
        rho_bounds = []

        n = len(scenario)
        if n == 1:
            result = self.scenario_base.success_stats[scenario]
            return result.rho, result.uncertainty

        delta = self.scenario_base.delta
        per_step_delta = delta / n  # union bound

        for i in range(len(scenario) - 1):
            s_name, t_name = scenario[i], scenario[i+1]
            df_s, df_t = self.scenario_base.data[s_name], self.scenario_base.data[t_name]

            # Select successful endpoints
            s_last = df_s.sort_values("step").groupby("trace_id").tail(1)
            s_last = s_last[s_last["label"] == True]
            t_first = df_t.sort_values("step").groupby("trace_id").head(1)
            t_last = df_t.sort_values("step").groupby("trace_id").tail(1)

            # KDE features
            if features:
                s_last_features = s_last[features].to_numpy()
                t_first_features = t_first[features].to_numpy()
                if s_last_features.shape[0] < 2 or t_first_features.shape[0] < 2:
                    return 0.0, 0.0
                if norm_feat_idx:
                    for j in norm_feat_idx:
                        s_last_features[:, j] = self._normalize_features(s_last_features[:, j].reshape(-1, 1)).flatten()
                        t_first_features[:, j] = self._normalize_features(t_first_features[:, j].reshape(-1, 1)).flatten()
            else:
                raise ValueError("Feature list must be provided for KDE.")

            s_last_features, t_first_features = s_last_features.T, t_first_features.T
            kde_s_last = gaussian_kde(s_last_features)
            kde_t_first = gaussian_kde(t_first_features)
            p_vals = kde_s_last(t_first_features)
            q_vals = kde_t_first(t_first_features)
            weights = np.nan_to_num(p_vals / q_vals, nan=0.0, posinf=0.0, neginf=0.0)

            labels_t_last = t_last["label"].astype(float).to_numpy()
            min_len = min(len(weights), len(labels_t_last))
            weights = weights[:min_len]
            labels_t_last = labels_t_last[:min_len]

            rho_step = np.sum(weights * labels_t_last) / np.sum(weights) if np.sum(weights) > 0 else 0.0
            rho *= rho_step

            # Hoeffding absolute bound with effective samples
            N_eff = np.sum(weights)**2 / np.sum(weights**2) if np.sum(weights**2) > 0 else 1.0
            epsilon_i = np.sqrt(np.log(2 / per_step_delta) / (2 * N_eff))
            rho_bounds.append(epsilon_i)

        # Provable multiplicative error
        prod_factor = np.prod([1 + eps / max(rho_step, 1e-12) for eps in rho_bounds])
        uncertainty = rho * (prod_factor - 1)

        return rho, uncertainty

    def falsify(
        self,
        scenario: Union[str, Sequence[str]],
        features: Optional[List[str]] = None,
        norm_feat_idx: Optional[List[int]] = None,
        align_feat_idx: Optional[List[int]] = None,
    ) -> Tuple[Optional[pd.DataFrame], float]:
        """
        Generates a counterexample trace using the given traces.

        Args:
            scenario: Ordered list of scenario names
            features: Optional list of features to include in KDE
            norm_feat_idx: Optional indices of features to normalize
            align_feat_idx: Optional indices of features to align

        Returns:
            Trace
        """
        if len(scenario) == 0:
            raise ValueError("Scenario list must contain at least one scenario.")

        cex = None
        n = len(scenario)

        if n == 1:
            t_name = scenario[0]
            df_t = self.scenario_base.data[t_name]

            t_traces = df_t.sort_values("step").groupby("trace_id")
            t_first = t_traces.head(1).sort_values("trace_id")
            t_last = t_traces.tail(1).sort_values("trace_id")

            fail_idx = (t_last["label"] == False).to_numpy()
            t_first = t_first[fail_idx].sort_values("trace_id")
            t_last = t_last[fail_idx].sort_values("trace_id")

            if t_first.empty or t_last.empty:
                return None

            t_last_features = t_last[features].to_numpy()
            if t_last_features.shape[0] < 1:
                return None
            elif t_last_features.shape[0] == 2:
                t_trace_id = t_last_features[0]["trace_id"]
                t_trace = t_traces.get_group(t_trace_id)
                return t_trace

            if norm_feat_idx:
                for j in norm_feat_idx:
                    t_last_features[:, j] = self._normalize_features(t_last_features[:, j].reshape(-1, 1)).flatten()

            kde_t_last = gaussian_kde(t_last_features.T)
            t_last_prob = kde_t_last(t_last_features.T)
            t_idx = np.argmax(t_last_prob)
            t_trace_id = t_first.iloc[t_idx]["trace_id"]
            t_trace = t_traces.get_group(t_trace_id)
            return t_trace

        for i in reversed(range(n - 1)):
            s_name, t_name = scenario[i], scenario[i+1]
            df_s, df_t = self.scenario_base.data[s_name], self.scenario_base.data[t_name]

            s_traces = df_s.sort_values("step").groupby("trace_id")
            s_last = s_traces.tail(1).sort_values("trace_id")
            s_last = s_last[s_last["label"] == True].sort_values("trace_id")

            if cex is None:
                t_traces = df_t.sort_values("step").groupby("trace_id")
                t_first = t_traces.head(1).sort_values("trace_id")
                t_last = t_traces.tail(1).sort_values("trace_id")

                fail_idx = (t_last["label"] == False).to_numpy()
                t_first = t_first[fail_idx].sort_values("trace_id")
                t_last = t_last[fail_idx].sort_values("trace_id")

                if t_first.empty or t_last.empty:
                    continue

            # KDE features
            if features:
                s_last_features = s_last[features].to_numpy()
                if s_last_features.shape[0] < 2:
                    continue
                if cex is None:
                    t_first_features = t_first[features].to_numpy()
                    t_last_features = t_last[features].to_numpy()
                    if t_first_features.shape[0] < 2 or t_last_features.shape[0] < 2:
                        continue
                if norm_feat_idx:
                    for j in norm_feat_idx:
                        s_last_features[:, j] = self._normalize_features(s_last_features[:, j].reshape(-1, 1)).flatten()
                        if cex is None:
                            t_first_features[:, j] = self._normalize_features(t_first_features[:, j].reshape(-1, 1)).flatten()
                            t_last_features[:, j] = self._normalize_features(t_last_features[:, j].reshape(-1, 1)).flatten()
            else:
                raise ValueError("Feature list must be provided for KDE.")

            if cex is None:
                kde_s_last = gaussian_kde(s_last_features.T)
                kde_t_first = gaussian_kde(t_first_features.T)

                s_last_prob = kde_t_first(s_last_features.T)
                t_first_prob = kde_s_last(t_first_features.T)

                s_idx = np.argmax(s_last_prob)
                t_idx = np.argmax(t_first_prob)

                s_trace_id = s_last.iloc[s_idx]["trace_id"]
                t_trace_id = t_first.iloc[t_idx]["trace_id"]

                s_trace = s_traces.get_group(s_trace_id)
                t_trace = t_traces.get_group(t_trace_id)

                if align_feat_idx:
                    for idx in align_feat_idx:
                        s_feat = s_trace[features[idx]]
                        t_feat = t_trace[features[idx]]
                        offset = s_feat.iloc[-1] - t_feat.iloc[0]
                        t_trace.loc[:, features[idx]] = t_feat + offset

                cex = t_trace

            else:
                if align_feat_idx:
                    compare_idx = align_feat_idx
                else:
                    compare_idx = list(range(len(features)))

                # build arrays
                # s_last_features rows correspond to s_last (they were computed above)
                s_feat_mat = s_last_features[:, compare_idx]  # shape (num_s_last, k)
                cex_first = cex[features].iloc[0].to_numpy()[compare_idx]  # shape (k,)

                # compute Euclidean distances
                diffs = s_feat_mat - cex_first.reshape(1, -1)
                dists = np.linalg.norm(diffs, axis=1)

                # choose the s trace with minimum distance
                s_idx = int(np.argmin(dists))
                s_trace_id = s_last.iloc[s_idx]["trace_id"]
                s_trace = s_traces.get_group(s_trace_id)

                # Align cex to s_trace if align_feat_idx provided
                if align_feat_idx:
                    for idx in align_feat_idx:
                        s_feat = s_trace[features[idx]]
                        cex_feat = cex[features[idx]]
                        offset = s_feat.iloc[-1] - cex_feat.iloc[0]
                        cex.loc[:, features[idx]] = cex_feat + offset

            cex = pd.concat([s_trace, cex])

        if cex is None:
            return None

        final_features = [feat for feat in features] + ["label"]
        return cex[final_features].reset_index(drop=True)

