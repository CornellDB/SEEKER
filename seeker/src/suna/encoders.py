from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

import pandas as pd
from sklearn.preprocessing import OneHotEncoder


def infer_categorical_columns(
    df: pd.DataFrame,
    *,
    excludes: Optional[Sequence[str]] = None,
    max_unique: int = 30,
) -> List[str]:
    """Heuristic selection of categorical columns."""
    excludes = set(excludes or [])
    categorical_cols = []
    for col in df.columns:
        if col in excludes:
            continue
        series = df[col]
        if pd.api.types.is_bool_dtype(series):
            categorical_cols.append(col)
        elif pd.api.types.is_categorical_dtype(series):
            categorical_cols.append(col)
        elif pd.api.types.is_object_dtype(series):
            categorical_cols.append(col)
        elif series.nunique(dropna=True) <= max_unique:
            categorical_cols.append(col)
    return categorical_cols


def select_numeric_candidates(
    df: pd.DataFrame, excludes: Iterable[str]
) -> List[str]:
    """Return numeric columns that are not part of the excluded set."""
    excludes = set(excludes)
    candidates = []
    for col in df.columns:
        if col in excludes:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            candidates.append(col)
    return candidates


@dataclass
class EncodingArtifacts:
    encoded_frame: pd.DataFrame
    numeric_columns: List[str]
    categorical_columns: List[str]
    feature_names: List[str]


class CategoricalEncoder:
    """
    Thin wrapper around scikit-learn encoders to keep preprocessing local.
    """

    def __init__(self, handle_unknown: str = "ignore"):
        self.handle_unknown = handle_unknown
        self.encoder: Optional[OneHotEncoder] = None
        self._categorical_columns: List[str] = []

    def fit(
        self,
        df: pd.DataFrame,
        *,
        categorical_columns: Optional[Sequence[str]] = None,
    ) -> None:
        if categorical_columns is None:
            categorical_columns = infer_categorical_columns(df)

        self._categorical_columns = list(categorical_columns)
        if not self._categorical_columns:
            self.encoder = None
            return

        self.encoder = OneHotEncoder(
            handle_unknown=self.handle_unknown,
            sparse_output=False,
            dtype=float,
        )
        self.encoder.fit(df[self._categorical_columns])

    def transform(self, df: pd.DataFrame) -> EncodingArtifacts:
        if self.encoder is None or not self._categorical_columns:
            numeric_cols = [col for col in df.columns if pd.api.types.is_numeric_dtype(df[col])]
            return EncodingArtifacts(
                encoded_frame=df.copy(),
                numeric_columns=numeric_cols,
                categorical_columns=[],
                feature_names=list(df.columns),
            )

        encoded = self.encoder.transform(df[self._categorical_columns])
        encoded_df = pd.DataFrame(
            encoded,
            columns=self.encoder.get_feature_names_out(self._categorical_columns),
            index=df.index,
        )
        numeric_columns = [
            col
            for col in df.columns
            if col not in self._categorical_columns
            and pd.api.types.is_numeric_dtype(df[col])
        ]
        result = pd.concat([df[numeric_columns], encoded_df], axis=1)
        return EncodingArtifacts(
            encoded_frame=result,
            numeric_columns=numeric_columns,
            categorical_columns=self._categorical_columns,
            feature_names=list(result.columns),
        )

    def fit_transform(
        self,
        df: pd.DataFrame,
        *,
        categorical_columns: Optional[Sequence[str]] = None,
    ) -> EncodingArtifacts:
        self.fit(df, categorical_columns=categorical_columns)
        return self.transform(df)
