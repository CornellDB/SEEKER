from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

import pandas as pd


@dataclass
class BootstrapSummary:
    quantile_value: float
    mean_delta: float
    samples: List[float]

    def to_dict(self) -> Dict[str, object]:
        return {
            "quantile": self.quantile_value,
            "mean": self.mean_delta,
            "samples": self.samples,
        }


@dataclass
class ConfounderFinding:
    name: str
    mi_drop: float
    bootstrap: BootstrapSummary
    r2_treat_on_candidate: float
    r2_candidate_on_treat: float

    def to_row(self, dataset_name: str) -> Dict[str, object]:
        return {
            "dataset_name": dataset_name,
            "confounder": self.name,
            "mi_drop": self.mi_drop,
            "bootstrap_quantile": self.bootstrap.quantile_value,
            "bootstrap_mean": self.bootstrap.mean_delta,
            "r2_treat_on_candidate": self.r2_treat_on_candidate,
            "r2_candidate_on_treat": self.r2_candidate_on_treat,
        }


@dataclass
class SunaDiscoveryResult:
    dataset_name: str
    treatment: str
    outcome: str
    method: str
    findings: List[ConfounderFinding] = field(default_factory=list)
    ate: Optional[float] = None
    ate_std_err: Optional[float] = None
    metadata: Dict[str, object] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dataframe(self) -> pd.DataFrame:
        rows = [finding.to_row(self.dataset_name) for finding in self.findings]
        return pd.DataFrame(rows)
