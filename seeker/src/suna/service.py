from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from seeker.src.seeker_service_modules.search_module import DataSeeker
from seeker.src.data_visualization.search_visualizer import SearchResultsVisualizer
from seeker.src.index_creation.dataset_model import DatasetModel

from .config import SunaConfig, parse_cli_overrides
from .pipelines import SunaDiscoveryPipeline
from .results import ConfounderFinding, SunaDiscoveryResult


class OptionalDependencyUnavailable(RuntimeError):
    """Raised when a requested scoring routine requires missing extras."""


@dataclass
class SunaConfounderDiscoveryService:
    dataset_model: DatasetModel
    base_config: SunaConfig

    @classmethod
    def from_dataset(
        cls,
        dataset_model: DatasetModel,
        *,
        overrides: Optional[Dict[str, object]] = None,
    ) -> "SunaConfounderDiscoveryService":
        config = SunaConfig.from_metadata(dataset_model, overrides=overrides or {})
        return cls(dataset_model=dataset_model, base_config=config)

    def discover(self, *, config_overrides: Optional[Dict[str, object]] = None) -> SunaDiscoveryResult:
        config = self.base_config
        if config_overrides:
            config = config.with_overrides(config_overrides)
        pipeline = SunaDiscoveryPipeline(config)
        return pipeline.execute(self.dataset_model)


def _to_visualizer_rows(result: SunaDiscoveryResult) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []
    for finding in result.findings:
        rows.append(
            {
                "dataset_name": result.dataset_name,
                "score": finding.mi_drop,
                "metadata": {
                    "bootstrap_quantile": finding.bootstrap.quantile_value,
                    "bootstrap_mean": finding.bootstrap.mean_delta,
                    "r2_treat_on_candidate": finding.r2_treat_on_candidate,
                    "r2_candidate_on_treat": finding.r2_candidate_on_treat,
                    "treatment": result.treatment,
                    "outcome": result.outcome,
                    "ate": result.ate,
                    "ate_std_err": result.ate_std_err,
                },
                "top_words": None,
            }
        )
    return rows


class SunaDataSeeker(DataSeeker):
    """DataSeeker adaptor that surfaces Suna discovery results."""

    def __init__(self, search_query: str, dataset_models: Dict[str, DatasetModel]):
        super().__init__(search_query)
        self.dataset_models = dataset_models

    def discover(
        self,
        dataset_name: str,
        overrides: Optional[Dict[str, object]] = None,
    ) -> SunaDiscoveryResult:
        if dataset_name not in self.dataset_models:
            raise ValueError(f"Dataset '{dataset_name}' not found in loaded models.")
        dataset_model = self.dataset_models[dataset_name]
        service = SunaConfounderDiscoveryService.from_dataset(
            dataset_model, overrides=overrides
        )
        result = service.discover()
        rows = _to_visualizer_rows(result)
        if rows:
            visualizer = SearchResultsVisualizer(rows, self.search_query)
            visualizer.display()
        else:
            print(
                f"Suna discovery finished for dataset '{dataset_name}' but no confounders "
                "passed the selection thresholds."
            )
        return result


def execute_from_cli(
    dataset_models: Dict[str, DatasetModel],
    args: Iterable[str],
    *,
    search_query: str = "",
) -> SunaDiscoveryResult:
    params = parse_cli_overrides(args)
    dataset_name = params.pop("dataset", None)
    if not dataset_name:
        raise ValueError("Suna discovery requires specifying dataset=<name>.")

    overrides = params
    seeker = SunaDataSeeker(search_query, dataset_models)
    return seeker.discover(dataset_name, overrides=overrides)
