from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Sequence

import pandas as pd

from seeker.src.index_creation.dataset_model import DatasetModel

from .config import SunaConfig
from .discovery import IterativeConfounderDiscovery
from .results import SunaDiscoveryResult
from .sketches import SketchPreprocessor


def _dataset_identifier(dataset_model: DatasetModel) -> str:
    dataset_id = getattr(dataset_model, "id", None)
    if dataset_id is None:
        dataset_id = getattr(dataset_model, "dataset_id", None)
    if dataset_id is None:
        dataset_id = getattr(dataset_model, "dataset_name", None)
    if dataset_id is None:
        dataset_id = getattr(dataset_model, "name", None)
    return str(dataset_id)


@dataclass
class SunaDiscoveryPipeline:
    config: SunaConfig
    preprocessor: SketchPreprocessor = field(init=False)

    def __post_init__(self) -> None:
        self.preprocessor = SketchPreprocessor(self.config.sketch)

    def execute(self, dataset_model: DatasetModel) -> SunaDiscoveryResult:
        dataset: pd.DataFrame = dataset_model.dataset
        dataset_id = _dataset_identifier(dataset_model)

        artifacts = self.preprocessor.prepare(
            dataset,
            dataset_id=dataset_id,
            treatment=self.config.treatment,
            outcome=self.config.outcome,
            candidate_covariates=self.config.candidate_covariates,
            join_keys=self.config.join_keys,
        )

        discovery = IterativeConfounderDiscovery(
            config=self.config, bootstrap=self.config.bootstrap
        )
        result = discovery.run(artifacts)
        return result
