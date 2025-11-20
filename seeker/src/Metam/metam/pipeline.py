"""
Core METAM execution pipeline.

This module exposes reusable helpers that can be invoked from either the Flask
backend (GUI flow) or standalone CLI tooling.  The logic is adapted from the
original ``examples/example.py`` implementation with structural improvements
but identical behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass
import copy
import os
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

from src.backend.core.join_column import JoinColumn
from src.backend.core import join_path
from src.backend.clustering import kcenter
from src.backend.qualityscore import profile_weights
import src.backend.querying as querying
from src.backend.others.logger import get_logger, setup_logging

from .config import Config


@dataclass
class MetamResult:
    """Container describing the outcome of a METAM execution."""

    dataframe: pd.DataFrame
    initial_metric: float
    final_metric: float
    candidate_indices: Sequence[int]
    total_queries: int
    iterations: int


class MetamPipeline:
    """
    One-shot METAM execution helper.

    The pipeline mirrors the original flow: load metadata, expand join
    candidates, cluster them, and finally run the sequential/grouping
    exploration via ``MetamRunner``.
    """

    def __init__(self, config: Config, event_queue=None) -> None:
        self.config = config
        self.event_queue = event_queue
        self.logger = get_logger(__name__)
        self._data_cache: Dict[str, pd.DataFrame] = {}

    def run(self) -> MetamResult:
        """Execute METAM end-to-end and return the resulting artefacts."""
        setup_logging(level="INFO")
        if self.config.MODEL is None:
            raise ValueError("Config.MODEL must be assigned before running METAM.")
        if not self.config.PRED_COL:
            raise ValueError("Config.PRED_COL must be specified.")

        base_df = self._load_base_dataframe()
        join_paths = self._load_join_paths()

        new_columns = self._build_join_columns(join_paths, base_df)
        if not new_columns:
            self.logger.warning("No join columns produced; returning base dataframe unchanged.")
            metric = self.config.MODEL.train_pred_eval(base_df, self.config.PRED_COL)
            return MetamResult(
                dataframe=base_df,
                initial_metric=metric,
                final_metric=metric,
                candidate_indices=[],
                total_queries=0,
                iterations=0,
            )

        centers, assignment, clusters = self._cluster_candidates(new_columns)
        candidates = self._select_candidates(centers, len(new_columns))
        weights = self._initialize_weights(new_columns)

        initial_metric = self._evaluate_metric(base_df)
        self.logger.info("Original metric: %.4f", initial_metric)

        metam_runner = querying.MetamRunner(
            tau=len(centers),
            model=self.config.MODEL,
            candidates=candidates,
            local_config=self.config,
            metric=initial_metric,
            initial_df=copy.deepcopy(base_df),
            new_col_lst=new_columns,
            weights=weights,
            clusters=clusters,
            assignment=assignment,
            event_queue=self.event_queue,
        )

        augmented_df = metam_runner.run()
        final_metric = metam_runner.metric
        self.logger.info(
            "Final metric: %.4f (queries=%d, iterations=%d)",
            final_metric,
            metam_runner.total_queries,
            metam_runner.iteration,
        )

        return MetamResult(
            dataframe=augmented_df,
            initial_metric=initial_metric,
            final_metric=final_metric,
            candidate_indices=candidates,
            total_queries=metam_runner.total_queries,
            iterations=metam_runner.iteration,
        )

    def _load_base_dataframe(self) -> pd.DataFrame:
        if not self.config.QUERY_PATH:
            raise ValueError("Config.QUERY_PATH must be set before executing METAM.")
        df = pd.read_csv(self.config.QUERY_PATH, low_memory=False)
        self._data_cache[self.config.QUERY_DATA] = df
        return df

    def _load_join_paths(self) -> List[join_path.JoinPath]:
        if not self.config.JOIN_PATH_FILE:
            raise ValueError("Config.JOIN_PATH_FILE must be configured.")
        paths = join_path.get_join_paths_from_file(
            self.config.QUERY_DATA,
            self.config.JOIN_PATH_FILE,
        )
        self.logger.info("Discovered %d join paths", len(paths))
        return paths

    def _build_join_columns(
        self,
        join_paths: Iterable[join_path.JoinPath],
        base_df: pd.DataFrame,
    ) -> List[JoinColumn]:
        columns: List[JoinColumn] = []

        for jp in join_paths:
            left_tbl = jp.join_path[0].tbl
            right_tbl = jp.join_path[1].tbl
            left_df = self._load_table(left_tbl)
            right_df = self._load_table(right_tbl)

            left_key = jp.join_path[0].col
            right_key = jp.join_path[1].col

            if left_key not in left_df.columns or right_key not in right_df.columns:
                self.logger.debug("Skipping join path %s: key missing.", jp.to_str())
                continue

            for column in right_df.columns:
                self.logger.debug(
                    "Evaluating join candidate %s.%s via %s.%s",
                    right_tbl,
                    column,
                    left_tbl,
                    left_key,
                )
                jc = JoinColumn(
                    jp,
                    right_df,
                    column,
                    base_df,
                    self.config.PRED_COL,
                    len(columns),
                    self.config.UNINFO,
                    local_config=self.config,
                )
                columns.append(jc)
        self.logger.info("Constructed %d candidate columns", len(columns))
        return columns

    def _load_table(self, table_name: str) -> pd.DataFrame:
        if table_name in self._data_cache:
            return self._data_cache[table_name]

        if table_name == self.config.QUERY_DATA:
            df = self._data_cache.get(table_name)
            if df is None:
                raise FileNotFoundError(f"Base table {table_name} not cached.")
        else:
            data_path = self.config.DATA_PATH
            if not data_path:
                raise ValueError("Config.DATA_PATH must be set to load auxiliary tables.")
            csv_path = os.path.join(data_path, table_name)
            df = pd.read_csv(csv_path, low_memory=False)

        self._data_cache[table_name] = df
        return df

    def _cluster_candidates(
        self,
        join_columns: Sequence[JoinColumn],
    ) -> Tuple[Sequence[int], Dict[JoinColumn, int], Sequence[Sequence[JoinColumn]]]:
        centers, assignment, clusters = kcenter.cluster_join_paths(
            join_columns,
            k=self.config.K,
            epsilon=self.config.EPSILON,
        )
        return centers, assignment, clusters

    @staticmethod
    def _select_candidates(centers: Sequence[int], total_columns: int) -> Sequence[int]:
        tau = len(centers)
        if tau == 1:
            return list(range(total_columns))
        return list(centers)

    @staticmethod
    def _initialize_weights(columns: Sequence[JoinColumn]) -> Dict[Tuple[str, str], float]:
        weights: Dict[Tuple[str, str], float] = {}
        return profile_weights.initialize_weights(columns[0], weights)

    def _evaluate_metric(self, dataframe: pd.DataFrame) -> float:
        return self.config.MODEL.train_pred_eval(dataframe, self.config.PRED_COL)


def run_metam(config: Config, event_queue=None) -> MetamResult:
    """
    Convenience wrapper that executes METAM with the provided configuration.
    """
    pipeline = MetamPipeline(config, event_queue=event_queue)
    return pipeline.run()


def main(event_queue=None, local_config: Optional[Config] = None):
    """
    Backward-compatible entry point retained for Flask integration.

    The backend instantiates ``Config`` externally and passes it in so we only
    need to drive the pipeline and write the output file here.
    """
    config = local_config or Config()
    result = run_metam(config, event_queue=event_queue)
    result.dataframe.to_csv(config.OUTPUT_FILE, index=False)
