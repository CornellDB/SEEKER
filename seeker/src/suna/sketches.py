from __future__ import annotations

import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from .encoders import CategoricalEncoder, EncodingArtifacts, select_numeric_candidates
from .config import SketchConfig


@dataclass
class SketchArtifacts:
    """Materialized artifacts produced by the sketch preprocessor."""

    dataframe: pd.DataFrame
    treatment_column: str
    outcome_column: str
    candidate_columns: List[str]
    encoding: EncodingArtifacts

    def features_for(self, columns: Sequence[str]) -> pd.DataFrame:
        return self.dataframe[list(columns)]


class SketchCacheManager:
    """Utility to persist and restore sketch artifacts from disk."""

    def __init__(self, sketch_config: SketchConfig, dataset_id: str):
        self.sketch_config = sketch_config
        self.dataset_id = dataset_id
        self.cache_dir = self.sketch_config.resolve(dataset_id)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _artifact_path(self) -> Path:
        return self.cache_dir / "sketch.pkl"

    def load(self) -> Optional[SketchArtifacts]:
        if not self.sketch_config.enable_cache:
            return None
        artifact_path = self._artifact_path()
        if artifact_path.exists():
            with artifact_path.open("rb") as infile:
                return pickle.load(infile)
        return None

    def save(self, artifacts: SketchArtifacts) -> None:
        if not self.sketch_config.enable_cache:
            return
        artifact_path = self._artifact_path()
        if artifact_path.exists() and not self.sketch_config.overwrite:
            return
        with artifact_path.open("wb") as outfile:
            pickle.dump(artifacts, outfile)


class SketchPreprocessor:
    """
    Prepare dataset sketches. For the first SEEKER integration we keep an
    in-memory representation but expose caching hooks for future expansion.
    """

    def __init__(self, sketch_config: SketchConfig):
        self.sketch_config = sketch_config
        self.encoder = CategoricalEncoder()

    def prepare(
        self,
        df: pd.DataFrame,
        *,
        dataset_id: str,
        treatment: str,
        outcome: str,
        candidate_covariates: Optional[Sequence[str]] = None,
        join_keys: Optional[Sequence[Sequence[str]]] = None,  # placeholder for future
    ) -> SketchArtifacts:
        cache_manager = SketchCacheManager(self.sketch_config, dataset_id)
        cached = cache_manager.load()
        if cached and not self.sketch_config.overwrite:
            return cached

        if candidate_covariates is None:
            excludes = {treatment, outcome}
            if join_keys:
                excludes.update({jk for key in join_keys for jk in key})
            candidate_covariates = select_numeric_candidates(df, excludes)

        encoding = self.encoder.fit_transform(df)
        encoded_df = encoding.encoded_frame
        # Ensure treatment and outcome remain available (after encoding)
        if treatment not in encoded_df.columns or outcome not in encoded_df.columns:
            encoded_df = encoded_df.assign(
                **{treatment: df[treatment], outcome: df[outcome]}
            )

        artifacts = SketchArtifacts(
            dataframe=encoded_df,
            treatment_column=treatment,
            outcome_column=outcome,
            candidate_columns=list(candidate_covariates),
            encoding=encoding,
        )

        cache_manager.save(artifacts)
        return artifacts
