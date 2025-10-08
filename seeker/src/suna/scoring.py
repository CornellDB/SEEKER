from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import LinearRegression

from .config import BootstrapConfig


@dataclass
class BCDScore:
    candidate: str
    delta_samples: np.ndarray
    quantile_value: float
    mean_delta: float
    r2_treat_on_candidate: float
    r2_candidate_on_treat: float


def _compute_residual(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    model = LinearRegression()
    model.fit(X, y)
    return y - model.predict(X), model


def _safe_mutual_info(X: np.ndarray, y: np.ndarray, random_state: Optional[int]) -> float:
    try:
        return float(mutual_info_regression(X, y, random_state=random_state)[0])
    except ValueError:
        return 0.0


def _bootstrap_indices(n_samples: int, n_bootstrap: int, rng: np.random.Generator):
    for _ in range(n_bootstrap):
        yield rng.integers(0, n_samples, size=n_samples)


def score_bcd(
    df: pd.DataFrame,
    treatment: str,
    outcome: str,
    candidate: str,
    bootstrap: BootstrapConfig,
) -> BCDScore:
    """
    Compute bootstrap BCD scores using the simplified single-table statistics.
    """
    series_candidate = df[candidate].to_numpy()
    series_treatment = df[treatment].to_numpy()

    if np.var(series_candidate) < 1e-10 or np.var(series_treatment) < 1e-10:
        zero_array = np.zeros(bootstrap.n_samples, dtype=float)
        return BCDScore(
            candidate=candidate,
            delta_samples=zero_array,
            quantile_value=0.0,
            mean_delta=0.0,
            r2_treat_on_candidate=0.0,
            r2_candidate_on_treat=0.0,
        )

    X_candidate = series_candidate.reshape(-1, 1)
    X_treatment = series_treatment.reshape(-1, 1)

    res_treat, model_z_on_t = _compute_residual(series_candidate, X_treatment)
    res_candidate, model_t_on_z = _compute_residual(series_treatment, X_candidate)

    r2_treat_on_candidate = model_t_on_z.score(X_candidate, series_treatment)
    r2_candidate_on_treat = model_z_on_t.score(X_treatment, series_candidate)

    rng = np.random.default_rng(bootstrap.random_state)
    delta_samples = np.zeros(bootstrap.n_samples, dtype=float)

    for idx, sample_idx in enumerate(
        _bootstrap_indices(len(df), bootstrap.n_samples, rng)
    ):
        res_t_sample = res_treat[sample_idx]
        res_c_sample = res_candidate[sample_idx]
        X_c_sample = X_candidate[sample_idx]
        X_t_sample = X_treatment[sample_idx]

        p_plus = _safe_mutual_info(X_c_sample, res_c_sample, bootstrap.random_state)
        p_minus = _safe_mutual_info(X_t_sample, res_t_sample, bootstrap.random_state)
        delta_samples[idx] = p_minus - p_plus

    quantile_value = float(np.quantile(delta_samples, 1 - bootstrap.tau))
    mean_delta = float(np.mean(delta_samples))

    return BCDScore(
        candidate=candidate,
        delta_samples=delta_samples,
        quantile_value=quantile_value,
        mean_delta=mean_delta,
        r2_treat_on_candidate=r2_treat_on_candidate,
        r2_candidate_on_treat=r2_candidate_on_treat,
    )


def unavailable_feature(*_args, **_kwargs):
    raise ImportError(
        "Optional dependency not installed. Install seeker[suna_subspace] to enable."
    )


score_subgroup = unavailable_feature
score_cmi = unavailable_feature
score_mprp = unavailable_feature
score_shap = unavailable_feature
forest_clusters = unavailable_feature
