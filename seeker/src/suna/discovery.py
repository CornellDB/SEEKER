from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

from .config import BootstrapConfig, SunaConfig
from .results import BootstrapSummary, ConfounderFinding, SunaDiscoveryResult
from .scoring import BCDScore, score_bcd
from .sketches import SketchArtifacts


def _linear_regression_score(df: pd.DataFrame, features: Sequence[str], target: str) -> LinearRegression:
    model = LinearRegression()
    model.fit(df[list(features)], df[target])
    return model


@dataclass
class IterativeConfounderDiscovery:
    config: SunaConfig
    bootstrap: BootstrapConfig = field(default_factory=BootstrapConfig)

    def run(self, artifacts: SketchArtifacts) -> SunaDiscoveryResult:
        df = artifacts.dataframe.copy()
        findings: List[ConfounderFinding] = []
        selected: List[str] = []
        remaining = [c for c in artifacts.candidate_columns if c not in (artifacts.treatment_column, artifacts.outcome_column)]

        metadata: Dict[str, object] = {
            "initial_candidate_count": len(remaining),
            "bootstrap_n": self.bootstrap.n_samples,
            "bootstrap_tau": self.bootstrap.tau,
        }

        base_features = [artifacts.treatment_column]
        ate = None
        ate_std_err = None

        while remaining:
            candidate_scores: List[BCDScore] = []
            for candidate in remaining:
                score = score_bcd(
                    df,
                    artifacts.treatment_column,
                    artifacts.outcome_column,
                    candidate,
                    self.bootstrap,
                )
                candidate_scores.append(score)

            admissible = [
                s
                for s in candidate_scores
                if s.quantile_value > self.config.mi_drop_threshold
            ]
            if not admissible:
                break

            base_model = _linear_regression_score(
                df, base_features + selected, artifacts.outcome_column
            )
            base_r2 = base_model.score(
                df[base_features + selected], df[artifacts.outcome_column]
            )

            def mi_drop_for(score: BCDScore) -> float:
                augmented_features = base_features + selected + [score.candidate]
                augmented_model = _linear_regression_score(
                    df, augmented_features, artifacts.outcome_column
                )
                return augmented_model.score(df[augmented_features], df[artifacts.outcome_column]) - base_r2

            candidate_drops = [(score, mi_drop_for(score)) for score in admissible]
            candidate_drops.sort(key=lambda item: item[1], reverse=True)

            best_score, mi_drop = candidate_drops[0]
            if mi_drop <= self.config.mi_drop_threshold:
                break

            selected.append(best_score.candidate)
            remaining = [c for c in remaining if c != best_score.candidate]

            findings.append(
                ConfounderFinding(
                    name=best_score.candidate,
                    mi_drop=mi_drop,
                    bootstrap=BootstrapSummary(
                        quantile_value=best_score.quantile_value,
                        mean_delta=best_score.mean_delta,
                        samples=best_score.delta_samples.tolist(),
                    ),
                    r2_treat_on_candidate=best_score.r2_treat_on_candidate,
                    r2_candidate_on_treat=best_score.r2_candidate_on_treat,
                )
            )

        final_features = base_features + selected
        if final_features:
            final_model = _linear_regression_score(
                df, final_features, artifacts.outcome_column
            )
            ate = float(final_model.coef_[final_features.index(artifacts.treatment_column)])
            # Standard error estimate via residual variance
            design = df[final_features].to_numpy()
            if len(df) > len(final_features):
                preds = final_model.predict(df[final_features])
                residuals = df[artifacts.outcome_column] - preds
                residual_var = np.var(residuals, ddof=len(final_features))
                XtX_inv = np.linalg.pinv(design.T @ design)
                treat_index = final_features.index(artifacts.treatment_column)
                ate_std_err = float(
                    np.sqrt(max(residual_var, 0) * XtX_inv[treat_index, treat_index])
                )

        return SunaDiscoveryResult(
            dataset_name=self.config.dataset_name,
            treatment=artifacts.treatment_column,
            outcome=artifacts.outcome_column,
            method=self.config.method,
            findings=findings,
            ate=ate,
            ate_std_err=ate_std_err,
            metadata=metadata,
        )
