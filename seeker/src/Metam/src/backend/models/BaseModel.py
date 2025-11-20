from abc import ABC, abstractmethod
import pandas as pd

from sklearn.model_selection import train_test_split


class BaseModel(ABC):
    """
    Abstract base class:
      - drops rows with missing target
      - fills missing features
      - encodes categorical features
      - converts target to float (regression) or to integer labels (classification)
    """
    def __init__(self, name: str = "BaseModel", utility_metrics= None):
        self.name = name
        self.utility_metrics = utility_metrics

    def _preprocess(self,
                    df: pd.DataFrame,
                    target_col: str,
                    test_size: float,
                    random_state: int,
                    is_classifier: bool):
        # 1) Drop any rows where the target is missing
        df = df.dropna(subset=[target_col]).copy()

        # 2) Separate features / target
        features = [c for c in df.columns if c != target_col]
        X = df[features].copy()
        y = df[target_col].copy()

        # 3) Fill and encode features
        for col in X.columns:
            col_series = X[col].fillna(0)
            if col_series.dtype == "object" or pd.api.types.is_categorical_dtype(col_series):
                X.loc[:, col] = col_series.astype("category").cat.codes
            else:
                X.loc[:, col] = col_series

        # 4) Convert y
        if is_classifier:
            # if non‐numeric, label encode
            if y.dtype == "object" or pd.api.types.is_categorical_dtype(y):
                y = y.astype("category").cat.codes
            else:
                # convert floats→ints if already numeric
                y = y.astype(int)
        else:
            # regression: everything to float
            y = pd.to_numeric(y, errors="raise").astype(float)

        # 5) split
        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        return X_tr, X_te, y_tr, y_te
